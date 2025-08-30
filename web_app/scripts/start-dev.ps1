# AlgoKG Web Application Development Environment Startup Script (PowerShell)

Write-Host "Starting AlgoKG Intelligent Q&A Web Application..." -ForegroundColor Green

# Function to check if command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (-not (Test-Command "docker")) {
    Write-Host "Error: Docker is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Command "node")) {
    Write-Host "Error: Node.js is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Test-Command "python")) {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "All prerequisites found!" -ForegroundColor Green

# Check environment file
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit .env file to configure your settings" -ForegroundColor Yellow
}

# Start database services
Write-Host "Starting database services..." -ForegroundColor Yellow
try {
    docker-compose up -d neo4j redis
    Write-Host "Database services started successfully" -ForegroundColor Green
} catch {
    Write-Host "Failed to start database services: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Wait for services to be ready
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start backend service
Write-Host "Starting backend service..." -ForegroundColor Yellow
Set-Location "backend"

if (-not (Test-Path "venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment and install dependencies
& "venv\Scripts\Activate.ps1"
pip install -r requirements.txt

# Start backend server in new window
Write-Host "Starting FastAPI server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

Set-Location ".."

# Start frontend service
Write-Host "Starting frontend service..." -ForegroundColor Yellow
Set-Location "frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

# Start frontend server in new window
Write-Host "Starting React development server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm start"

Set-Location ".."

# Display success message
Write-Host ""
Write-Host "AlgoKG Web Application Started Successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  Frontend:        http://localhost:3000" -ForegroundColor White
Write-Host "  Backend API:     http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:        http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Neo4j Browser:   http://localhost:7474" -ForegroundColor White
Write-Host ""
Write-Host "To stop services, close the PowerShell windows or run 'docker-compose stop'" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to exit this window"
