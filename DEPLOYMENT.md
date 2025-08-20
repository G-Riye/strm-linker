# 🚀 STRM Linker 部署指南

## 📋 GitHub 仓库设置

### 1. 推送代码到 GitHub

```bash
# 1. 在 GitHub 创建新仓库 strm-linker
# 2. 添加远程仓库
git remote add origin https://github.com/your-username/strm-linker.git

# 3. 推送代码
git branch -M main
git push -u origin main
```

### 2. 配置 DockerHub 自动构建

#### 2.1 创建 DockerHub 访问令牌
1. 登录 [DockerHub](https://hub.docker.com/)
2. 点击头像 → **Account Settings** → **Security**
3. 点击 **New Access Token**
4. 输入名称: `github-actions-strm-linker`
5. 权限选择: **Read, Write, Delete**
6. 复制生成的 token（只显示一次）

#### 2.2 在 GitHub 设置 Secrets
1. 进入你的 GitHub 仓库
2. 点击 **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret** 添加以下密钥：

| Name | Value | Description |
|------|-------|-------------|
| `DOCKERHUB_USERNAME` | 你的 DockerHub 用户名 | 用于登录 DockerHub |
| `DOCKERHUB_TOKEN` | 上面创建的访问令牌 | 用于推送镜像 |

#### 2.3 更新配置文件中的用户名

需要在以下文件中将 `yourdockerhubusername` 替换为你的实际 DockerHub 用户名：

1. **README.md**
2. **.github/workflows/docker-publish.yml**
3. **.github/workflows/release.yml**
4. **CHANGELOG.md**

### 3. 触发自动构建

#### 3.1 推送到 main 分支触发构建
```bash
# 修改代码后推送
git add .
git commit -m "update: 配置 DockerHub 用户名"
git push origin main
```

#### 3.2 创建版本标签触发发布
```bash
# 创建并推送版本标签
git tag v1.0.0
git push origin v1.0.0
```

## 🐳 Docker 镜像使用

### 1. 快速启动

```bash
# 使用 docker run
docker run -d \
  --name strm-linker \
  -p 8080:80 \
  -v /path/to/your/media:/media:rw \
  -v ./data:/app/data \
  your-dockerhub-username/strm-linker:latest

# 使用 docker-compose（推荐）
wget https://raw.githubusercontent.com/your-username/strm-linker/main/docker/docker-compose.yml
# 编辑 docker-compose.yml 修改路径
docker-compose up -d
```

### 2. 环境变量

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `APP_HOST` | `0.0.0.0` | 服务绑定地址 |
| `APP_PORT` | `8000` | 后端服务端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `TZ` | - | 时区设置 |
| `PYTHONUNBUFFERED` | `1` | Python 输出缓冲 |

### 3. 目录挂载

| 容器路径 | 描述 | 必需 |
|----------|------|------|
| `/media` | 媒体文件目录 | ✅ |
| `/app/data` | 数据持久化目录 | ✅ |

## 🔧 开发环境设置

### 1. 本地开发

```bash
# 克隆项目
git clone https://github.com/your-username/strm-linker.git
cd strm-linker

# 启动开发模式
./build.sh dev
```

### 2. 本地构建测试

```bash
# 构建镜像
./build.sh build

# 启动服务
./build.sh start

# 查看日志
./build.sh logs

# 停止服务
./build.sh stop
```

## 🔄 CI/CD 工作流

### 自动化流程说明

1. **代码推送** → main 分支
2. **触发构建** → GitHub Actions
3. **多平台构建** → amd64, arm64
4. **镜像推送** → DockerHub
5. **安全扫描** → Trivy（可选）

### 支持的标签

- `latest` - 最新稳定版（main 分支）
- `v1.0.0` - 指定版本号
- `v1.0` - 主要和次要版本
- `v1` - 主要版本

## 📊 镜像信息

- **基础镜像**: `python:3.11-slim`
- **预期大小**: ~150MB
- **支持架构**: `linux/amd64`, `linux/arm64`
- **健康检查**: 内置 HTTP 健康检查
- **安全扫描**: Trivy 漏洞扫描

## 🛠 故障排除

### 常见问题

1. **构建失败**
   - 检查 DockerHub 凭据是否正确
   - 确认仓库权限和访问令牌权限

2. **镜像推送失败**
   - 验证 DOCKERHUB_USERNAME 和 DOCKERHUB_TOKEN
   - 检查网络连接和 DockerHub 状态

3. **健康检查失败**
   - 确认端口映射正确
   - 检查容器内服务启动状态

### 调试命令

```bash
# 查看构建日志
docker logs strm-linker

# 进入容器调试
docker exec -it strm-linker bash

# 检查服务状态
docker exec strm-linker supervisorctl status

# 手动健康检查
curl http://localhost:8080/api/health
```
