#!/bin/bash
# ============================================
# Docker镜像构建脚本 - AMD64架构
# 适用于: x86服务器、迷你主机、PC
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Camera Monitor - AMD64 构建脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查Docker是否运行
if ! docker info &> /dev/null; then
    echo -e "${RED}错误: Docker 服务未运行${NC}"
    exit 1
fi

# 镜像名称和标签
IMAGE_NAME="camera-monitor"
IMAGE_TAG="amd64"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${YELLOW}构建配置:${NC}"
echo "  镜像名称: ${FULL_IMAGE}"
echo "  架构: AMD64 (x86_64)"
echo ""

# 构建前清理（可选）
read -p "是否清理旧镜像? [y/N]: " CLEANUP
if [[ "$CLEANUP" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}清理旧镜像...${NC}"
    docker rmi ${FULL_IMAGE} 2>/dev/null || true
fi

# 开始构建
echo -e "${GREEN}开始构建镜像...${NC}"
echo ""

docker build \
    --platform linux/amd64 \
    --no-cache \
    -t ${FULL_IMAGE} \
    -f Dockerfile .

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  构建成功!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}下一步操作:${NC}"
echo ""
echo "1. 查看镜像:"
echo "   docker images ${FULL_IMAGE}"
echo ""
echo "2. 运行容器:"
echo "   docker run -d \\
       --name camera-monitor \\
       --restart unless-stopped \\
       --network host \\
       -v \$(pwd)/config.json:/app/config.json:ro \\
       -v \$(pwd)/data:/app/data \\
       ${FULL_IMAGE}"
echo ""
echo "3. 使用 docker-compose:"
echo "   docker-compose up -d"
echo ""
echo "4. 查看日志:"
echo "   docker logs -f camera-monitor"
echo ""
