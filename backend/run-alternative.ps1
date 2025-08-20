# STRM Linker PowerShell 启动脚本 - 变量重映射方案

param(
    [string]$HostAddress = "0.0.0.0",  # 使用不同的参数名
    [int]$Port = 8000,
    [switch]$Dev
)

# 内部重映射变量（避免与系统$Host冲突）
$AppHost = $HostAddress

# 颜色输出函数
function Write-Success { param([string]$Message) Write-Host "✅ $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message) Write-Host "⚠️  $Message" -ForegroundColor Yellow }
function Write-Error { param([string]$Message) Write-Host "❌ $Message" -ForegroundColor Red }
function Write-Info { param([string]$Message) Write-Host "📍 $Message" -ForegroundColor Cyan }

Write-Host "🚀 启动 STRM Linker 后端服务..." -ForegroundColor Blue

# 获取脚本目录
$BackendDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 检查虚拟环境
if ($env:VIRTUAL_ENV) {
    Write-Success "检测到虚拟环境: $env:VIRTUAL_ENV"
} else {
    Write-Warning "未检测到虚拟环境，建议使用虚拟环境运行"
    Write-Host ""
    Write-Host "创建虚拟环境的步骤:" -ForegroundColor Yellow
    Write-Host "1. python -m venv venv" -ForegroundColor Gray
    Write-Host "2. venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "3. pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host "4. .\run-alternative.ps1" -ForegroundColor Gray
    Write-Host ""
    
    $continue = Read-Host "是否继续运行? (y/N)"
    if ($continue -ne 'y' -and $continue -ne 'Y') {
        exit 0
    }
}

# 检查 Python
try {
    $pythonVersion = python --version 2>$null
    Write-Success "Python 版本: $pythonVersion"
} catch {
    Write-Error "Python 未安装或未在 PATH 中"
    exit 1
}

# 检查依赖文件
if (-not (Test-Path "requirements.txt")) {
    Write-Error "未找到 requirements.txt 文件"
    exit 1
}

# 设置环境变量（使用重映射的变量）
$env:PYTHONPATH = $BackendDir
$env:APP_HOST = $AppHost  # 使用局部变量而非参数直接传入
$env:APP_PORT = $Port

# 开发模式额外设置
if ($Dev) {
    $env:RELOAD = "true"
    Write-Info "开发模式: 启用热重载"
}

# 显示访问信息
Write-Info "访问地址: http://localhost:$Port"
Write-Info "API 文档: http://localhost:$Port/api/docs"
Write-Host ""

# 启动应用
try {
    Push-Location $BackendDir
    python run.py
} catch {
    Write-Error "启动失败: $($_.Exception.Message)"
    exit 1
} finally {
    Pop-Location
}
