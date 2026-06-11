#!/bin/bash
# scripts/build_mac_app.sh
# 一键编译生成 macOS 独立应用程序 (.app) 并集成 Dock/应用高清图标。

# 确保遇到错误立即终止
set -e

# 获取脚本所在目录的绝对路径，并切换到项目根目录
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# 定义应用程序名称（大众认知名：密码管家）
APP_NAME="密码管家"
APP_BUNDLE="dist/${APP_NAME}.app"

echo "=== 1. 开始处理 macOS 原生图标转换 ==="
PNG_ICON="src/password_manager/gui/app_icon.png"
ICNS_ICON="src/password_manager/gui/app_icon.icns"

if [ -f "$PNG_ICON" ]; then
    echo "发现 PNG 图标，正在利用 macOS sips & iconutil 编译成原生 .icns 格式..."
    ICON_DIR="src/password_manager/gui/app_icon.iconset"
    mkdir -p "$ICON_DIR"

    # 生成各分辨率 PNG 文件，供 Retina 屏与普通屏自适应
    sips -z 16 16     "$PNG_ICON" --out "$ICON_DIR/icon_16x16.png" > /dev/null 2>&1
    sips -z 32 32     "$PNG_ICON" --out "$ICON_DIR/icon_16x16@2x.png" > /dev/null 2>&1
    sips -z 32 32     "$PNG_ICON" --out "$ICON_DIR/icon_32x32.png" > /dev/null 2>&1
    sips -z 64 64     "$PNG_ICON" --out "$ICON_DIR/icon_32x32@2x.png" > /dev/null 2>&1
    sips -z 128 128   "$PNG_ICON" --out "$ICON_DIR/icon_128x128.png" > /dev/null 2>&1
    sips -z 256 256   "$PNG_ICON" --out "$ICON_DIR/icon_128x128@2x.png" > /dev/null 2>&1
    sips -z 256 256   "$PNG_ICON" --out "$ICON_DIR/icon_256x256.png" > /dev/null 2>&1
    sips -z 512 512   "$PNG_ICON" --out "$ICON_DIR/icon_256x256@2x.png" > /dev/null 2>&1
    sips -z 512 512   "$PNG_ICON" --out "$ICON_DIR/icon_512x512.png" > /dev/null 2>&1
    sips -z 1024 1024 "$PNG_ICON" --out "$ICON_DIR/icon_512x512@2x.png" > /dev/null 2>&1

    # 制作 icns
    iconutil -c icns "$ICON_DIR" -o "$ICNS_ICON"
    rm -rf "$ICON_DIR"
    echo "原生 .icns 图标生成成功: $ICNS_ICON"
else
    echo "警告: 未在 $PNG_ICON 找到源图标文件，将使用默认图标进行打包。"
fi

echo ""
echo "=== 2. 开始使用 PyInstaller 进行打包 ==="
# 清理以前的构建产物
rm -rf build dist

# 调用 PyInstaller 
# --windowed/--noconsole: 窗口模式，启动时不弹出终端黑窗口
# --paths="src": 包含源码目录
# --add-data: 把 app_icon.png 也打进包中，方便 main_window 启动时加载
.venv/bin/pyinstaller \
  --noconfirm \
  --windowed \
  --name="${APP_NAME}" \
  --icon="$ICNS_ICON" \
  --add-data="src/password_manager/gui/app_icon.png:password_manager/gui" \
  --add-data=".env:." \
  --paths="src" \
  run_gui.py

echo ""
echo "=== 3. 打包完成 ==="
if [ -d "$APP_BUNDLE" ]; then
    # 去除 Info.plist 中 CFBundleIconFile 值的 .icns 后缀以符合苹果官方图标规范，解决 @ 纸张占位图标问题
    sed -i '' 's/app_icon.icns/app_icon/g' "$APP_BUNDLE/Contents/Info.plist" || true
    
    # 强制让 Finder/Launch Services 丢弃可能存在的旧图标缓存并重新载入
    touch "$APP_BUNDLE"
    touch "$APP_BUNDLE/Contents/Info.plist"
    
    # 在系统级强制刷新 Launch Services 应用包的注册关联
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$APP_BUNDLE" >/dev/null 2>&1 || \
    /System/Library/Frameworks/CoreServices.framework/Versions/A/Frameworks/LaunchServices.framework/Versions/A/Support/lsregister -f "$APP_BUNDLE" >/dev/null 2>&1 || true
    
    # 额外打包一份保留完整 Unix 可执行权限的 .zip，方便用户通过网络一键发给别人使用
    echo "正在将应用打包为防权限丢失的 zip 压缩包..."
    cd dist
    zip -ry "${APP_NAME}_mac_dist.zip" "${APP_NAME}.app" >/dev/null 2>&1 || true
    cd ..
    
    echo "恭喜！macOS 应用程序打包成功！"
    echo "应用包路径: $PROJECT_DIR/$APP_BUNDLE"
    echo "分发用 ZIP 包 (保留可执行权限): $PROJECT_DIR/dist/${APP_NAME}_mac_dist.zip"
    echo "您现在可以将其拖入您的 Applications 或程序坞 (Dock) 中直接点击打开！"
else
    echo "错误: 未能生成 $APP_BUNDLE，请检查上方的打包错误日志。"
    exit 1
fi
