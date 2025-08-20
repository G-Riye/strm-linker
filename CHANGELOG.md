# 更新日志

## [v1.0.0] - 2024-08-20

### ✨ 新功能
- 🔍 智能扫描 `.strm` 文件并自动解析视频格式
- 🔗 批量创建多种格式的软链接（MP4、MKV、AVI 等）
- 👀 实时文件监听，新文件自动处理
- ⏰ 灵活的定时任务配置（支持 Cron 表达式）
- 🌐 现代化 Web 管理界面（Vue 3 + Element Plus）
- 📱 响应式设计，完美支持 PC 和移动端
- 📝 完整的日志管理和查看功能
- 🐳 Docker 容器化部署，一键启动
- 🔍 增强的目录选择器，支持路径自动补全
- 📊 实时系统状态监控

### 🛠 技术特性
- **后端**: FastAPI + Python 3.11
- **前端**: Vue 3 + Element Plus + Vite
- **部署**: Docker 多阶段构建
- **服务**: Nginx + Supervisor 进程管理
- **监听**: Watchdog 文件系统监听
- **调度**: APScheduler 定时任务

### 📦 Docker 镜像
```bash
docker pull yourdockerhubusername/strm-linker:v1.0.0
docker pull yourdockerhubusername/strm-linker:latest
```

### 🚀 快速开始
```bash
docker run -d \
  --name strm-linker \
  -p 8080:80 \
  -v /path/to/your/media:/media:rw \
  -v ./data:/app/data \
  yourdockerhubusername/strm-linker:latest
```

### 🎯 使用场景
- Emby/Jellyfin 媒体服务器字幕管理
- `.strm` 文件与字幕文件的自动关联
- 大批量媒体文件的软链接管理
- 定时自动化的文件处理任务

### ⚡ 性能优化
- 多线程并发处理文件
- Docker 镜像大小优化（约 150MB）
- 前端资源压缩和缓存优化
- 数据库查询和日志管理优化
