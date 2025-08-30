@echo off
chcp 65001 >nul
REM AlgoKG Web Application Development Environment Startup Script (Windows)

echo Starting AlgoKG Intelligent Q&A Web Application Development Environment...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed or not running
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    pause
    exit /b 1
)

REM Check environment variables file
if not exist .env (
    echo Creating environment variables file...
    copy .env.example .env
    echo Please edit .env file to configure necessary environment variables
)

REM Start basic services
echo Starting database services...
docker-compose up -d neo4j redis

REM Wait for services to start
echo Waiting for database services to start...
timeout /t 15 /nobreak >nul

echo Database services started successfully

REM Start backend service
echo Starting backend service...
cd backend

if not exist venv (
    echo Creating Python virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
pip install -r requirements.txt

echo Starting FastAPI server...
start "AlgoKG Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

cd ..

REM Start frontend service
echo Starting frontend service...
cd frontend

if not exist node_modules (
    echo Installing frontend dependencies...
    npm install
)

echo Starting React development server...
start "AlgoKG Frontend" cmd /k "npm start"

cd ..

echo.
echo AlgoKG Web Application Development Environment Started Successfully!
echo.
echo Frontend URL: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Neo4j Browser: http://localhost:7474
echo.
echo Close command windows or use 'docker-compose stop' to stop services
echo.

pause
