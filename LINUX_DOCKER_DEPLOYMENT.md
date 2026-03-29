---
AIGC:
    ContentProducer: Minimax Agent AI
    ContentPropagator: Minimax Agent AI
    Label: AIGC
    ProduceID: "00000000000000000000000000000000"
    PropagateID: "00000000000000000000000000000000"
    ReservedCode1: 3045022075a0e331d071e52c891640b80687a0156ae1b83a609aa67bb80e3ce6bf04252c022100b2fd5dbf0cc9e771db3f202b3f59dcfc8fe668054f0c8804f4aa8d5544c7a227
    ReservedCode2: 3046022100bb26e4d2ba290c11434ecb6d798181dbd8d9719a49eb72be17bc43c25dadf2a8022100a6d840172d3b1a327e36767722f2a31c32c6ba6b5b0c1f270d0cd331e56225dd
---

# TP-LINK 摄像头监控系统 - Linux Docker 部署详细指南

## 目录

1. [环境准备](#1-环境准备)
2. [项目下载](#2-项目下载)
3. [构建 Docker 镜像](#3-构建-docker-镜像)
4. [配置与部署](#4-配置与部署)
5. [Docker Compose 部署](#5-docker-compose-部署)
6. [Web 管理界面](#6-web-管理界面)
7. [验证与测试](#7-验证与测试)
8. [运维管理](#8-运维管理)
9. [常见问题](#9-常见问题)

---

## 1. 环境准备

### 1.1 检查系统架构

首先确认目标设备的系统架构，以便选择正确的镜像构建方式：

```bash
# 查看系统架构
uname -m

# 查看详细系统信息
cat /etc/os-release
```

常见架构对应的输出：

| 架构标识 | 说明 | 适用设备 |
|----------|------|----------|
| `x86_64` | AMD64 | Intel/AMD 服务器、迷你主机、PC |
| `aarch64` | ARM64 | 树莓派 4B/5、ARM 开发板、NAS |
| `armv7l` | ARM32 | 树莓派 3B 及以下（较少支持） |

### 1.2 安装 Docker

#### Ubuntu / Debian 系统

```bash
# 第一步：更新软件源并安装基础工具
sudo apt update
sudo apt upgrade -y
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 第二步：添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 第三步：添加 Docker 仓库（根据系统选择）
# Debian 系统
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Ubuntu 系统（如果需要）
# echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 第四步：安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 第五步：启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 第六步：验证安装
docker --version
docker compose version
```

#### CentOS / RHEL 系统

```bash
# 安装基础工具
sudo yum install -y yum-utils device-mapper-persistent-data lvm2

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### 树莓派 OS (ARM64)

```bash
# 添加 Docker 仓库
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=arm64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian bookworm stable" | sudo tee /etc/apt/sources.list.d/docker.list

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 1.3 配置 Docker 权限

将当前用户加入 docker 组，避免每次使用 sudo：

```bash
# 将用户加入 docker 组（将 username 替换为实际用户名）
sudo usermod -aG docker $USER

# 使组成员权限生效（需要重新登录，或执行以下命令）
newgrp docker

# 验证权限配置
docker ps
```

如果执行 `docker ps` 没有报错，说明权限配置成功。

---

## 2. 项目下载

### 2.1 创建项目目录

```bash
# 创建项目目录
mkdir -p ~/camera-monitor
cd ~/camera-monitor

# 验证目录
pwd
```

### 2.2 下载项目文件

如果有 Git 仓库：

```bash
git clone https://your-repo/camera-monitor.git .
```

或者手动复制项目文件到该目录。确保项目包含以下核心文件：

```
camera-monitor/
├── Dockerfile              # Docker 镜像定义
├── docker-compose.yml      # Docker Compose 配置
├── docker-run.sh          # 快速运行脚本
├── docker-build-amd64.sh  # AMD64 构建脚本
├── docker-build-arm64.sh  # ARM64 构建脚本
├── config.json            # 配置文件
├── requirements.txt       # Python 依赖
└── ...
```

### 2.3 设置执行权限

```bash
# 设置脚本执行权限
chmod +x docker-run.sh
chmod +x docker-build-amd64.sh
chmod +x docker-build-arm64.sh

# 验证权限
ls -la *.sh
```

---

## 3. 构建 Docker 镜像

### 3.1 方式一：使用构建脚本（推荐）

根据系统架构选择对应的构建脚本：

**AMD64 架构（Intel/AMD 处理器）：**

```bash
# 开始构建
./docker-build-amd64.sh

# 等待构建完成（首次构建约需 5-10 分钟）
# 构建成功后显示 "构建成功"
```

**ARM64 架构（树莓派、ARM 开发板）：**

```bash
# 开始构建
./docker-build-arm64.sh

# 等待构建完成（首次构建约需 10-15 分钟）
```

### 3.2 方式二：手动构建

如果构建脚本不可用，可以手动执行 Docker 命令：

**AMD64 构建：**

```bash
docker build \
    --platform linux/amd64 \
    --no-cache \
    -t camera-monitor:amd64 \
    -f Dockerfile \
    .
```

**ARM64 构建：**

```bash
docker build \
    --platform linux/arm64/v8 \
    --no-cache \
    -t camera-monitor:arm64 \
    -f Dockerfile \
    .
```

### 3.3 验证镜像构建

```bash
# 查看已构建的镜像
docker images

# 应该看到类似输出：
# REPOSITORY          TAG       IMAGE ID       CREATED        SIZE
# camera-monitor      amd64     xxxxxxxx       10 seconds ago  256MB
# camera-monitor      arm64     xxxxxxxx       10 seconds ago  256MB
```

---

## 4. 配置与部署

### 4.1 创建数据目录

```bash
# 创建数据持久化目录
mkdir -p ~/camera-monitor/data/screenshots
mkdir -p ~/camera-monitor/data/videos
mkdir -p ~/camera-monitor/data/lowfps
mkdir -p ~/camera-monitor/data/logs

# 设置目录权限
chmod -R 755 ~/camera-monitor/data

# 验证目录创建
ls -la ~/camera-monitor/data/
```

### 4.2 配置 config.json

编辑配置文件，填入您的摄像头信息：

```bash
nano ~/camera-monitor/config.json
```

关键配置项说明：

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
  }
}
```

**RTSP 地址格式说明：**

```
rtsp://用户名:密码@摄像头IP:554/码流地址
```

常见的 TP-LINK 摄像头码流地址：

| 码流 | 地址 | 说明 |
|------|------|------|
| 主码流 | `/stream1` | 1080P 高清 |
| 子码流 | `/stream2` | 720P 标清 |

### 4.3 运行容器

#### 方式一：使用快速启动脚本

```bash
# 确保在项目目录
cd ~/camera-monitor

# 运行启动脚本
./docker-run.sh
```

#### 方式二：手动运行

```bash
# 确保在项目目录
cd ~/camera-monitor

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
    -v /etc/localtime:/etc/localtime:ro \
    -v /etc/timezone:/etc/timezone:ro \
    -e TZ=Asia/Shanghai \
    -e PYTHONUNBUFFERED=1 \
    camera-monitor:amd64   # 或 camera-monitor:arm64
```

### 4.4 参数说明

| 参数 | 说明 |
|------|------|
| `--name camera-monitor` | 容器名称 |
| `--restart unless-stopped` | 除非手动停止，否则自动重启 |
| `--network host` | 使用主机网络（必需，RTSP 需要） |
| `--privileged` | 授予特权模式（访问硬件） |
| `-v config.json:/app/config.json:ro` | 配置文件只读挂载 |
| `-v data/*:/app/data/*` | 数据目录持久化 |
| `-e TZ=Asia/Shanghai` | 设置时区 |

---

## 5. Docker Compose 部署

### 5.1 安装 Docker Compose

如果系统未安装 Docker Compose：

```bash
# 安装 Docker Compose v2
sudo apt install docker-compose-plugin

# 或安装独立版本
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker compose version
```

### 5.2 编辑 docker-compose.yml

Docker Compose 配置已包含两个服务：

| 服务 | 说明 | 端口 |
|------|------|------|
| `camera-monitor` | 主监控服务 | 无（使用 host 网络） |
| `camera-web` | Web 管理界面 | `5000:5000` |

默认配置即可使用，如需修改端口：

```bash
nano ~/camera-monitor/docker-compose.yml
```

修改 Web 服务端口映射：

```yaml
camera-web:
  ports:
    - "8080:5000"  # 改为 8080 端口
```

### 5.3 使用 Docker Compose 部署

```bash
# 确保在项目目录
cd ~/camera-monitor

# 构建并启动所有服务
docker compose up -d

# 或分步执行
docker compose build
docker compose up -d
```

---

## 6. Web 管理界面

### 6.1 访问 Web 界面

部署完成后，打开浏览器访问：

```
http://服务器IP:5000
```

本地访问：

```
http://localhost:5000
```

### 6.2 Web 界面功能

| 功能模块 | 说明 |
|----------|------|
| **仪表盘** | 系统状态、存储信息、今日统计、快捷操作 |
| **配置管理** | 可视化编辑 config.json |
| **日志查看** | 实时查看系统运行日志 |
| **服务管理** | 重启服务、手动合成视频、清理文件 |

### 6.3 仪表盘预览

**仪表盘页面**显示以下信息：

- 系统运行状态（在线/离线）
- 进程信息（PID、内存占用、CPU 使用率）
- 存储使用情况（截图、视频数量和大小）
- 今日统计（截图数量、视频数量）
- 最近日志（实时滚动）

### 6.4 配置管理

在 Web 界面中可以直接修改以下配置：

- 摄像头 RTSP 地址和凭证
- 截图间隔（分时段配置）
- 视频合成参数
- 云端上传设置
- 报警推送配置
- 清理策略

### 6.5 防火墙设置

如果无法访问 Web 界面，需要开放端口：

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 5000/tcp
sudo ufw reload

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# 或直接关闭防火墙（测试环境）
sudo systemctl stop firewalld
sudo systemctl disable firewalld
```

### 6.6 安全建议

生产环境建议：

1. **修改 Web 密钥**：在 `docker-compose.yml` 中修改 `WEB_SECRET_KEY`

```yaml
environment:
  - WEB_SECRET_KEY=your-very-secure-secret-key-here
```

2. **配置反向代理**：使用 Nginx 配置 HTTPS

```nginx
server {
    listen 443 ssl;
    server_name camera.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **配置访问密码**：可使用 Nginx 的 Basic Auth

```bash
# 安装 Apache 工具
sudo apt install apache2-utils

# 创建密码文件
htpasswd -cb /etc/nginx/.htpasswd admin your_password

# Nginx 配置中添加
auth_basic "Restricted Access";
auth_basic_user_file /etc/nginx/.htpasswd;
```

---

## 7. 验证与测试

### 7.1 检查容器状态

```bash
# 查看容器列表
docker ps -a | grep camera

# 应该看到 STATUS 为 "Up" 的运行中容器
```

### 7.2 查看容器日志

```bash
# 实时查看日志
docker logs -f camera-monitor

# 查看最近 100 行日志
docker logs --tail 100 camera-monitor

# 查看错误日志
docker logs camera-monitor 2>&1 | grep -i error
```

### 7.3 进入容器检查

```bash
# 进入容器
docker exec -it camera-monitor bash

# 在容器内检查 Python 环境
python3 --version
python3 -c "import flask; print('Flask:', flask.__version__)"

# 检查 FFmpeg
ffmpeg -version | head -n 1

# 退出容器
exit
```

### 7.4 测试截图功能

```bash
# 在宿主机测试 FFmpeg 截图（需要摄像头在线）
ffmpeg -rtsp_transport tcp -i "rtsp://admin:您的密码@192.168.1.2:554/stream1" \
    -vframes 1 -y ~/test_screenshot.jpg

# 检查截图文件
ls -lh ~/test_screenshot.jpg
```

### 7.5 查看数据生成

```bash
# 查看截图目录
ls -la ~/camera-monitor/data/screenshots/ | tail -10

# 查看视频目录
ls -la ~/camera-monitor/data/videos/ | tail -10

# 查看日志
ls -la ~/camera-monitor/data/logs/
```

---

## 8. 运维管理

### 8.1 日常管理命令

```bash
# 启动容器
docker start camera-monitor

# 停止容器
docker stop camera-monitor

# 重启容器
docker restart camera-monitor

# 查看容器状态
docker ps | grep camera-monitor

# 查看资源使用
docker stats camera-monitor
```

### 8.2 更新系统

```bash
# 进入项目目录
cd ~/camera-monitor

# 拉取最新代码（如果有 Git 仓库）
git pull

# 重新构建镜像
docker build --no-cache -t camera-monitor:amd64 .

# 停止并删除旧容器
docker stop camera-monitor
docker rm camera-monitor

# 启动新容器
docker run -d \
    --name camera-monitor \
    --restart unless-stopped \
    --network host \
    --privileged \
    -v $(pwd)/config.json:/app/config.json:ro \
    -v $(pwd)/data:/app/data \
    -e TZ=Asia/Shanghai \
    camera-monitor:amd64
```

### 8.3 备份数据

```bash
# 创建备份目录
mkdir -p ~/camera-monitor-backup/$(date +%Y%m%d)

# 备份配置文件
cp ~/camera-monitor/config.json ~/camera-monitor-backup/$(date +%Y%m%d)/

# 备份数据
tar -czvf ~/camera-monitor-backup/$(date +%Y%m%d)/camera-data.tar.gz \
    ~/camera-monitor/data/

# 查看备份
ls -lh ~/camera-monitor-backup/
```

### 8.4 恢复数据

```bash
# 停止容器
docker stop camera-monitor

# 解压恢复数据
tar -xzvf ~/camera-monitor-backup/20240328/camera-data.tar.gz -C ~/

# 启动容器
docker start camera-monitor
```

### 8.5 卸载系统

```bash
# 停止并删除容器
docker stop camera-monitor
docker rm camera-monitor

# 删除镜像（可选）
docker rmi camera-monitor:amd64
docker rmi camera-monitor:arm64

# 删除项目目录（谨慎操作，先备份）
rm -rf ~/camera-monitor
```

---

## 9. 常见问题

### Q1：构建镜像失败

**问题描述：** Docker 构建过程中报错。

**解决方案：**

```bash
# 清理 Docker 缓存
docker builder prune -a

# 重新构建
docker build --no-cache -t camera-monitor:amd64 .
```

### Q2：容器无法启动

**问题描述：** `docker start` 报错 "Conflict. The container name is already in use"。

**解决方案：**

```bash
# 删除同名旧容器
docker rm -f camera-monitor

# 重新启动
docker run -d ...
```

### Q3：RTSP 连接失败

**问题描述：** 日志显示 "RTSP connect failed"。

**解决方案：**

1. 确认摄像头 IP 和端口正确
2. 确认用户名密码正确
3. 检查网络连通性：`ping 192.168.1.2`
4. 在容器外测试：`ffmpeg -i "rtsp://..." test.jpg`

### Q4：权限问题

**问题描述：** 无法写入数据目录。

**解决方案：**

```bash
# 修改目录所有者
sudo chown -R 1000:1000 ~/camera-monitor/data/

# 重新启动容器
docker restart camera-monitor
```

### Q5：内存不足

**问题描述：** 容器被 OOM killer 终止。

**解决方案：**

```bash
# 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 或限制容器内存使用
docker run -d \
    --memory=512m \
    --memory-reservation=256m \
    ...
```

### Q6：时区不正确

**问题描述：** 日志时间与实际时间不符。

**解决方案：**

```bash
# 确认宿主机时区
cat /etc/timezone

# 确认 localtime 链接正确
ls -la /etc/localtime

# 在运行时正确挂载
-v /etc/localtime:/etc/localtime:ro \
-v /etc/timezone:/etc/timezone:ro \
-e TZ=Asia/Shanghai \
```

---

## 附录：快速参考命令

```bash
# 一键部署 AMD64（Docker Compose，包含 Web 界面）
cd ~/camera-monitor && \
chmod +x *.sh && \
./docker-build-amd64.sh && \
mkdir -p data/* && \
docker compose up -d

# 一键部署 ARM64（Docker Compose，包含 Web 界面）
cd ~/camera-monitor && \
chmod +x *.sh && \
./docker-build-arm64.sh && \
mkdir -p data/* && \
docker compose up -d

# 查看所有服务状态
docker compose ps

# 查看监控服务日志
docker logs -f camera-monitor

# 查看 Web 界面日志
docker logs -f camera-web

# 重启所有服务
docker compose restart

# 停止所有服务
docker compose down

# 启动所有服务
docker compose up -d

# 访问 Web 管理界面
echo "http://$(hostname -I | awk '{print $1}'):5000"
```

### Web 界面访问

部署完成后，访问以下地址进入 Web 管理界面：

```
http://服务器IP:5000
```

---

**文档版本：** 2.0  
**更新日期：** 2026-03-28  
**适用版本：** Camera Monitor System v1.0+
