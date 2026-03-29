#!/bin/bash
# ============================================
# Docker多架构镜像构建脚本
# 使用Docker Buildx同时构建ARM64和AMD64镜像
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Camera Monitor - 多架构构建脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装${NC}"
    echo "请先安装 Docker: https://docs.docker.com/engine/install/"
    exit 1
fi

# 检查Buildx是否可用
if ! docker buildx version &> /dev/null; then
    echo -e "${YELLOW}Docker Buildx 不可用，正在启用...${NC}"
    docker buildx install || docker buildx create --use
fi

# 创建构建器（如果不存在）
BUILDER_NAME="camera-monitor-builder"

if ! docker buildx inspect ${BUILDER_NAME} &> /dev/null; then
    echo -e "${YELLOW}创建构建器: ${BUILDER_NAME}${NC}"
    docker buildx create --name ${BUILDER_NAME} --driver docker-container --use
fi

docker buildx use ${BUILDER_NAME}

# 镜像配置
IMAGE_NAME="camera-monitor"
REGISTRY=""  # 如需推送到仓库，填写如: docker.io/username/

echo -e "${YELLOW}构建配置:${NC}"
echo "  镜像名称: ${IMAGE_NAME}"
echo "  支持架构: linux/amd64, linux/arm64/v8"
echo ""

# 选择构建模式
echo -e "${BLUE}请选择构建模式:${NC}"
echo "  1) 同时构建 AMD64 + ARM64（推荐，需要两台机器或QEMU）"
echo "  2) 仅构建 AMD64"
echo "  3) 仅构建 ARM64"
read -p "请选择 [1-3]: " BUILD_MODE

case ${BUILD_MODE} in
    1)
        PLATFORMS="linux/amd64,linux/arm64/v8"
        TAG_SUFFIX=""
        ;;
    2)
        PLATFORMS="linux/amd64"
        TAG_SUFFIX="-amd64"
        ;;
    3)
        PLATFORMS="linux/arm64/v8"
        TAG_SUFFIX="-arm64"
        ;;
    *)
        echo -e "${RED}无效选择，默认使用模式1${NC}"
        PLATFORMS="linux/amd64,linux/arm64/v8"
        TAG_SUFFIX=""
        ;;
esac

# 镜像标签
FULL_IMAGE="${REGISTRY}${IMAGE_NAME}${TAG_SUFFIX}"

echo -e "${YELLOW}开始构建...${NC}"
echo ""

# 执行构建
docker buildx build \
    --platform ${PLATFORMS} \
    --no-cache \
    -t ${FULL_IMAGE} \
    -f Dockerfile \
    --push false \
    .

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  构建完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}生成的镜像:${NC}"
docker images ${IMAGE_NAME}
echo ""

# 清理构建器（可选）
read -p "是否清理构建器? [y/N]: " CLEANUP
if [[ "$CLEANUP" =~ ^[Yy]$ ]]; then
    docker buildx rm ${BUILDER_NAME}
fi

echo ""
echo -e "${GREEN}部署说明:${NC}"
echo ""
echo "本地加载AMD64镜像:"
echo "  docker buildx build --platform linux/amd64 -t ${IMAGE_NAME}:amd64 --load -f Dockerfile ."
echo ""
echo "本地加载ARM64镜像:"
echo "  docker buildx build --platform linux/arm64/v8 -t ${IMAGE_NAME}:arm64 --load -f Dockerfile ."
echo ""
echo "推送到远程仓库:"
echo "  docker buildx build --platform linux/amd64,linux/arm64/v8 -t ${REGISTRY}${IMAGE_NAME}:latest --push -f Dockerfile ."
echo ""
