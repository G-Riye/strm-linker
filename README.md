# 🔗 STRM Linker

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/docker/pulls/yourdockerhubusername/strm-linker.svg)](https://hub.docker.com/r/yourdockerhubusername/strm-linker)
[![Docker Image Size](https://img.shields.io/docker/image-size/yourdockerhubusername/strm-linker/latest.svg)](https://hub.docker.com/r/yourdockerhubusername/strm-linker)
[![Build Status](https://github.com/your-username/strm-linker/workflows/Docker%20Build%20and%20Push/badge.svg)](https://github.com/your-username/strm-linker/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.0+-green.svg)](https://vuejs.org)

专为 **Emby/Jellyfin** 设计的字幕软链管理工具，自动为 `.strm` 文件创建对应视频格式的软链接，完美解决字幕识别问题。

## ✨ 核心功能

- 🔍 **智能扫描**: 自动识别 `.strm` 文件并解析视频格式
- 🔗 **软链创建**: 批量创建多种格式的软链接
- 👀 **实时监听**: 监控目录变化，新文件自动处理
- ⏰ **定时任务**: 灵活的定时扫描配置
- 📊 **Web 界面**: 直观的管理界面，支持 PC 和移动端
- 📝 **日志管理**: 完整的操作日志记录和查看

## 🛠 技术栈

### 后端
- **FastAPI** - 现代化的 Python Web 框架
- **Watchdog** - 文件系统监听
- **APScheduler** - 定时任务调度
- **Pathlib** - 文件路径操作

### 前端  
- **Vue 3** - 渐进式 JavaScript 框架
- **Element Plus** - Vue 3 组件库
- **Vite** - 构建工具

### 部署
- **Docker** - 容器化部署
- **Nginx** - 反向代理和静态文件服务
- **Supervisor** - 进程管理

## 🚀 快速开始

### Docker 部署（推荐）

#### 方法一：使用 DockerHub 镜像（最简单）

```bash
# 1. 创建 docker-compose.yml
wget https://raw.githubusercontent.com/your-username/strm-linker/main/docker/docker-compose.yml

# 2. 修改媒体目录路径（编辑 docker-compose.yml）
# 将 /path/to/your/media:/media:rw 改为你的实际路径

# 3. 启动服务
docker-compose up -d

# 4. 访问 Web 界面
# http://localhost:8080
```

#### 方法二：克隆项目本地构建

1. **克隆项目**
```bash
git clone https://github.com/your-username/strm-linker.git
cd strm-linker
```

2. **修改配置**
编辑 `docker/docker-compose.yml`，调整媒体目录挂载路径：
```yaml
volumes:
  # 将你的媒体目录挂载到容器中
  - /path/to/your/media:/media:rw
```

3. **启动服务**
```bash
cd docker
docker-compose up -d
```

4. **访问界面**
打开浏览器访问：http://localhost:8080

### 🐳 DockerHub 镜像

```bash
# 直接运行（快速体验）
docker run -d \
  --name strm-linker \
  -p 8080:80 \
  -v /path/to/your/media:/media:rw \
  -v ./data:/app/data \
  yourdockerhubusername/strm-linker:latest

# 支持的标签
# latest    - 最新稳定版
# v1.0.0    - 指定版本
```

### 本地开发

#### Linux/macOS
```bash
cd backend
pip install -r requirements.txt
python main.py

# 前端（新终端）
cd frontend
npm install
npm run dev
```

#### Windows
```powershell
# PowerShell 脚本（推荐）
.\build.ps1 dev

# 或手动启动
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

📖 **Windows 用户**：详细说明请查看 [WINDOWS.md](WINDOWS.md)

## 📖 使用指南

### 基本使用流程

1. **配置扫描目录**: 在扫描管理页面选择包含 `.strm` 文件的目录
2. **选择目标格式**: 勾选要创建软链接的视频格式（建议 MP4 和 MKV）
3. **执行扫描**: 点击"开始扫描"按钮，系统会自动处理所有 `.strm` 文件
4. **查看结果**: 扫描完成后可查看处理结果和统计信息

### 文件监听设置

1. 进入**设置页面**，启用"文件监听服务"
2. 添加要监听的目录
3. 新增的 `.strm` 文件会被自动处理

### 定时任务配置

1. 在**定时任务页面**添加新任务
2. 设置执行时间（支持 Cron 表达式）
3. 配置扫描目录和目标格式
4. 任务会按计划自动执行

## 🔧 配置说明

### Docker 环境变量

```yaml
environment:
  - APP_HOST=0.0.0.0          # 应用绑定地址
  - APP_PORT=8000             # 应用端口
  - LOG_LEVEL=INFO            # 日志级别
  - TZ=Asia/Shanghai          # 时区设置
```

### 目录挂载

```yaml
volumes:
  - ./data:/app/data          # 数据目录（日志、配置）
  - /your/media:/media:rw     # 媒体目录（需要写权限）
```

## 📁 项目结构

```
strm-linker/
├── backend/                 # Python 后端
│   ├── main.py             # FastAPI 入口
│   ├── api/                # API 接口
│   │   ├── config.py       # 配置管理
│   │   ├── logs.py         # 日志接口  
│   │   └── browse.py       # 目录浏览
│   └── services/           # 核心服务
│       ├── scanner.py      # 扫描逻辑
│       ├── watcher.py      # 文件监听
│       ├── scheduler.py    # 定时任务
│       └── logger.py       # 日志管理
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── api/           # API 调用
│   │   └── router/        # 路由配置
│   └── dist/              # 构建产物
└── docker/                # Docker 配置
    ├── Dockerfile         # 镜像构建
    ├── docker-compose.yml # 容器编排
    ├── nginx.conf         # Nginx 配置
    └── supervisord.conf   # 进程管理
```

## 🐛 常见问题

### Windows 软链接权限问题
Windows 下创建软链接需要特殊权限，解决方案：
1. **管理员权限**：以管理员身份运行（推荐）
2. **开发者模式**：启用 Windows 开发者模式
3. **自动降级**：程序会自动使用硬链接或文件复制
4. 详细配置请参考：[WINDOWS.md](WINDOWS.md)

### 字幕仍无法识别
1. 检查字幕文件名是否与视频文件匹配
2. 确认软链接创建成功
3. 重启 Emby/Jellyfin 服务
4. 刷新媒体库

### 监听服务不工作  
1. 检查目录权限
2. 确认目录路径正确
3. 查看日志错误信息

## 📊 系统要求

### 最低配置
- **CPU**: 1 核心
- **内存**: 512MB RAM  
- **存储**: 100MB 可用空间
- **操作系统**: Windows 10+, Linux, macOS

### 推荐配置
- **CPU**: 2+ 核心
- **内存**: 1GB+ RAM
- **存储**: SSD 存储
- **Windows**: 启用开发者模式或管理员权限

### Windows 特别说明
- 支持 Windows 10/11 和 Windows Server 2019+
- PowerShell 5.1+ 或 PowerShell Core 7.0+
- 推荐以管理员权限运行获得最佳性能
- 详细指南：[WINDOWS.md](WINDOWS.md)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)  
5. 创建 Pull Request

## 📝 更新日志

### v1.0.0
- ✅ 基础扫描功能
- ✅ 实时文件监听  
- ✅ 定时任务调度
- ✅ Web 管理界面
- ✅ Docker 容器化部署
- ✅ 日志管理和查看

## 📜 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 优秀的 Python Web 框架
- [Vue.js](https://vuejs.org/) - 渐进式 JavaScript 框架  
- [Element Plus](https://element-plus.org/) - Vue 3 组件库
- [Emby](https://emby.media/) & [Jellyfin](https://jellyfin.org/) - 优秀的媒体服务器

---

如有问题或建议，欢迎提交 Issue 或联系开发者！ 🚀
