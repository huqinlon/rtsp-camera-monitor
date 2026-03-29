---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 304502210083fe36d68cdfcbc2d9a2cc387ba7601d012179df3f90b11cd89747f7abbe8d0902205786c6c8bbe6b4ca746545ae695f77f4bb11c58c0ebacca3353b77edca4651f8
    ReservedCode2: 3046022100f88ce9bca3cdd6a7b839e8780ade50950ab03ba525861ca0149e3be61953738e022100eebc3b45653defeb30cce6f1886eb0fef17c37ae7459171f548e2231373f3c81
---

# Camera Monitor Docker 镜像

预构建的 Docker 镜像，支持 AMD64 和 ARM64 架构，开箱即用。

## 快速开始

### 拉取镜像

**AMD64 架构（Intel/AMD 处理器）：**

```bash
docker pull docker.io/your-username/camera-monitor:amd64-latest
```

**ARM64 架构（树莓派、ARM 开发板）：**

```bash
docker pull docker.io/your-username/camera-monitor:arm64-latest
```

**自动选择架构（推荐）：**

```bash
docker pull docker.io/your-username/camera-monitor:latest
```

### 部署容器

#### 方式一：使用 Docker Compose

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  camera-monitor:
    image: docker.io/your-username/camera-monitor:latest
    container_name: camera-monitor
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config.json:/app/config.json:ro
      - ./data/screenshots:/app/data/screenshots
      - ./data/videos:/app/data/videos
      - ./data/lowfps:/app/data/lowfps
      - ./data/logs:/app/data/logs
      - ~/.config/rclone:/config/rclone:ro
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    environment:
      - TZ=Asia/Shanghai
      - PYTHONUNBUFFERED=1

  camera-web:
    image: docker.io/your-username/camera-monitor:latest
    container_name: camera-web
    restart: unless-stopped
    ports:
      - "5000:5000"
    command: ["python3", "/app/web_app.py"]
    volumes:
      - ./config.json:/app/config.json:ro
      - ./data/logs:/app/data/logs
      - /etc/localtime:/etc/localtime:ro
      - /etc/timezone:/etc/timezone:ro
    environment:
      - TZ=Asia/Shanghai
      - FLASK_ENV=production
```

启动服务：

```bash
docker compose up -d
```

#### 方式二：直接运行

```bash
# 创建数据目录
mkdir -p data/{screenshots,videos,lowfps,logs}

# 运行容器
docker run -d \
    --name camera-monitor \
    --restart unless-stopped \
    --network host \
    --privileged \
    -v $(pwd)/config.json:/app/config.json:ro \
    -v $(pwd)/data/screenshots:/app/data/screenshots \
    -v $(pwd)/data/videos:/app/data/videos \
    -v $(pwd)/data/lowfps:/app/data/lowfps \
    -v $(pwd)/data/logs:/app/data/logs \
    -e TZ=Asia/Shanghai \
    docker.io/your-username/camera-monitor:latest
```

### 访问 Web 界面

部署完成后，打开浏览器访问：

```
http://服务器IP:5000
```

## 镜像标签说明

| 标签 | 说明 | 适用场景 |
|------|------|----------|
| `latest` | 多架构镜像，自动适配 | 生产环境推荐 |
| `amd64-latest` | 仅 AMD64 架构 | Intel/AMD 服务器 |
| `arm64-latest` | 仅 ARM64 架构 | 树莓派、ARM 设备 |
| `amd64-{commit}` | 指定提交版本 | 特定版本调试 |
| `arm64-{commit}` | 指定提交版本 | 特定版本调试 |
| `v1.0.0` | 语义化版本 | 版本固定使用 |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `TZ` | `Asia/Shanghai` | 时区设置 |
| `PYTHONUNBUFFERED` | `1` | Python 输出缓冲 |
| `CONFIG_PATH` | `/app/config.json` | 配置文件路径 |
| `DATA_BASE_DIR` | `/app/data` | 数据目录 |
| `LOG_DIR` | `/app/data/logs` | 日志目录 |
| `WEB_SECRET_KEY` | `change-this-secret-key-in-production` | Web 会话密钥 |

## 数据持久化

必须持久化的目录：

| 宿主机路径 | 容器内路径 | 用途 |
|------------|------------|------|
| `./data/screenshots` | `/app/data/screenshots` | 截图文件 |
| `./data/videos` | `/app/data/videos` | 合成视频 |
| `./data/lowfps` | `/app/data/lowfps` | 低帧率视频 |
| `./data/logs` | `/app/data/logs` | 运行日志 |

## 配置文件

创建 `config.json` 配置文件：

```json
{
  "camera": {
    "cameras": [
      {
        "name": "摄像头1",
        "rtsp_url": "rtsp://用户名:密码@摄像头IP:554/stream1",
        "enabled": true
      }
    ]
  },
  "storage": {
    "screenshot_dir": "/app/data/screenshots",
    "video_dir": "/app/data/videos",
    "lowfps_dir": "/app/data/lowfps",
    "temp_dir": "/app/data/temp"
  },
  "scheme1_screenshot": {
    "enabled": true,
    "intervals": [
      {"start": "00:00", "end": "06:00", "interval_seconds": 900},
      {"start": "06:00", "end": "18:00", "interval_seconds": 300},
      {"start": "18:00", "end": "24:00", "interval_seconds": 600}
    ]
  },
  "video_synthesis": {
    "enabled": true,
    "schedule": "01:00",
    "output_fps": 2,
    "quality": 23
  }
}
```

## 常见问题

### Q1: 如何查看容器日志？

```bash
docker logs -f camera-monitor
```

### Q2: 如何进入容器？

```bash
docker exec -it camera-monitor bash
```

### Q3: 如何更新到最新版本？

```bash
docker pull docker.io/your-username/camera-monitor:latest
docker compose down
docker compose up -d
```

### Q4: ARM64 镜像在 amd64 机器上能运行吗？

不能。不同架构的 CPU 指令集不兼容，需要使用对应架构的镜像，或者使用 `latest` 标签让 Docker 自动选择。

## 构建自己的镜像

如果需要自定义镜像，可以手动构建：

```bash
# AMD64
docker build --platform linux/amd64 -t camera-monitor:amd64 .

# ARM64
docker build --platform linux/arm64/v8 -t camera-monitor:arm64 .
```

## 许可证

MIT License

## 联系方式

- Issue: https://github.com/your-username/camera-monitor/issues
