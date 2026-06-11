#!/usr/bin/env python3
# scripts/release.py
# 密码管家一键打包并自动发布至 GitHub Releases 脚本

import os
import re
import sys
import subprocess
import shutil

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = os.path.join(PROJECT_DIR, "src", "password_manager", "config", "settings.py")
ZIP_PATH = os.path.join(PROJECT_DIR, "dist", "密码管家_mac_dist.zip")


def print_success(msg):
    print(f"\033[92m[✓] {msg}\033[0m")


def print_info(msg):
    print(f"\033[94m[*] {msg}\033[0m")


def print_warn(msg):
    print(f"\033[93m[!] {msg}\033[0m")


def print_error(msg):
    print(f"\033[91m[✗] {msg}\033[0m")


def validate_version(version_str):
    """验证版本号是否符合 X.Y.Z 规范"""
    pattern = r"^\d+\.\d+\.\d+$"
    return bool(re.match(pattern, version_str))


def get_github_username():
    """获取当前登录 GitHub CLI 的用户名"""
    try:
        ret, stdout, stderr = run_command("gh api user --jq .login", check=False)
        username = stdout.strip()
        if ret == 0 and username:
            return username
    except Exception:
        pass
    
    # 尝试解析 gh auth status 的输出作为降级
    try:
        ret, stdout, stderr = run_command("gh auth status", check=False)
        # 寻找 "Logged in to github.com as 用户名" 或 "Logged in as 用户名"
        match = re.search(r"Logged in as ([a-zA-Z0-9\-]+)", stdout + stderr)
        if match:
            return match.group(1)
        match_alt = re.search(r"Logged in to github.com as ([a-zA-Z0-9\-]+)", stdout + stderr)
        if match_alt:
            return match_alt.group(1)
    except Exception:
        pass
        
    return None


def update_settings_version(version):
    """自动更新 settings.py 中的 CURRENT_VERSION 默认值"""
    if not os.path.exists(SETTINGS_PATH):
        print_error(f"找不到配置文件: {SETTINGS_PATH}")
        sys.exit(1)

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 正则替换：匹配 CURRENT_VERSION: str = Field(default="xxx" 或 Field(default='xxx'
    pattern = r'(CURRENT_VERSION:\s*str\s*=\s*Field\(\s*default=)(["\'])(.*?)\2'
    if not re.search(pattern, content):
        print_error("无法在 settings.py 中定位 CURRENT_VERSION 常量字段，请检查配置文件结构！")
        sys.exit(1)

    new_content = re.sub(pattern, rf'\g<1>\g<2>{version}\g<2>', content)

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print_success(f"已将 {SETTINGS_PATH} 中的客户端版本更新为: {version}")


def update_settings_update_url(github_username):
    """自动更新 settings.py 中的 UPDATE_URL 为当前登录用户的更新源"""
    if not os.path.exists(SETTINGS_PATH):
        return

    with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 正则替换：匹配 UPDATE_URL: str = Field(default="xxx" 或 Field(default='xxx'
    pattern = r'(UPDATE_URL:\s*str\s*=\s*Field\(\s*default=)(["\'])(.*?)\2'
    if not re.search(pattern, content):
        return

    new_url = f"https://api.github.com/repos/{github_username}/PasswordProject/releases/latest"
    
    # 提取旧配置对比，避免重复写盘
    old_match = re.search(pattern, content)
    if old_match and old_match.group(3) == new_url:
        print_info(f"更新源 UPDATE_URL 已匹配: {new_url}")
        return

    new_content = re.sub(pattern, rf'\g<1>\g<2>{new_url}\g<2>', content)

    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print_success(f"已将 {SETTINGS_PATH} 中的更新源 UPDATE_URL 修正为: {new_url}")


def run_command(cmd, cwd=PROJECT_DIR, shell=True, check=True):
    """辅助运行 shell 命令"""
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=shell, check=check, text=True, capture_output=True)
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        if check:
            print_error(f"命令执行失败: {cmd}")
            print_error(f"错误码: {e.returncode}")
            print_error(f"错误输出: {e.stderr or e.output}")
            sys.exit(e.returncode)
        return e.returncode, e.stdout, e.stderr


def setup_git_repo(version, github_username):
    """初始化 git 并在本地打 tag"""
    repo_url = f"https://github.com/{github_username}/PasswordProject.git"
    print_info("检查本地 Git 仓库状态...")
    git_dir = os.path.join(PROJECT_DIR, ".git")
    
    if not os.path.exists(git_dir):
        print_warn("本地未检测到 Git 仓库，正在为您初始化...")
        run_command("git init")
        run_command(f"git remote add origin {repo_url}")
        print_success("Git 仓库初始化完毕并已关联远程 origin。")
    else:
        # 检查是否关联了 remote，若没有则添加，若地址不同则修正
        _, remotes, _ = run_command("git remote -v", check=False)
        if "origin" not in remotes:
            run_command(f"git remote add origin {repo_url}")
        elif repo_url not in remotes and f"github.com/{github_username}/PasswordProject" not in remotes:
            print_warn(f"当前 remote origin 地址可能不匹配，正在修正为: {repo_url}")
            run_command("git remote remove origin")
            run_command(f"git remote add origin {repo_url}")

    # 提交代码更新
    run_command("git add src/password_manager/config/settings.py")
    
    # 检查是否有需要 commit 的内容
    _, status_out, _ = run_command("git status --porcelain", check=False)
    if "src/password_manager/config/settings.py" in status_out:
        print_info("提交版本修改到本地 Git...")
        run_command(f'git commit -m "chore: bump version to v{version}"')
        print_success("本地提交成功！")
    else:
        print_info("settings.py 版本无变化或已提交。")

    # 打 Tag 标记
    tag_name = f"v{version}"
    # 检查本地是否已存在该 tag
    _, tags, _ = run_command("git tag", check=False)
    if tag_name in tags.split():
        print_warn(f"本地已存在标签 {tag_name}，正在删除并重新创建...")
        run_command(f"git tag -d {tag_name}")
        
    run_command(f'git tag -a {tag_name} -m "Release version {tag_name}"')
    print_success(f"已成功在本地打上版本标签: {tag_name}")

    # 引导推送标签到 GitHub
    print_info(f"即将推送标签 {tag_name} 至 GitHub 远程仓库...")
    ret, _, err = run_command(f"git push origin {tag_name}", check=False)
    if ret != 0:
        print_warn("无法直接通过 Git 推送标签至 GitHub 仓库。")
        print_warn("这通常是因为远程仓库在云端尚未创建，或没有 SSH 推送权限。")
        print_warn("不用担心！接下来脚本将尝试通过 GitHub CLI 建立云端仓库并推送 Release。")
    else:
        print_success(f"成功将标签 {tag_name} 推送至 GitHub 云端！")


def check_and_ensure_gh_logged_in():
    """确保 GitHub CLI 安装且已正常登录授权"""
    # 检查是否安装了 gh
    gh_path = shutil.which("gh")
    if not gh_path:
        print_error("未在系统路径中找到 GitHub CLI (gh) 命令行工具！")
        print_error("自动发布至 GitHub Releases 依赖于 gh 工具。")
        print_error("请运行 `brew install gh` 安装它，或者选择手动在浏览器中发布。")
        sys.exit(1)

    while True:
        ret, stdout, stderr = run_command("gh auth status", check=False)
        if ret == 0:
            print_success("GitHub CLI (gh) 已验证登录状态正常。")
            break
        else:
            print_error("检测到您的 GitHub CLI 未登录或 Token 已失效！")
            print_warn("请在您的【本地系统终端】中执行以下命令以完成 GitHub 登录授权：")
            print("\n    \033[96mgh auth login\033[0m\n")
            print_info("提示：登录时，请选择 'GitHub.com' -> 'HTTPS' -> 授权选择浏览器登录或粘贴 Token 方式。")
            
            user_input = input("当您在终端中登录成功后，请按 [Enter] 回车键重试检测，或输入 'q' 退出：").strip()
            if user_input.lower() == 'q':
                print_info("您已取消发布流程。生成的打包文件仍保存在 dist 目录中。")
                sys.exit(0)


def build_app():
    """执行 build_mac_app.sh 打包"""
    print_info("正在启动 macOS 应用程序打包编译流程 (build_mac_app.sh)...")
    build_script = os.path.join(PROJECT_DIR, "scripts", "build_mac_app.sh")
    
    if not os.path.exists(build_script):
        print_error(f"找不到打包脚本: {build_script}")
        sys.exit(1)

    # 赋予脚本执行权限以防万一
    os.chmod(build_script, 0o755)

    # 执行打包
    ret, stdout, stderr = run_command(f'"{build_script}"', check=False)
    if ret != 0:
        print_error("打包编译失败！请检查上述日志排查 PyInstaller 错误。")
        sys.exit(1)
        
    if not os.path.exists(ZIP_PATH):
        print_error(f"未能在预期位置找到打包生成的压缩包: {ZIP_PATH}")
        sys.exit(1)

    print_success("应用程序打包成功！zip 压缩包已准备就绪。")


def create_github_release(version, github_username):
    """创建 GitHub Release 并上传 zip 包"""
    tag_name = f"v{version}"
    print_info(f"正在向 GitHub 仓库提交并创建 Release {tag_name}...")
    
    # 构建 Release 创建命令
    release_cmd = (
        f'gh release create "{tag_name}" "{ZIP_PATH}" '
        f'--title "{tag_name}" '
        f'--notes "密码管家自动升级包 {tag_name}。下载并解压后，替换旧版即可。"'
    )
    
    ret, stdout, stderr = run_command(release_cmd, check=False)
    
    # 特判仓库不存在的情况并自动建仓
    if ret != 0 and ("Could not resolve to a Repository" in stderr or "not found" in stderr.lower()):
        print_warn(f"云端未检测到仓库 {github_username}/PasswordProject，正在为您自动创建云端仓库...")
        
        # 临时移除本地 origin，避免 gh repo create 建立本地关联时报 origin 已存在错误
        run_command("git remote remove origin", check=False)
        
        # 使用 gh repo create 在云端创建同名公开仓库，并将本地推送上去
        create_repo_cmd = f"gh repo create PasswordProject --public --source={PROJECT_DIR} --push --remote=origin"
        ret_create, stdout_create, stderr_create = run_command(create_repo_cmd, check=False)
        
        if ret_create == 0:
            print_success("GitHub 远程仓库创建成功并已推送本地 main/master 分支！")
            # 重新推送 Tag
            run_command(f"git push origin {tag_name}", check=False)
            # 再次尝试创建 Release
            print_info(f"正在重新尝试创建 Release {tag_name}...")
            ret, stdout, stderr = run_command(release_cmd, check=False)
        else:
            print_error(f"自动创建仓库失败: {stderr_create or stderr}")
            
    # 特判已存在相同 tag 的 release，提供覆盖发布功能
    if ret != 0 and "already exists" in stderr:
        print_warn(f"云端已存在相同版本的发布版 {tag_name}。")
        user_choice = input("是否要覆盖发布该版本？这将自动删除云端旧版本并重新上传最新包 (y/n): ").strip().lower()
        if user_choice == 'y':
            print_info(f"正在为您清理云端已存在的 Release {tag_name}...")
            run_command(f'gh release delete "{tag_name}" --yes', check=False)
            run_command(f'git push origin --delete "{tag_name}"', check=False)
            
            # 重新创建本地 tag 并推送到云端
            print_info("重新创建本地 tag 并推送到云端...")
            run_command(f'git tag -d "{tag_name}"', check=False)
            run_command(f'git tag -a "{tag_name}" -m "Release version {tag_name}"')
            run_command(f"git push origin {tag_name}", check=False)
            
            # 再次尝试创建 Release
            print_info(f"正在重新尝试创建 Release {tag_name}...")
            ret, stdout, stderr = run_command(release_cmd, check=False)
            
    if ret == 0:
        print_success(f"GitHub Release {tag_name} 发布成功！")
        print_info(f"Release 链接: {stdout.strip()}")
        print_success("更新链条已闭环！其他人安装的密码管家客户端在下一次启动时将自动收到新版本更新提示并可一键无感升级！")
    else:
        print_error(f"发布 Release 失败！错误信息:\n{stderr}")
        print_warn("若因为权限限制发布失败，您可以登录 GitHub 网页端手动发布：")
        print(f"1. 访问 https://github.com/chennanxing/PasswordProject/releases")
        print(f"2. 点击 'Draft a new release'，Tag 填写 v{version}，标题填写 v{version}")
        print(f"3. 将本地打包出的文件拖拽上传至附件：")
        print(f"   路径: {ZIP_PATH}")
        print(f"4. 点击 'Publish release' 即可。")


def main():
    print("=" * 60)
    print("  🌿 密码管家 macOS/Windows 一键打包与 GitHub Release 自动发布工具  ")
    print("=" * 60)

    # 1. 获取版本号
    version = ""
    if len(sys.argv) > 1:
        version = sys.argv[1].strip().lstrip("v")
    
    while not version or not validate_version(version):
        if version:
            print_error(f"版本号格式错误: '{version}'，必须为 X.Y.Z 格式（例如: 1.0.1）")
        version = input("请输入您要发布的版本号 (例如 1.0.1): ").strip().lstrip("v")

    print_info(f"即将发布的版本号: v{version}")

    # 2. 检查并确保 gh cli 登录就绪
    check_and_ensure_gh_logged_in()
    
    # 获取实际登录的 GitHub 用户名
    github_username = get_github_username()
    if not github_username:
        print_error("无法获取当前登录的 GitHub 用户名，请检查 gh 状态！")
        sys.exit(1)
        
    print_info(f"已获取当前登录 GitHub 账号: {github_username}")

    # 3. 动态将真实的 github_username 的更新源写入 settings.py 并修改版本号
    update_settings_update_url(github_username)
    update_settings_version(version)

    # 4. 执行 build_mac_app.sh 编译打包
    build_app()

    # 5. Git 暂存、提交、打标签并尝试推送（动态传入 github_username）
    setup_git_repo(version, github_username)

    # 6. 推送代码到远程（确保 GitHub Actions 能拉取到最新代码进行构建）
    print_info("正在推送最新代码至 GitHub 远程仓库...")
    ret, _, err = run_command("git push origin HEAD", check=False)
    if ret == 0:
        print_success("代码推送成功！")
    else:
        print_warn(f"代码推送未成功（可能需要手动推送）: {err.strip()}")

    # 7. 使用 gh cli 发布 macOS 版 Release 并上传附件
    create_github_release(version, github_username)

    # 8. 提示云端 Windows 构建信息
    print("")
    print_info("=" * 56)
    print_info("🪟 Windows 客户端云端自动构建")
    print_info("=" * 56)
    print_info(f"Tag v{version} 已推送至 GitHub，云端 GitHub Actions 正在")
    print_info("自动为您编译 Windows 版 密码管家.exe 安装包。")
    print_info(f"您可在此查看构建进度：")
    print(f"    \033[96mhttps://github.com/{github_username}/PasswordProject/actions\033[0m")
    print_info("构建完成后，Windows 安装包将自动追加挂载到 Release 页面中。")

    print("\n" + "=" * 60)
    print("🎉 发布流程全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

