#!/bin/bash
# =============================================================================
# TP-LINK 摄像头监控系统 - Web界面启动脚本
# =============================================================================

echo "============================================"
echo "TP-LINK 摄像头监控系统 - Web管理界面"
echo "============================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 启动选项
HOST="0.0.0.0"
PORT=5000
DEBUG=false

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--host IP] [--port PORT] [--debug]"
            exit 1
            ;;
    esac
done

# 检查Python依赖
echo "检查Python依赖..."
pip3 show flask > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "安装Flask依赖..."
    pip3 install flask requests apscheduler psutil Pillow > /dev/null 2>&1
fi

# 检查端口是否被占用
if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
    echo "警告: 端口 $PORT 已被占用"
fi

# 创建必要的目录
mkdir -p templates
mkdir -p static
mkdir -p /mnt/sd/camera1/logs

echo ""
echo "启动Web管理界面..."
echo "访问地址: http://$HOST:$PORT"
echo "按 Ctrl+C 停止服务"
echo "============================================"

# 启动Web服务
cd "$SCRIPT_DIR"
python3 web_app.py --host "$HOST" --port "$PORT" --debug
