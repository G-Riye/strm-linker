# 🪟 Windows 运行指南

本文档专门介绍如何在 Windows 系统上运行 STRM Linker。

## 🔧 环境要求

### 必需软件
- **Docker Desktop** 4.0+ （推荐最新版本）
- **PowerShell 5.1+** 或 **PowerShell Core 7.0+**
- **Python 3.11+**（仅开发模式需要）
- **Node.js 18+**（仅开发模式需要）

### 权限要求
- **管理员权限**（推荐）：用于创建符号链接获得最佳性能
- **开发者模式**（可选）：允许非管理员用户创建符号链接

## 🚀 快速开始

### 方法一：PowerShell 脚本（推荐）

1. **以管理员身份**打开 PowerShell
2. 进入项目目录：
   ```powershell
   cd D:\path\to\strm-linker
   ```
3. 设置执行策略（如果需要）：
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```
4. 检查环境：
   ```powershell
   .\build.ps1 admin-check
   ```
5. 构建并启动：
   ```powershell
   .\build.ps1 build
   .\build.ps1 start
   ```

### 方法二：批处理脚本

1. **以管理员身份**打开命令提示符
2. 进入项目目录：
   ```cmd
   cd /d D:\path\to\strm-linker
   ```
3. 检查权限：
   ```cmd
   build.bat admin-check
   ```
4. 构建并启动：
   ```cmd
   build.bat build
   build.bat start
   ```

### 方法三：Docker 命令（直接运行）

```powershell
# 使用 DockerHub 镜像快速启动
docker run -d `
  --name strm-linker `
  -p 8080:80 `
  -v "D:\Media:/media:rw" `
  -v ".\data:/app/data" `
  yourdockerhubusername/strm-linker:latest
```

## 🔑 权限配置

### 方案一：管理员权限（推荐）
以管理员身份运行 PowerShell 或命令提示符，这样可以：
- 创建符号链接（性能最佳）
- 完整访问系统目录
- 无权限限制

### 方案二：开发者模式
1. 打开 **设置** → **更新和安全** → **开发者选项**
2. 启用 **开发者模式**
3. 重启系统
4. 现在非管理员用户也可以创建符号链接

### 方案三：降级处理（自动）
如果没有足够权限创建符号链接，程序会自动：
1. 尝试创建硬链接
2. 如果硬链接失败，则复制文件

## 📁 目录配置示例

### Windows 路径格式
```yaml
# docker-compose.yml 中的挂载配置
volumes:
  # Windows 路径示例
  - "D:\Media\Movies:/media/movies:rw"
  - "E:\TV Shows:/media/tv:rw"
  - ".\data:/app/data"
  
  # 或使用 UNC 路径
  - "\\NAS\Media:/media:rw"
```

### 推荐目录结构
```
D:\Media\
├── Movies\
│   ├── Movie1\
│   │   ├── Movie1.mp4.strm
│   │   └── Movie1.srt
│   └── Movie2\
│       ├── Movie2.mkv.strm
│       └── Movie2.ass
└── TV Shows\
    └── Series1\
        └── Season1\
            ├── S01E01.mp4.strm
            └── S01E01.srt
```

## 🛠 开发环境设置

### 后端开发

#### 方法一：使用启动脚本（推荐）
```powershell
# 进入后端目录
cd backend

# 创建并激活虚拟环境（如果需要）
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 使用 PowerShell 启动脚本
.\run.ps1

# 或使用批处理脚本
run.bat
```

#### 方法二：直接运行
```powershell
# 创建虚拟环境
cd backend
python -m venv venv

# 激活虚拟环境
venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 使用专用启动脚本（解决导入问题）
python run.py
```

### 前端开发
```powershell
# 安装依赖
cd frontend
npm install

# 启动开发服务器
npm run dev
```

### 自动化开发启动
```powershell
# 使用脚本自动启动开发环境
.\build.ps1 dev
```

## 🔍 故障排除

### 常见问题及解决方案

#### 1. PowerShell 执行策略错误
```
无法加载文件，因为在此系统上禁止运行脚本
```
**解决方案**：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### 2. Docker Desktop 未启动
```
error during connect: This error may indicate that the docker daemon is not running
```
**解决方案**：
- 启动 Docker Desktop 应用程序
- 等待 Docker 完全启动（系统托盘图标变为绿色）

#### 3. 权限不足无法创建符号链接
```
权限不足。Windows 下建议以管理员权限运行
```
**解决方案**：
1. **方案一**：以管理员身份重新运行
2. **方案二**：启用开发者模式
3. **方案三**：程序会自动降级为硬链接或文件复制

#### 4. 端口被占用
```
bind: Only one usage of each socket address is normally permitted
```
**解决方案**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8080

# 结束进程（替换 PID）
taskkill /PID <PID> /F

# 或更改端口
docker-compose up -d -p 8081:80
```

#### 5. Python 导入错误
```
ImportError: attempted relative import beyond top-level package
```
**解决方案**：
- 使用提供的启动脚本：`python run.py` 或 `.\run.ps1`
- 确保在正确的目录下运行
- 检查 Python 路径设置

#### 6. 路径中包含中文或特殊字符
**解决方案**：
- 确保路径使用 UTF-8 编码
- 避免使用特殊字符
- 使用双引号包围路径

#### 7. Windows Defender 或杀毒软件阻拦
**解决方案**：
- 将项目目录添加到杀毒软件的白名单
- 临时禁用实时保护进行测试

### 系统兼容性

| Windows 版本 | Docker Desktop | PowerShell | 符号链接 | 状态 |
|-------------|----------------|------------|---------|------|
| Windows 11 | ✅ | ✅ | ✅ | 完全支持 |
| Windows 10 Pro | ✅ | ✅ | ✅ | 完全支持 |
| Windows 10 Home | ✅ | ✅ | ⚠️ | 需要开发者模式 |
| Windows Server 2019+ | ✅ | ✅ | ✅ | 完全支持 |

## 🎯 性能优化建议

### Docker Desktop 设置
1. **内存分配**：建议分配至少 2GB RAM
2. **CPU 核心**：分配至少 2 个 CPU 核心
3. **磁盘空间**：确保至少 10GB 可用空间

### 存储性能
1. **SSD 存储**：使用 SSD 存储提高 I/O 性能
2. **本地存储**：避免使用网络驱动器进行密集操作
3. **符号链接**：优先使用符号链接而非文件复制

### 网络配置
1. **防火墙**：确保端口 8080 未被防火墙阻塞
2. **代理设置**：如果使用代理，确保 Docker 可以访问网络

## 📞 获取帮助

### 命令行帮助
```powershell
# PowerShell 脚本帮助
.\build.ps1 help

# 批处理脚本帮助
build.bat help

# 环境检查
.\build.ps1 admin-check
```

### 日志查看
```powershell
# 查看服务日志
.\build.ps1 logs

# 或直接使用 Docker 命令
docker logs strm-linker -f
```

### 社区支持
- GitHub Issues: [项目地址]/issues
- 文档更新: 查看项目 README.md
- 技术交流: 欢迎提交 Pull Request

---

💡 **小提示**: Windows 用户推荐使用 PowerShell 脚本，它提供了更好的错误处理和用户体验！
