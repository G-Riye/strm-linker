# STRM Linker PowerShell 构建和部署脚本
param(
    [Parameter(Position=0)]
    [ValidateSet("build", "start", "stop", "restart", "logs", "clean", "dev", "test", "admin-check", "help")]
    [string]$Action = "build"
)

# 颜色输出函数
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$ForegroundColor = "White"
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
}

function Write-Success { param([string]$Message) Write-ColorOutput "✅ $Message" "Green" }
function Write-Warning { param([string]$Message) Write-ColorOutput "⚠️  $Message" "Yellow" }
function Write-Error { param([string]$Message) Write-ColorOutput "❌ $Message" "Red" }
function Write-Info { param([string]$Message) Write-ColorOutput "📍 $Message" "Cyan" }
function Write-Title { param([string]$Message) Write-ColorOutput "🚀 $Message" "Blue" }

Write-Title "STRM Linker PowerShell 构建脚本"

# 检查 Docker 和 Docker Compose
function Test-DockerInstallation {
    try {
        $null = docker --version
        if ($LASTEXITCODE -ne 0) { throw "Docker 命令执行失败" }
    }
    catch {
        Write-Error "Docker 未安装或未启动，请先安装 Docker Desktop"
        exit 1
    }

    try {
        $null = docker-compose --version
        if ($LASTEXITCODE -ne 0) { throw "Docker Compose 命令执行失败" }
    }
    catch {
        Write-Error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    }
}

# 检查管理员权限
function Test-AdminRights {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# 获取脚本目录
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DockerDir = Join-Path $ScriptDir "docker"

switch ($Action) {
    "build" {
        Write-Warning "🔨 构建 Docker 镜像..."
        Test-DockerInstallation
        
        Push-Location $DockerDir
        try {
            docker-compose build
            if ($LASTEXITCODE -eq 0) {
                Write-Success "镜像构建完成"
            } else {
                Write-Error "镜像构建失败"
                exit 1
            }
        }
        finally {
            Pop-Location
        }
    }
    
    "start" {
        Write-Warning "🚀 启动服务..."
        Test-DockerInstallation
        
        Push-Location $DockerDir
        try {
            docker-compose up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Success "服务启动成功"
                Write-Info "访问地址: http://localhost:8080"
            } else {
                Write-Error "服务启动失败"
                exit 1
            }
        }
        finally {
            Pop-Location
        }
    }
    
    "stop" {
        Write-Warning "⏹️ 停止服务..."
        Test-DockerInstallation
        
        Push-Location $DockerDir
        try {
            docker-compose down
            if ($LASTEXITCODE -eq 0) {
                Write-Success "服务已停止"
            }
        }
        finally {
            Pop-Location
        }
    }
    
    "restart" {
        Write-Warning "🔄 重启服务..."
        Test-DockerInstallation
        
        Push-Location $DockerDir
        try {
            docker-compose down
            docker-compose up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Success "服务重启成功"
                Write-Info "访问地址: http://localhost:8080"
            }
        }
        finally {
            Pop-Location
        }
    }
    
    "logs" {
        Write-Warning "📋 查看服务日志..."
        Test-DockerInstallation
        
        Push-Location $DockerDir
        try {
            docker-compose logs -f
        }
        finally {
            Pop-Location
        }
    }
    
    "clean" {
        Write-Warning "🧹 清理 Docker 资源..."
        Test-DockerInstallation
        
        Push-Location $DockerDir
        try {
            docker-compose down -v --remove-orphans
            docker system prune -f
            Write-Success "清理完成"
        }
        finally {
            Pop-Location
        }
    }
    
    "dev" {
        Write-Warning "🛠️ 开发模式启动..."
        
        Write-Host ""
        Write-Host "后端服务启动步骤:" -ForegroundColor Yellow
        Write-Host "1. cd backend" -ForegroundColor Gray
        Write-Host "2. python -m venv venv" -ForegroundColor Gray
        Write-Host "3. venv\Scripts\Activate.ps1" -ForegroundColor Gray
        Write-Host "4. pip install -r requirements.txt" -ForegroundColor Gray
        Write-Host "5. python main.py" -ForegroundColor Gray
        
        Write-Host ""
        Write-Host "前端服务启动步骤:" -ForegroundColor Yellow
        Write-Host "1. cd frontend" -ForegroundColor Gray
        Write-Host "2. npm install" -ForegroundColor Gray
        Write-Host "3. npm run dev" -ForegroundColor Gray
        
        Write-Host ""
        Write-Info "前端地址: http://localhost:3000"
        Write-Info "后端地址: http://localhost:8000"
        
        $response = Read-Host "`n是否自动启动开发环境? (y/N)"
        if ($response -eq 'y' -or $response -eq 'Y') {
            Write-Warning "启动后端服务..."
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptDir\backend'; python -m venv venv; venv\Scripts\Activate.ps1; pip install -r requirements.txt; python main.py"
            
            Start-Sleep -Seconds 3
            
            Write-Warning "启动前端服务..."
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ScriptDir\frontend'; npm install; npm run dev"
        }
    }
    
    "test" {
        Write-Warning "🧪 运行测试..."
        
        # 测试后端
        $backendPath = Join-Path $ScriptDir "backend"
        if (Test-Path (Join-Path $backendPath "requirements.txt")) {
            Push-Location $backendPath
            try {
                python -c "from main import app; print('✅ 后端应用检查通过')" 2>$null
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "后端应用检查失败"
                    Pop-Location
                    exit 1
                }
            }
            finally {
                Pop-Location
            }
        }
        
        # 测试前端构建
        $frontendPath = Join-Path $ScriptDir "frontend"
        if (Test-Path (Join-Path $frontendPath "package.json")) {
            Push-Location $frontendPath
            try {
                if (-not (Test-Path "node_modules")) {
                    Write-Warning "正在安装前端依赖..."
                    npm install
                }
                
                npm run build
                if (Test-Path "dist\index.html") {
                    Write-Success "前端构建测试通过"
                } else {
                    Write-Error "前端构建测试失败"
                    Pop-Location
                    exit 1
                }
            }
            finally {
                Pop-Location
            }
        }
        
        Write-Success "所有测试通过"
    }
    
    "admin-check" {
        Write-Warning "🔍 检查系统环境..."
        
        # 检查管理员权限
        if (Test-AdminRights) {
            Write-Success "当前以管理员身份运行"
            Write-Info "可以创建符号链接以获得最佳性能"
        } else {
            Write-Warning "当前非管理员身份运行"
            Write-Warning "建议以管理员身份重新运行以创建符号链接"
            Write-Info "或启用 Windows 开发者模式允许非管理员创建符号链接"
        }
        
        # 检查开发者模式
        try {
            $devMode = Get-ItemPropertyValue -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Name "AllowDevelopmentWithoutDevLicense" -ErrorAction SilentlyContinue
            if ($devMode -eq 1) {
                Write-Success "Windows 开发者模式已启用"
                Write-Info "非管理员用户可以创建符号链接"
            } else {
                Write-Warning "Windows 开发者模式未启用"
                Write-Info "建议启用开发者模式或以管理员身份运行"
            }
        }
        catch {
            Write-Warning "无法检查开发者模式状态"
        }
        
        # 检查 Docker
        Write-Host ""
        Write-Warning "检查 Docker 状态..."
        try {
            Test-DockerInstallation
            Write-Success "Docker 和 Docker Compose 已正确安装"
            
            # 检查 Docker 运行状态
            $dockerInfo = docker info 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Docker 服务运行正常"
            } else {
                Write-Warning "Docker 服务可能未启动"
            }
        }
        catch {
            Write-Error "Docker 环境检查失败"
        }
        
        # 显示系统信息
        Write-Host ""
        Write-Info "系统信息:"
        Write-Host "  PowerShell 版本: $($PSVersionTable.PSVersion)" -ForegroundColor Gray
        Write-Host "  操作系统: $(Get-ComputerInfo -Property WindowsProductName | Select-Object -ExpandProperty WindowsProductName)" -ForegroundColor Gray
        Write-Host "  Python 版本: $(python --version 2>$null)" -ForegroundColor Gray
        Write-Host "  Node.js 版本: $(node --version 2>$null)" -ForegroundColor Gray
    }
    
    "help" {
        Write-Title "📖 PowerShell 使用说明:"
        Write-Host ""
        Write-Host "  .\build.ps1 [命令]" -ForegroundColor White
        Write-Host ""
        Write-Host "可用命令:" -ForegroundColor Yellow
        Write-Host "  build       - 构建 Docker 镜像" -ForegroundColor Gray
        Write-Host "  start       - 启动服务" -ForegroundColor Gray
        Write-Host "  stop        - 停止服务" -ForegroundColor Gray
        Write-Host "  restart     - 重启服务" -ForegroundColor Gray
        Write-Host "  logs        - 查看日志" -ForegroundColor Gray
        Write-Host "  clean       - 清理 Docker 资源" -ForegroundColor Gray
        Write-Host "  dev         - 开发模式启动" -ForegroundColor Gray
        Write-Host "  test        - 运行测试" -ForegroundColor Gray
        Write-Host "  admin-check - 检查系统环境和权限" -ForegroundColor Gray
        Write-Host "  help        - 显示此帮助信息" -ForegroundColor Gray
        Write-Host ""
        Write-Warning "💡 Windows 特别说明:"
        Write-Host "  - 建议以管理员权限运行 PowerShell 以获得最佳性能" -ForegroundColor Gray
        Write-Host "  - 或启用开发者模式允许创建符号链接" -ForegroundColor Gray
        Write-Host "  - 确保已安装并启动 Docker Desktop" -ForegroundColor Gray
        Write-Host "  - 如遇到执行策略问题，请运行: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Gray
        Write-Host ""
        Write-Warning "示例:"
        Write-Host "  .\build.ps1 build" -ForegroundColor Gray
        Write-Host "  .\build.ps1 start" -ForegroundColor Gray
        Write-Host "  .\build.ps1 admin-check" -ForegroundColor Gray
    }
}
