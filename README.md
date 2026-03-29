---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022055edcd95c90f67fb1cd329da380a0a09a390ce488c3e484e6ffab44fd67f38cc022100ce15261b4922f3fd9aed17665aa4b42ed59ca4a382bd334398dac3166314589c
    ReservedCode2: 3046022100909eea8e48d713120aaf0d7f650d35fc6110ca85a60559cd174d94c45f0df4b802210081e2b0c54c893f6cde4d288da712aa33da9cc0f55d4a512a644d753404dcef3e
---

# TP-LINK Camera Monitor

一个功能完整的摄像头监控系统，支持定时截图、视频合成、云端上传、统计推送和 Web 管理界面。

## 特性

- **定时截图**：分时段自适应截图间隔，智能分配存储
- **视频合成**：每日自动将截图合成为浓缩视频，快速浏览全天概况
- **云端上传**：支持 rclone 上传到各种云存储
- **统计推送**：每日统计信息推送到 Memos
- **告警推送**：异常情况通过 PushPlus 及时通知
- **自动清理**：自动清理过期文件，防止磁盘满
- **进程守护**：24 小时无人值守运行，异常自动重启
- **Web 管理界面**：可视化配置管理、状态监控、日志查看
- **Docker 支持**：预构建镜像，支持 AMD64 和 ARM64 架构

## 快速开始

### 使用预构建镜像（推荐）

```bash
# 创建项目目录
mkdir -p camera-monitor && cd camera-monitor

# 创建配置文件
cat > config.json << 'EOF'
{
  "camera": {
    "cameras": [
      {
        "name": "摄像头",
        "rtsp_url": "rtsp://用户名:密码@IP:554/stream1",
        "enabled": true
      }
    ]
  },
  "storage": {
    "screenshot_dir": "/app/data/screenshots",
    "video_dir": "/app/data/videos",
    "lowfps_dir": "/app/data/lowfps",
    "temp_dir": "/app/data/temp"
  }
}
EOF

# 创建 docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  camera-monitor:
    image: your-username/camera-monitor:latest
    container_name: camera-monitor
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./config.json:/app/config.json:ro
      - ./data/screenshots:/app/data/screenshots
      - ./data/videos:/app/data/videos
      - ./data/lowfps:/app/data/lowfps
      - ./data/logs:/app/data/logs
      - /etc/localtime:/etc/localtime:ro
    environment:
      - TZ=Asia/Shanghai

  camera-web:
    image: your-username/camera-monitor:latest
    container_name: camera-web
    restart: unless-stopped
    ports:
      - "5000:5000"
    command: ["python3", "/app/web_app.py"]
    volumes:
      - ./config.json:/app/config.json:ro
      - ./data/logs:/app/data/logs
    environment:
      - TZ=Asia/Shanghai
EOF

# 创建数据目录并启动
mkdir -p data/{screenshots,videos,lowfps,logs}
docker compose up -d
```

访问 **http://服务器IP:5000** 进入 Web 管理界面。

### 手动构建

```bash
# 克隆仓库
git clone https://github.com/your-username/camera-monitor.git
cd camera-monitor

# 构建镜像
docker build --platform linux/amd64 -t camera-monitor:amd64 .
# 或 ARM64
docker build --platform linux/arm64/v8 -t camera-monitor:arm64 .

# 运行
docker compose up -d
```

## 架构支持

| 架构 | 镜像标签 | 适用设备 |
|------|----------|----------|
| AMD64 | `amd64-latest` | Intel/AMD 服务器、迷你主机 |
| ARM64 | `arm64-latest` | 树莓派 4B/5、ARM 开发板、NAS |

## 目录结构

```
camera-monitor/
├── .github/
│   ├── workflows/
│   │   └── docker-build.yml    # GitHub Actions 自动构建
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.yml      # Bug 报告模板
│   │   └── feature_request.yml  # 功能请求模板
│   └── PULL_REQUEST_TEMPLATE.md # PR 模板
├── modules/                     # Python 功能模块
├── templates/                   # Web 界面模板
├── config.json                  # 配置文件
├── Dockerfile                   # Docker 镜像定义
├── docker-compose.yml           # Docker Compose 配置
├── requirements.txt             # Python 依赖
├── README.md                    # 主说明文档
├── DOCKER_IMAGE_README.md       # Docker 镜像使用指南
├── GITHUB_ACTIONS_GUIDE.md      # GitHub Actions 指南
└── LINUX_DOCKER_DEPLOYMENT.md   # Linux 部署详细指南
```

## 文档

- [Docker 镜像使用指南](DOCKER_IMAGE_README.md) - 镜像拉取和快速部署
- [GitHub Actions 自动构建指南](GITHUB_ACTIONS_GUIDE.md) - CI/CD 配置
- [Linux Docker 部署详细指南](LINUX_DOCKER_DEPLOYMENT.md) - 完整部署步骤

## 配置说明

### 摄像头配置

```json
"camera": {
    "cameras": [
        {
            "name": "摄像头名称",
            "rtsp_url": "rtsp://用户名:密码@IP:554/码流",
            "enabled": true
        }
    ]
}
```

### 截图配置

```json
"scheme1_screenshot": {
    "enabled": true,
    "intervals": [
        {"start": "00:00", "end": "06:00", "interval_seconds": 900},
        {"start": "06:00", "end": "18:00", "interval_seconds": 300},
        {"start": "18:00", "end": "24:00", "interval_seconds": 600}
    ]
}
```

## 常见问题

### Q: 如何查看日志？

```bash
docker logs -f camera-monitor
```

### Q: 如何更新到最新版本？

```bash
docker compose pull
docker compose up -d
```

### Q: 支持多摄像头吗？

是的，在 `config.json` 的 `camera.cameras` 数组中添加多个摄像头配置。

### Q: 如何使用 GitHub Actions 自动构建？

参见 [GitHub Actions 指南](GITHUB_ACTIONS_GUIDE.md)。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 作者

MiniMax Agent
