# ============================================
# TP-LINK Camera Monitor System - Docker Image
# 支持 ARM64 (arm64/v8) 和 AMD64 (amd64) 架构
# ============================================

FROM python:3.11-slim-bookworm

# 防止交互式安装提示
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# 安装基础系统工具（分步安装以提高稳定性）
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl wget git ca-certificates tzdata && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 安装 Python 包编译所需的工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 创建非 root 用户
RUN useradd -m -s /bin/bash camera

# 安装 Python 依赖
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

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
