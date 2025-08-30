# 仅启动后端服务的PowerShell脚本

Write-Host "Starting AlgoKG Backend Service..." -ForegroundColor Green

# 设置环境变量以避免API密钥问题
$env:QWEN_API_KEY = ""
$env:OPENAI_API_KEY = ""

# 导航到后端目录
Set-Location "backend"

# 激活虚拟环境
if (Test-Path "venv\Scripts\Activate.ps1") {
    & "venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found, creating..." -ForegroundColor Yellow
    python -m venv venv
    & "venv\Scripts\Activate.ps1"
    pip install -r requirements.txt
}

# 启动后端服务
Write-Host "Starting FastAPI server..." -ForegroundColor Green
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
