# 密码管家 (PassKeeper) macOS 部署流程与注意细节手册

本手册详细介绍了如何将“密码管家”应用程序进行打包、网络分发以及在他人 Mac 电脑上部署运行的完整流程，并针对 macOS 系统级隐私安全门禁（Gatekeeper）等常见细节问题提供了直接的解决方案。

---

## 📌 一、 部署前环境要求
1. **远程数据库连通性**：本 App 目前后端使用 MySQL 作为数据存储。在部署 App 前，请确保 MySQL 容器/服务（如运行在 `10.151.174.39` 上的容器）已正常启动，且网络处于可联通状态。
2. **大模型 API 连通性**：如果需要使用 AI 智能提取与多模态导入功能，请确保本地能正常连接远程 SenseAuto 大模型服务，并保证 API Key 有效。

---

## 🛠️ 二、 发布者打包与自动发布流程（开发/发布人员）
在发布新版本应用时，您可以选择**本地打包**或**一键自动发布**：

### 方式 A：一键打包并自动发布至 GitHub Releases（推荐 🚀，可触发客户端自动更新）
若要升级软件版本并让其他人安装的客户端能够**自动在线检测并更新**，您可以使用专用的发布脚本：
1. **确保安装并登录了 GitHub CLI**：
   ```bash
   brew install gh
   gh auth login
   ```
2. **运行发布脚本**：在项目根目录下执行：
   ```bash
   python scripts/release.py
   ```
   *脚本会自动完成以下动作：*
   - 交互式提示您输入新版本号（如 `1.0.1`），并自动校验格式；
   - 自动将新版本号写入代码配置，免去手动改 `settings.py` 遗忘的烦恼；
   - 自动运行打包生成最新的 `dist/密码管家_mac_dist.zip`；
   - 自动初始化本地 Git 并为您提交代码、打上版本 Tag 标签；
   - 自动调用 `gh` CLI 将压缩包发布为 GitHub Release，挂载为最新更新源。

---

### 方式 B：仅本地打包（手动分发）
若您只想在本地生成一个 App 压缩包用于手动发送：
1. **修正最新配置**：在项目根目录的 `.env` 中填写正确的数据库连接地址与 AI 配置。
2. **运行打包脚本**：在项目根目录下，执行：
   ```bash
   ./scripts/build_mac_app.sh
   ```
   *脚本会自动编译生成 macOS 原生 `.app` 包，并自动在 `dist` 目录下将其打包压缩为 **`密码管家_mac_dist.zip`**。*

---

## 📬 三、 软件分发与部署流程（使用者）

### 1. 本地直接使用
如果您是在自己打包的这台 Mac 上使用：
* 直接进入 `dist` 目录，将 **`密码管家.app`** 拖拽到桌面、或者拖进 **“应用程序(Applications)”** 文件夹。
* 直接双击运行即可，它已内置了本地的 `.env` 数据库配置，无需任何额外配置！

### 2. 发送给别人使用（网络分发细节 ⚠️ 极为重要）
如果您需要通过微信、钉钉、QQ 或网盘等方式将软件发送给别人的 Mac：
* **禁止操作**：**绝对不要直接发送 `密码管家.app` 文件夹！** （macOS 上的 `.app` 表面是单个图标，本质是多层级文件夹。直接发送会导致微信等传输软件直接抹除内部运行二进制文件的 Unix 可执行权限，导致对方解压后无法识别为 App 并报错）。
* **正确操作**：**请务必只发送 `dist/密码管家_mac_dist.zip` 这个压缩包文件**。该压缩包内部通过特殊的打包参数锁定了 Unix 执行权限，能确保解压出来的 App 结构完好。

---

## ⚠️ 四、 对方接收运行时的关键注意细节与解限办法
当别人收到您的 `密码管家_mac_dist.zip` 并在他们自己的 Mac 电脑上解压运行时，可能会因为苹果系统的安全限制遇到以下三个经典报错，请按照对应的办法一秒排除：

### 细节 1：提示“密码管家已损坏，无法打开。你应该将它移到废纸篓”
* **原因**：这是 macOS 著名的 Gatekeeper 门禁防护弹窗。苹果系统一旦检测到这属于个人开发且从网络下载的未签名软件，就会在文件上强行附加一个“安全隔离标签（Quarantine 属性）”，故意弹出此“损坏”警告。
* **一键解限办法**：让对方打开 Mac 的 **终端 (Terminal.app)**，输入命令：
  ```bash
  xattr -cr /Path/To/密码管家.app
  ```
  *(💡 操作小窍门：让对方在终端中输入 `xattr -cr ` 后带一个空格，然后直接用鼠标把桌面上解压出来的 `密码管家.app` 往终端里一拖，路径便会自动填好，回车即可彻底解除此限制。)*

### 细节 2：双击打开应用时弹出“文本编辑”报错，提示“未能打开文稿，文本编码不适用”
* **原因**：对方可能没有使用 macOS 自带的归档实用工具进行解压，或者在多次拷贝中丢失了 Unix 可执行属性。这导致 macOS 不再将 `.app` 识别为软件，而是当作普通文本文档去用“文本编辑”翻译它的二进制文件，导致了报错。
* **一键解限办法**：让对方打开终端，输入命令，手动为包内的核心可执行文件补齐执行权限：
  ```bash
  chmod +x /Path/To/密码管家.app/Contents/MacOS/密码管家
  ```
  *(💡 操作小窍门：让对方在终端输入 `chmod +x ` 后带一个空格，然后右键点击 `.app` 选择“显示包内容”，依次点进 `Contents -> MacOS`，把里面的 `密码管家` 可执行文件直接用鼠标拖入终端窗口，回车即可。)*

### 细节 3：在 M 系列芯片（Apple Silicon）的新 Mac 上双击启动提示需要安装软件
* **原因**：由于我们当前的编译环境是 Intel 架构 (x86_64)，在较新的 M1/M2/M3 芯片的 Mac 上运行时，需要通过系统的 Rosetta 2 翻译器做指令集无感翻译。
* **解决办法**：在对方首次双击打开应用时，如果系统弹窗提示“需要安装 Rosetta 运行此软件”，**点击“安装”确认即可**。系统会自动安装并在以后透明运行，没有任何性能损失。

### 细节 4：使用自定义的数据库配置（高阶功能）
* **特点**：如果使用者需要将应用连接至他们自己的 MySQL，而不想用包内打包进去的默认数据库：
* **配置方式**：应用支持多态配置自适应。使用者只需在解压出的 `密码管家.app` 文件的 **同级目录下** 放置一个他们自己的 `.env` 配置文件（或者在其个人家目录下创建 `~/.password_manager/.env`），App 就会自动优先读取他们自己的外部配置。

---

## 🪟 五、 跨平台编译 Windows 客户端（.exe）与部署指南

### 1. 为什么在 macOS 上无法直接打包生成 `.exe` 文件？
PyInstaller 并不是一个交叉编译器，它是通过将当前操作系统中的 Python 解释器、系统动态链接库（macOS 为 `.dylib`，Windows 为 `.dll`）以及项目源码打包在一起。由于 macOS 系统中不包含 Windows 系统的运行环境与 API 库，因此**无法在 macOS 环境下直接输出运行在 Windows 上的 `.exe` 文件**。

### 2. 方案 A：在本地 Windows 环境打包
要在 Windows 系统下生成 `密码管家.exe`，请在 Windows 电脑（或虚拟机）中执行以下步骤：
1. **安装环境与依赖**：
   确保安装了 Python 3.10+ 并拉取代码，在项目根目录下安装依赖：
   ```cmd
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. **执行打包**：
   在 Windows 的 PowerShell 或 CMD 终端中运行：
   ```cmd
   pyinstaller -F run_gui.py --name="密码管家" --noconsole --clean
   ```
   * 参数说明：
     - `-F`：打包为单个独立的可执行文件；
     - `--noconsole`：运行时不弹出黑色的 CMD 命令行窗口；
     - `--name`：指定生成的可执行文件名称；
     - `--clean`：打包前清理临时缓存。
3. **打包结果**：
   打包完成后，在根目录下的 `dist/` 文件夹内可以找到 `密码管家.exe`。

### 3. 方案 B：利用 GitHub Actions 云端矩阵打包发布（推荐）
为了彻底解放本地环境限制，可以通过配置 GitHub Actions 流水线，在云端自动完成 macOS（`.app`）和 Windows（`.exe`）的双端打包，并一键发布至 GitHub Releases。
在项目 `.github/workflows/release.yml` 中配置矩阵：
```yaml
jobs:
  build:
    name: Build and Release
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [macos-latest, windows-latest]
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Run Build
        run: |
          pyinstaller -F run_gui.py --noconsole --name="密码管家"

      - name: Upload Release Asset
        # 使用相关 Action 将 dist/ 中的打包结果挂载到 GitHub Release
        ...
```

### 4. Windows 客户端热更新与安全替换机制
* **独占锁规避**：Windows 下运行中的进程文件不能直接覆盖。当客户端检测到并下载了新版本 zip 包后，会自动生成临时的 `pwd_update.bat` 脚本并在后台隐藏窗口执行，延迟 2 秒后关闭主程序、覆盖替换 exe，并完成自动重启。
* **中文乱码保护**：客户端解压 Windows 版更新包时已全面自动防乱码（通过 `cp437` fallback 修复），并且批处理已默认支持 UTF-8（chcp 65001），能保障中文路径下的升级万无一失。

