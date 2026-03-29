# ============================================
# TP-LINK Camera Monitor System - Docker Image
# 支持 ARM64 (arm64/v8) 和 AMD64 (amd64) 架构
# ============================================

# -----------------------------
# 基础阶段：安装系统依赖
# -----------------------------
FROM debian:bookworm-slim AS base

# 防止交互式安装提示
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# 安装基础系统工具
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    curl \
    wget \
    git \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Python 依赖阶段
# -----------------------------
FROM base AS python-deps

# 升级 pip
# hadolint ignore=DL3008
RUN pip3 install --no-cache-dir --break-system-packages --upgrade pip setuptools wheel

# 安装 Python 依赖
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# -----------------------------
# 最终镜像构建
# -----------------------------
FROM base AS runtime

# 复制 Python 依赖
COPY --from=python-deps /usr/local/lib/python3.11/dist-packages /usr/local/lib/python3.11/dist-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

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

# 创建非 root 用户
RUN useradd -m -s /bin/bash camera && \
    chown -R camera:camera /app

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
