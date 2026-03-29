# ============================================
# TP-LINK Camera Monitor System - Docker Image
# 支持 ARM64 (arm64/v8) 和 AMD64 (amd64) 架构
# ============================================

FROM python:3.11-slim-bookworm

# 防止交互式安装提示
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_TIMEOUT=300

# 安装基础系统工具和 Python 依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    wget \
    git \
    ca-certificates \
    tzdata \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libopenjp2-7 \
    libtiff5 \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -s /bin/bash camera

# 安装 Python 依赖（使用宽松版本约束）
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt || \
    pip install --no-cache-dir -r /tmp/requirements.txt --prefer-binary || \
    pip install --no-cache-dir -r /tmp/requirements.txt --no-build-isolation

# 创建应用目录
RUN mkdir -p /app/modules /app/templates /app/data/logs /app/data/screenshots /app/data/videos /app/data/lowfps /app/data/temp

# 复制应用文件
COPY modules/ /app/modules/
COPY templates/ /app/templates/
COPY *.py /app/
COPY *.json /app/
COPY *.md /app/

# 复制脚本文件
COPY install.sh /usr/local/bin/
COPY start_web.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# 设置权限
RUN chown -R camera:camera /app

# 设置工作目录
WORKDIR /app

# 环境变量
ENV TZ=Asia/Shanghai
ENV PYTHONPATH=/app
ENV CAMERA_MONITOR_HOME=/app
ENV CONFIG_PATH=/app/config.json
ENV DATA_BASE_DIR=/app/data
ENV LOG_DIR=/app/data/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=5)" || exit 1

# 切换到非 root 用户
USER camera

# 暴露端口
EXPOSE 5000

# 默认启动命令
ENTRYPOINT ["python3", "/app/camera_monitor.py"]
