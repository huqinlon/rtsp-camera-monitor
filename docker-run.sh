#!/bin/bash
# ============================================
# Docker容器快速运行脚本 - 优化版
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Camera Monitor - Docker 快速启动${NC}"
echo -e "${GREEN}========================================${NC}"

# 检测架构
ARCH=$(uname -m)
case ${ARCH} in
    x86_64)
        IMAGE_TAG="amd64"
        ;;
    aarch64)
        IMAGE_TAG="arm64"
        ;;
    armv7l)
        IMAGE_TAG="arm"
        ;;
    *)
        IMAGE_TAG="amd64"
        ;;
esac

IMAGE_NAME="camera-monitor:${IMAGE_TAG}"
CONTAINER_NAME="camera-monitor"

echo -e "${YELLOW}检测到架构: ${ARCH} -> 使用镜像: ${IMAGE_TAG}${NC}"
echo ""

# -----------------------------------------
# 检查并创建数据目录（根据持久化需求）
# -----------------------------------------
echo -e "${YELLOW}检查数据目录...${NC}"

REQUIRED_DIRS=(
    "data/screenshots"    # 截图存储 - 必需持久化
    "data/videos"         # 视频存储 - 必需持久化
    "data/lowfps"          # 低帧率视频 - 必需持久化
    "data/logs"            # 日志存储 - 必需持久化
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "  创建目录: ${dir}"
        mkdir -p "$dir"
    else
        echo -e "  已存在: ${dir}"
    fi
done

echo ""

# 检查配置文件
if [ ! -f "config.json" ]; then
    echo -e "${YELLOW}配置文件不存在，创建默认配置...${NC}"
    cat > config.json << 'EOF'
{
  "camera": {
    "cameras": [
      {
        "name": "摄像头1",
        "rtsp_url": "rtsp://用户名:密码@摄像头IP:554/码流",
        "enabled": true
      }
    ]
  },
  "storage": {
    "screenshot_dir": "/app/data/screenshots",
    "video_dir": "/app/data/videos",
    "lowfps_dir": "/app/data/lowfps",
    "temp_dir": "/app/data/temp",
    "keep_days": 7
  },
  "scheme1_screenshot": {
    "enabled": true,
    "intervals": [
      {"start": "00:00", "end": "06:00", "interval_seconds": 900},
      {"start": "06:00", "end": "18:00", "interval_seconds": 300},
      {"start": "18:00", "end": "24:00", "interval_seconds": 600}
    ]
  },
  "scheme3_lowfps": {
    "enabled": false,
    "frame_rate": 1,
    "periods": [
      {"start": "22:00", "end": "06:00"}
    ]
  },
  "video_synthesis": {
    "enabled": true,
    "output_fps": 2,
    "codec": "libx264",
    "quality": 23,
    "schedule": "01:00"
  },
  "cloud_upload": {
    "enabled": false,
    "rclone_config": {
      "remote": "your-rclone-name",
      "remote_path": "camera1"
    },
    "upload_screenshots": false,
    "upload_videos": true,
    "schedule": "02:00"
  },
  "statistics": {
    "enabled": false,
    "push_to_memos": true,
    "memos_api_url": "https://memos.example.com/api/v1/memos",
    "memos_token": "your_token",
    "visibility": "PUBLIC",
    "tags": ["监控", "统计"],
    "schedule": "08:00"
  },
  "cleanup": {
    "enabled": true,
    "screenshot_days": 7,
    "video_days": 30,
    "lowfps_days": 7,
    "log_days": 30,
    "schedule": "03:00",
    "min_free_space_gb": 10
  },
  "guardian": {
    "enabled": true,
    "check_interval_minutes": 5,
    "auto_restart": true,
    "max_memory_mb": 500,
    "restart_on_error": true
  },
  "alerts": {
    "enabled": false,
    "push_to_pushplus": true,
    "pushplus_token": "your_token",
    "alert_types": {
      "camera_offline": true,
      "rtsp_connect_failed": true,
      "storage_full": true,
      "screenshot_failed": true,
      "video_synthesis_failed": true,
      "upload_failed": true,
      "process_restart": true,
      "cleanup_failed": true
    },
    "check_interval_minutes": 5,
    "offline_threshold_minutes": 10
  },
  "logging": {
    "enabled": true,
    "log_dir": "/app/data/logs",
    "log_level": "INFO",
    "separate_logs": {
      "screenshot": true,
      "lowfps": true,
      "synthesis": true,
      "upload": true,
      "statistics": true,
      "alerts": true,
      "cleanup": true,
      "guardian": true
    }
  }
}
EOF
    echo -e "${YELLOW}请编辑 config.json 填入正确的摄像头信息${NC}"
fi

echo ""
echo -e "${YELLOW}停止并删除旧容器（如存在）...${NC}"
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo ""
echo -e "${GREEN}启动容器...${NC}"
echo ""
echo "持久化目录映射:"
echo "  ./data/screenshots -> /app/data/screenshots (截图)"
echo "  ./data/videos    -> /app/data/videos    (合成视频)"
echo "  ./data/lowfps    -> /app/data/lowfps    (低帧率视频)"
echo "  ./data/logs      -> /app/data/logs      (运行日志)"
echo ""

docker run -d \
    --name ${CONTAINER_NAME} \
    --restart unless-stopped \
    --network host \
    --privileged \
    -v $(pwd)/config.json:/app/config.json:ro \
    -v $(pwd)/data/screenshots:/app/data/screenshots \
    -v $(pwd)/data/videos:/app/data/videos \
    -v $(pwd)/data/lowfps:/app/data/lowfps \
    -v $(pwd)/data/logs:/app/data/logs \
    -v /etc/localtime:/etc/localtime:ro \
    -v /etc/timezone:/etc/timezone:ro \
    -e TZ=Asia/Shanghai \
    -e PYTHONUNBUFFERED=1 \
    ${IMAGE_NAME}

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  启动成功!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}查看日志:${NC} docker logs -f ${CONTAINER_NAME}"
echo -e "${YELLOW}查看状态:${NC} docker ps | grep ${CONTAINER_NAME}"
echo ""
echo -e "${YELLOW}数据备份:${NC} tar -czvf camera-data.tar.gz data/"
echo ""
