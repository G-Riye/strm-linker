# STRM Linker 测试启动脚本
Write-Host "🚀 启动 STRM Linker 测试环境..." -ForegroundColor Green

# 检查后端是否运行
Write-Host "📋 检查后端服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ 后端服务已运行" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ 后端服务未运行，正在启动..." -ForegroundColor Red
    
    # 启动后端
    Write-Host "🔧 启动后端服务..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; .\venv\Scripts\Activate.ps1; python main.py"
    
    # 等待服务启动
    Write-Host "⏳ 等待服务启动..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# 打开测试页面
Write-Host "🌐 打开测试页面..." -ForegroundColor Yellow
$testPage = "$PWD\frontend\test.html"
if (Test-Path $testPage) {
    Start-Process $testPage
    Write-Host "✅ 测试页面已打开" -ForegroundColor Green
} else {
    Write-Host "❌ 测试页面不存在: $testPage" -ForegroundColor Red
}

Write-Host ""
Write-Host "📖 使用说明:" -ForegroundColor Cyan
Write-Host "1. 后端服务地址: http://localhost:8000" -ForegroundColor Gray
Write-Host "2. API 文档: http://localhost:8000/api/docs" -ForegroundColor Gray
Write-Host "3. 测试页面: $testPage" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 提示: 在测试页面中可以测试所有 API 功能" -ForegroundColor Yellow
