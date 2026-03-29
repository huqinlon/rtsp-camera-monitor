---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 304502200a2c916e7027c32d51a7c91bf6fe10d29d7ca83538ef58fd804b34cc2b23c5cb022100a14b206495579f651b3ea1a0a71574f94a15f1ea4f682cc9868dc49b898d177c
    ReservedCode2: 3044022061707184df3738773c2cbe8f194e6770f3a77e341185a9d310753d7a79baf5f102207275bd948e13019a89241b78bd56df71357f8e12de4c9ab1bd6824857548f231
---

# GitHub Actions 自动化构建指南

本文档详细介绍如何创建 GitHub 仓库、配置 Actions 自动构建 Docker 镜像，以及如何使用构建好的镜像部署容器。

---

## 目录

1. [创建 GitHub 仓库](#1-创建-github-仓库)
2. [推送项目文件](#2-推送项目文件)
3. [配置 GitHub Secrets](#3-配置-github-secrets)
4. [配置 Docker Hub](#4-配置-docker-hub)
5. [触发和监控构建](#5-触发和监控构建)
6. [使用构建好的镜像](#6-使用构建好的镜像)
7. [完整示例](#7-完整示例)

---

## 1. 创建 GitHub 仓库

### 1.1 登录 GitHub

访问 https://github.com 并登录您的账号。

### 1.2 创建新仓库

1. 点击右上角的 **+** 图标，选择 **New repository**
2. 填写仓库信息：

| 配置项 | 说明 |
|--------|------|
| **Repository name** | `camera-monitor`（或您喜欢的名称） |
| **Description** | `TP-LINK 摄像头监控系统 Docker 镜像` |
| **Visibility** | Public（公开）或 Private（私有） |
| **Initialize** | 不勾选任何选项（我们将从零开始） |

3. 点击 **Create repository**

### 1.3 仓库结构

创建完成后，您的仓库应包含以下文件：

```
camera-monitor/
├── .github/
│   └── workflows/
│       └── docker-build.yml    # GitHub Actions 工作流
├── modules/                     # Python 模块
├── templates/                   # Web 界面模板
├── config.json                  # 配置文件模板
├── Dockerfile                   # Docker 镜像定义
├── docker-compose.yml           # Docker Compose 配置
├── requirements.txt             # Python 依赖
├── README.md                    # 项目说明
├── DOCKER_IMAGE_README.md       # 镜像使用说明
└── ...
```

---

## 2. 推送项目文件

### 2.1 本地初始化 Git

在项目目录中初始化 Git 仓库：

```bash
cd ~/camera-monitor
git init
git add .
git commit -m "Initial commit: Camera Monitor Docker project"
```

### 2.2 添加远程仓库

将本地仓库关联到 GitHub 仓库（将 `your-username` 替换为您的 GitHub 用户名）：

```bash
git remote add origin https://github.com/your-username/camera-monitor.git
```

### 2.3 推送代码

```bash
# 切换到 main 分支
git checkout -b main

# 推送代码
git push -u origin main
```

### 2.4 验证推送

刷新 GitHub 仓库页面，确认所有文件已上传。

---

## 3. 配置 GitHub Secrets

GitHub Secrets 用于安全存储敏感信息（如 Docker Hub 凭证）。

### 3.1 获取 Docker Hub 访问令牌

1. 登录 Docker Hub：https://hub.docker.com
2. 点击右上角头像，选择 **Account Settings**
3. 左侧菜单选择 **Security**
4. 点击 **New Access Token**
5. 填写令牌描述：`GitHub Actions - Camera Monitor`
6. 复制生成的令牌（请妥善保管，只显示一次）

### 3.2 配置 GitHub Secrets

1. 在 GitHub 仓库页面，点击 **Settings**（设置）
2. 左侧菜单选择 **Secrets and variables** -> **Actions**
3. 点击 **New repository secret**
4. 添加以下两个 Secrets：

| Secret 名称 | 值 |
|--------------|---|
| `DOCKERHUB_USERNAME` | 您的 Docker Hub 用户名 |
| `DOCKERHUB_TOKEN` | 刚才生成的访问令牌 |

### 3.3 验证配置

配置完成后，Secrets 页面应显示：

```
DOCKERHUB_USERNAME   ✓ Updated
DOCKERHUB_TOKEN      ✓ Updated
```

---

## 4. 配置 Docker Hub

### 4.1 确保仓库为公开

如果 Docker Hub 用户名为公开，镜像可以被任何人拉取。

### 4.2 私有仓库（如需要）

如果需要推送私有镜像到 Docker Hub：

1. 在 Docker Hub 创建私有仓库：`camera-monitor`
2. 确保 `docker-build.yml` 中的 `REGISTRY` 和 `IMAGE_NAME` 正确配置

---

## 5. 触发和监控构建

### 5.1 触发构建的方式

| 方式 | 触发条件 |
|------|----------|
| **自动触发** | 推送代码到 main 分支 |
| **版本发布** | 创建 Git 标签（如 `v1.0.0`） |
| **手动触发** | 在 GitHub Actions 页面手动运行 |

### 5.2 推送代码触发构建

```bash
# 修改代码后推送
git add .
git commit -m "Update configuration"
git push origin main
```

### 5.3 创建标签发布版本

```bash
# 创建标签
git tag v1.0.0

# 推送标签
git push origin v1.0.0
```

### 5.4 手动触发构建

1. 在 GitHub 仓库页面，点击 **Actions** 标签
2. 左侧选择 **Build and Push Docker Image**
3. 点击 **Run workflow**
4. 选择分支并点击 **Run workflow**

### 5.5 监控构建进度

1. 点击 **Actions** 标签
2. 点击正在运行的工作流
3. 查看各 job 的实时状态：

```
✓ Lint                    # 代码检查
✓ Build AMD64            # AMD64 构建
✓ Build ARM64            # ARM64 构建
✓ Create Manifest        # 创建多架构清单
✓ Build Report           # 生成报告
```

### 5.6 查看构建日志

点击任意 job 可以查看详细日志：

```log
#24 Building AMD64
Building image with docker buildx...
#25 exporting to image
Image pushed: docker.io/your-username/camera-monitor:amd64-latest
```

---

## 6. 使用构建好的镜像

### 6.1 查看可用镜像

构建完成后，访问 Docker Hub 查看镜像：

```
https://hub.docker.com/r/your-username/camera-monitor
```

### 6.2 拉取镜像

```bash
# AMD64 设备
docker pull docker.io/your-username/camera-monitor:amd64-latest

# ARM64 设备
docker pull docker.io/your-username/camera-monitor:arm64-latest

# 自动选择架构
docker pull docker.io/your-username/camera-monitor:latest
```

### 6.3 部署容器

#### 步骤 1：创建项目目录

```bash
mkdir -p ~/camera-monitor
cd ~/camera-monitor

# 创建数据目录
mkdir -p data/{screenshots,videos,lowfps,logs}
```

#### 步骤 2：创建配置文件

创建 `config.json`：

```bash
nano config.json
```

填入您的配置：

```json
{
  "camera": {
    "cameras": [
      {
        "name": "客厅摄像头",
        "rtsp_url": "rtsp://admin:您的密码@192.168.1.2:554/stream1",
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

#### 步骤 3：创建 docker-compose.yml

```bash
nano docker-compose.yml
```

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

#### 步骤 4：启动容器

```bash
# 拉取最新镜像
docker compose pull

# 启动服务
docker compose up -d
```

#### 步骤 5：验证运行

```bash
# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f
```

#### 步骤 6：访问 Web 界面

打开浏览器访问：

```
http://服务器IP:5000
```

---

## 7. 完整示例

### 7.1 一键部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash
# Camera Monitor 一键部署脚本

set -e

# 配置
DOCKER_IMAGE="your-username/camera-monitor"
PROJECT_DIR="/opt/camera-monitor"

echo "=========================================="
echo "Camera Monitor 部署脚本"
echo "=========================================="

# 创建目录
echo "[1/6] 创建项目目录..."
mkdir -p ${PROJECT_DIR}/{screenshots,videos,lowfps,logs}

# 拉取镜像
echo "[2/6] 拉取 Docker 镜像..."
docker pull ${DOCKER_IMAGE}:latest

# 停止现有容器
echo "[3/6] 停止现有容器..."
docker compose -f ${PROJECT_DIR}/docker-compose.yml down 2>/dev/null || true

# 复制配置文件
echo "[4/6] 复制配置文件..."
if [ ! -f "${PROJECT_DIR}/config.json" ]; then
    cat > ${PROJECT_DIR}/config.json << 'EOF'
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
    echo "请编辑 ${PROJECT_DIR}/config.json 填入摄像头信息"
fi

# 启动服务
echo "[5/6] 启动服务..."
cd ${PROJECT_DIR}
docker compose up -d

# 验证
echo "[6/6] 验证服务..."
sleep 3
docker compose ps

echo ""
echo "=========================================="
echo "部署完成!"
echo "=========================================="
echo ""
echo "访问 Web 界面: http://服务器IP:5000"
echo "查看日志: docker compose -f ${PROJECT_DIR}/docker-compose.yml logs -f"
```

运行部署脚本：

```bash
chmod +x deploy.sh
sudo ./deploy.sh
```

### 7.2 更新镜像脚本

创建 `update.sh`：

```bash
#!/bin/bash
# Camera Monitor 更新脚本

set -e

DOCKER_IMAGE="your-username/camera-monitor"
PROJECT_DIR="/opt/camera-monitor"

echo "=========================================="
echo "Camera Monitor 更新脚本"
echo "=========================================="

# 拉取最新镜像
echo "[1/3] 拉取最新镜像..."
docker pull ${DOCKER_IMAGE}:latest

# 重启容器
echo "[2/3] 重启服务..."
cd ${PROJECT_DIR}
docker compose up -d

# 查看状态
echo "[3/3] 服务状态..."
docker compose ps

echo ""
echo "=========================================="
echo "更新完成!"
echo "=========================================="
```

---

## 附录：镜像标签说明

| 标签 | 来源 | 说明 |
|------|------|------|
| `amd64-latest` | main 分支推送 | 最新 AMD64 镜像 |
| `arm64-latest` | main 分支推送 | 最新 ARM64 镜像 |
| `latest` | main 分支推送 | 多架构镜像 |
| `amd64-{sha}` | 每次提交 | 特定版本 |
| `v1.0.0` | Git 标签 | 正式版本 |

---

## 故障排查

### Q1: 构建失败 "unauthorized: authentication required"

**原因：** Docker Hub 凭证配置错误

**解决：**
1. 确认 Secrets 中的 `DOCKERHUB_USERNAME` 和 `DOCKERHUB_TOKEN` 正确
2. 确认 Docker Hub 访问令牌未过期

### Q2: 构建超时

**原因：** GitHub Actions 免费版有时间限制

**解决：**
1. 优化 Dockerfile，减少构建时间
2. 使用 GitHub 付费版增加构建时间

### Q3: ARM64 构建失败

**原因：** QEMU 模拟问题

**解决：**
确保 `docker-build.yml` 中正确配置了 QEMU：

```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3
```

---

**文档版本：** 1.0
**更新日期：** 2026-03-28
