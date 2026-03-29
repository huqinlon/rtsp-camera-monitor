---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022100a09b76bd77b742bf6a8f4f30a8b03595d97de718979250064fba1432c49d7ba8022041c576b84b311e6cf561eff8c442231ec8e63b055b5c9742fd4b690bfbba4f60
    ReservedCode2: 3045022051aa267708c93c14c400e947639c80f9154b24fd39eba97ecec432fb115788d20221008730ad8840d5a8b453bb19e808eee0b3e3f33a7e113bed5e2dc4568cd119c9d1
---

# TP-LINK Camera Monitor System
# Docker 部署指南

---

## 目录

1. [简介](#1-简介)
2. [环境要求](#2-环境要求)
3. [快速部署](#3-快速部署)
4. [详细部署步骤](#4-详细部署步骤)
5. [架构特定说明](#5-架构特定说明)
6. [配置说明](#6-配置说明)
7. [运维管理](#7-运维管理)
8. [常见问题](#8-常见问题)

---

## 1. 简介

本文档详细介绍如何使用 Docker 和 Docker Compose 部署 TP-LINK 摄像头监控系统。本系统支持以下架构：

| 架构 | 说明 | 适用设备 |
|------|------|----------|
| **AMD64 (x86_64)** | 64位x86处理器 |  Intel/AMD服务器、迷你主机、PC |
| **ARM64 (arm64/v8)** | 64位ARM处理器 | 树莓派4B/5、ARM开发板、NAS |

### Docker 部署优势

- **环境隔离**：所有依赖打包在容器中，避免与主机环境冲突
- **易于迁移**：容器可在不同设备间快速迁移
- **资源控制**：可精确限制CPU、内存使用
- **自动重启**：容器可配置自动重启策略
- **简化维护**：一条命令即可更新到最新版本

---

## 2. 环境要求

### 2.1 硬件要求

| 配置项 | 最低要求 | 推荐配置 |
|--------|----------|----------|
| 内存 | 512MB | 1GB+ |
| 存储 | 4GB | 16GB+ |
| 网络 | 100Mbps | 1Gbps |

### 2.2 软件要求

- **Docker**：20.10.x 或更高版本
- **Docker Compose**：v2.0 或更高版本（可选）
- **操作系统**：Linux（推荐 Ubuntu 20.04+、Debian 11+）

### 2.3 安装 Docker

#### Ubuntu / Debian

```bash
# 更新软件源
sudo apt update
sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker GPG 密钥
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 当前用户加入 docker 组（免sudo）
sudo usermod -aG docker $USER
newgrp docker
```

#### 树莓派 OS (ARM64)

```bash
# 树莓派使用 debian 仓库
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=arm64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

---

## 3. 快速部署

### 3.1 自动部署（推荐）

```bash
# 1. 下载项目文件到服务器
cd /opt
sudo git clone https://your-repo/camera-monitor.git
cd camera-monitor

# 2. 给脚本添加执行权限
chmod +x docker-run.sh docker-build-*.sh

# 3. 构建镜像（根据架构自动选择）
./docker-build-amd64.sh    # AMD64 设备
# 或
./docker-build-arm64.sh    # ARM64 设备

# 4. 编辑配置文件
nano config.json

# 5. 启动容器
./docker-run.sh
```

### 3.2 Docker Compose 部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

---

## 4. 详细部署步骤

### 4.1 项目结构

```
camera-monitor/
├── Dockerfile              # Docker镜像定义
├── docker-compose.yml      # Docker Compose配置
├── docker-run.sh          # 快速运行脚本
├── docker-build-amd64.sh  # AMD64构建脚本
├── docker-build-arm64.sh  # ARM64构建脚本
├── docker-build-all.sh    # 多架构构建脚本
├── config.json           # 系统配置文件
├── modules/              # 功能模块
├── templates/            # Web界面模板
├── requirements.txt     # Python依赖
└── data/                # 数据存储目录（需创建）
```

### 4.2 构建 Docker 镜像

#### 方式一：使用构建脚本

**AMD64 架构：**

```bash
./docker-build-amd64.sh
```

**ARM64 架构：**

```bash
./docker-build-arm64.sh
```

#### 方式二：手动构建

```bash
# AMD64
docker build --platform linux/amd64 -t camera-monitor:amd64 .

# ARM64
docker build --platform linux/arm64/v8 -t camera-monitor:arm64 .
```

### 4.3 配置数据目录

```bash
# 创建数据目录
mkdir -p data/logs data/screenshots data/videos data/lowfps

# 设置权限
chmod 755 data
```

### 4.4 配置 config.json

将项目中的 `config.json` 复制到目标服务器并编辑：

```bash
cp config.json /opt/camera-monitor/
nano /opt/camera-monitor/config.json
```

关键配置项说明：

```json
{
    "camera": {
        "rtsp_url": "rtsp://用户名:密码@摄像头IP:554/码流地址",
        "enabled": true
    },
    "storage": {
        "base_path": "/app",
        "screenshots_dir": "screenshots",
        "videos_dir": "videos",
        "logs_dir": "logs"
    },
    "cloud_upload": {
        "enabled": true,
        "rclone_remote": "你的rclone配置名:目标路径"
    }
}
```

### 4.5 rclone 配置（如使用云端上传）

如果需要云端备份功能，需要配置 rclone：

```bash
# 进入容器配置 rclone
docker exec -it camera-monitor bash

# 配置 rclone
rclone config

# 完成后退出
exit
```

或者直接在主机配置并挂载：

```bash
# 主机配置
rclone config

# 创建 rclone 配置目录
mkdir -p ~/.config/rclone

# 启动时挂载配置
docker run -d \
    ... \
    -v ~/.config/rclone:/config/rclone:ro \
    camera-monitor:amd64
```

### 4.6 启动容器

```bash
# 使用快速启动脚本
./docker-run.sh

# 或手动运行
docker run -d \
    --name camera-monitor \
    --restart unless-stopped \
    --network host \
    --privileged \
    -v $(pwd)/config.json:/app/config.json:ro \
    -v $(pwd)/data/screenshots:/app/screenshots \
    -v $(pwd)/data/videos:/app/videos \
    -v $(pwd)/data/lowfps:/app/lowfps \
    -v $(pwd)/data/logs:/app/logs \
    -v /etc/localtime:/etc/localtime:ro \
    -e TZ=Asia/Shanghai \
    camera-monitor:amd64
```

### 4.7 验证运行

```bash
# 查看容器状态
docker ps | grep camera-monitor

# 查看实时日志
docker logs -f camera-monitor

# 进入容器调试
docker exec -it camera-monitor bash
```

---

## 5. 架构特定说明

### 5.1 AMD64 架构（x86_64）

**适用设备：**

- Intel/AMD 处理器的服务器和 PC
- 迷你主机（如 N5105、N100 等小主机）
- 软路由（如 x86 架构的 RouterOS、OpenWrt）

**构建命令：**

```bash
./docker-build-amd64.sh
```

**镜像标签：** `camera-monitor:amd64`

### 5.2 ARM64 架构（aarch64）

**适用设备：**

- 树莓派 4B / 5
- 斐讯 N1 / S905D 等 ARM 盒子的 Armbian 系统
- NAS 设备（如群晖、威联通的 Docker 环境）
- ARM 服务器

**构建命令：**

```bash
./docker-build-arm64.sh
```

**镜像标签：** `camera-monitor:arm64`

### 5.3 多架构构建（CI/CD 使用）

如果需要同时构建多个架构（需要 buildx 支持）：

```bash
./docker-build-all.sh
```

---

## 6. 配置说明

### 6.1 端口映射

系统默认使用 `host` 网络模式，直接使用主机网络。如需端口映射，修改 `docker-compose.yml`：

```yaml
services:
  camera-monitor:
    network_mode: host
    # 或使用端口映射
    ports:
      - "5000:5000"  # Web界面
```

### 6.2 资源限制

根据设备性能调整资源限制：

```yaml
services:
  camera-monitor:
    deploy:
      resources:
        limits:
          memory: 512M      # 最大内存
          cpus: '1.0'       # 最大CPU核心数
        reservations:
          memory: 256M     # 预留内存
```

### 6.3 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `TZ` | 时区 | `Asia/Shanghai` |
| `PYTHONUNBUFFERED` | Python输出缓冲 | `1` |
| `CAMERA_MONITOR_HOME` | 应用目录 | `/app` |

### 6.4 数据持久化

所有数据通过 Docker volume 持久化：

```bash
# 查看数据卷
docker volume ls | grep camera

# 备份数据
tar -czvf camera-data-backup.tar.gz data/

# 恢复数据
tar -xzvf camera-data-backup.tar.gz
```

---

## 7. 运维管理

### 7.1 日常维护命令

```bash
# 查看容器状态
docker ps

# 查看日志
docker logs -f camera-monitor

# 重启服务
docker restart camera-monitor

# 停止服务
docker stop camera-monitor

# 重新构建并启动
docker-compose up -d --build
```

### 7.2 更新系统

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建镜像
docker-compose build --no-cache

# 3. 重启服务
docker-compose up -d

# 4. 清理旧镜像
docker image prune -f
```

### 7.3 监控容器状态

```bash
# 查看资源使用
docker stats camera-monitor

# 查看容器健康状态
docker inspect --format='{{.State.Health.Status}}' camera-monitor

# 查看容器详细信息
docker inspect camera-monitor
```

### 7.4 日志管理

```bash
# 查看最近100行日志
docker logs --tail 100 camera-monitor

# 查看错误日志
docker logs camera-monitor 2>&1 | grep ERROR

# 导出日志
docker logs camera-monitor > camera-monitor.log
```

### 7.5 备份与恢复

**备份：**

```bash
# 停止容器
docker stop camera-monitor

# 备份数据
tar -czvf camera-monitor-backup-$(date +%Y%m%d).tar.gz \
    config.json \
    data/

# 重新启动
docker start camera-monitor
```

**恢复：**

```bash
# 停止容器
docker stop camera-monitor

# 解压备份
tar -xzvf camera-monitor-backup-YYYYMMDD.tar.gz

# 启动容器
docker start camera-monitor
```

---

## 8. 常见问题

### Q1: 容器无法启动

**问题：** `docker: Error response from daemon: Conflict.`

**解决：** 容器已存在，需要先删除：

```bash
docker rm camera-monitor
docker run ...
```

### Q2: RTSP 连接失败

**问题：** 容器无法连接摄像头

**解决：**

1. 检查摄像头 IP 和端口是否正确
2. 确认网络模式是否正确（建议使用 host 模式）
3. 在容器内测试连接：

```bash
docker exec camera-monitor ffmpeg -i rtsp://...
```

### Q3: 权限问题

**问题：** 无法写入数据目录

**解决：**

```bash
# 修改目录权限
sudo chown -R 1000:1000 data/

# 或在运行时指定用户
docker run ... -u $(id -u):$(id -g) ...
```

### Q4: 内存不足

**问题：** 容器被 OOM killer 终止

**解决：**

1. 增加主机可用内存
2. 减少并发任务数
3. 限制容器内存：

```bash
docker run --memory=512m ...
```

### Q5: 时区不正确

**问题：** 日志时间与实际时间不符

**解决：** 挂载时区文件：

```bash
-v /etc/localtime:/etc/localtime:ro \
-v /etc/timezone:/etc/timezone:ro \
```

### Q6: 构建失败

**问题：** Docker 构建时出错

**解决：**

1. 清理 Docker 缓存：

```bash
docker builder prune -a
```

2. 重新构建：

```bash
docker build --no-cache -t camera-monitor .
```

### Q7: 如何查看 Web 界面

**问题：** 无法访问 Web 管理界面

**解决：**

1. 确认容器是否运行：

```bash
docker exec camera-monitor ps aux | grep web
```

2. 启动 Web 应用：

```bash
docker exec camera-monitor python3 /app/web_app.py &
```

3. 访问地址：`http://服务器IP:5000`

---

## 附录：快速参考

### 常用命令汇总

```bash
# 构建镜像
docker build -t camera-monitor:amd64 .

# 运行容器
docker run -d --name camera-monitor --restart unless-stopped \
    --network host \
    -v $(pwd)/config.json:/app/config.json:ro \
    -v $(pwd)/data:/app/data \
    camera-monitor:amd64

# 查看日志
docker logs -f camera-monitor

# 进入容器
docker exec -it camera-monitor bash

# 停止/启动
docker stop camera-monitor
docker start camera-monitor

# 删除容器
docker rm -f camera-monitor
```

---

**文档版本：** 1.0  
**更新日期：** 2024年  
**适用版本：** Camera Monitor System v1.0+
