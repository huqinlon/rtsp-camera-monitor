#!/bin/bash
# =============================================================================
# TP-LINK 摄像头录像压缩系统 - 完整安装脚本
# =============================================================================

echo "============================================"
echo "TP-LINK 摄像头监控系统 - 安装脚本"
echo "============================================"

# 检查root权限
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本"
    echo "用法: sudo bash install.sh"
    exit 1
fi

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "[1/7] 安装系统依赖..."
echo "--------------------------------------------"

# 安装Python依赖
echo "安装Python依赖包..."
pip3 install flask requests apscheduler psutil Pillow > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "  ✓ Python依赖安装完成"
else
    echo "  ✗ Python依赖安装失败"
    exit 1
fi

# 检查FFmpeg
if command -v ffmpeg > /dev/null 2>&1; then
    echo "  ✓ FFmpeg已安装"
else
    echo "安装FFmpeg..."
    apt-get update > /dev/null 2>&1
    apt-get install -y ffmpeg > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✓ FFmpeg安装完成"
    else
        echo "  ✗ FFmpeg安装失败"
    fi
fi

# 检查rclone
if command -v rclone > /dev/null 2>&1; then
    echo "  ✓ rclone已安装"
else
    echo "  ○ rclone未安装（可选，用于云端上传功能）"
fi

echo ""
echo "[2/7] 创建目录结构..."
echo "--------------------------------------------"

# 创建必要的目录（支持自定义安装路径）
INSTALL_DIR="${INSTALL_DIR:-/opt/camera_monitor}"
mkdir -p "${INSTALL_DIR}/{screenshots,videos,lowfps_videos,temp,logs}"
mkdir -p "$SCRIPT_DIR/templates"
mkdir -p "$SCRIPT_DIR/static"
echo "  ✓ 目录创建完成: ${INSTALL_DIR}/"

echo ""
echo "[3/7] 复制配置文件..."
echo "--------------------------------------------"

# 复制配置文件（如果不存在）
if [ ! -f "${INSTALL_DIR}/config.json" ]; then
    cp "$SCRIPT_DIR/config.json" "${INSTALL_DIR}/config.json"
    echo "  ✓ 配置文件已复制到: ${INSTALL_DIR}/config.json"
    echo "  ! 请根据实际情况修改配置文件中的参数"
else
    echo "  ✓ 配置文件已存在: ${INSTALL_DIR}/config.json"
fi

echo ""
echo "[4/7] 设置脚本执行权限..."
echo "--------------------------------------------"

# 设置脚本执行权限
chmod +x "$SCRIPT_DIR/camera_monitor.py"
chmod +x "$SCRIPT_DIR/web_app.py"
chmod +x "$SCRIPT_DIR/guardian.py"
chmod +x "$SCRIPT_DIR/test_full_flow.py"
chmod +x "$SCRIPT_DIR/start_web.sh"
echo "  ✓ 权限设置完成"

echo ""
echo "[5/7] 安装监控服务（可选）..."
echo "--------------------------------------------"

read -p "是否安装监控服务？(y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 复制systemd服务文件
    cp "$SCRIPT_DIR/camera-monitor.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable camera-monitor
    echo "  ✓ 监控服务已安装"
    echo ""
    echo "监控服务命令:"
    echo "  启动: sudo systemctl start camera-monitor"
    echo "  停止: sudo systemctl stop camera-monitor"
    echo "  状态: sudo systemctl status camera-monitor"
else
    echo "  ○ 跳过监控服务安装"
fi

echo ""
echo "[6/7] 安装Web界面服务（可选）..."
echo "--------------------------------------------"

read -p "是否安装Web界面服务？(y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 复制systemd服务文件
    cp "$SCRIPT_DIR/camera-monitor-web.service" /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable camera-monitor-web
    echo "  ✓ Web界面服务已安装"
    echo ""
    echo "Web界面服务命令:"
    echo "  启动: sudo systemctl start camera-monitor-web"
    echo "  停止: sudo systemctl stop camera-monitor-web"
    echo "  状态: sudo systemctl status camera-monitor-web"
else
    echo "  ○ 跳过Web界面服务安装"
fi

echo ""
echo "[7/7] 完成安装..."
echo "--------------------------------------------"

echo ""
echo "============================================"
echo "安装完成！"
echo "============================================"
echo ""
echo "使用方法:"
echo ""
echo "方法1: 使用systemd服务（推荐）"
echo "  启动监控: sudo systemctl start camera-monitor"
echo "  启动Web:  sudo systemctl start camera-monitor-web"
echo "  Web访问:  http://localhost:5000"
echo ""
echo "方法2: 直接运行"
echo "  监控服务: python3 camera_monitor.py"
echo "  Web界面:  bash start_web.sh"
echo ""
echo "方法3: 使用守护进程"
echo "  python3 guardian.py"
echo ""
echo "配置文件位置: ${INSTALL_DIR}/config.json"
echo "日志文件位置: ${INSTALL_DIR}/logs/"
echo ""
echo "============================================"
echo ""
