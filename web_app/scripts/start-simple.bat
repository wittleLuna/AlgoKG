@echo off
REM Simple startup script for AlgoKG Web Application

echo Starting AlgoKG Web Application...

REM Check if .env exists
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo Please edit .env file with your configuration
)

REM Start database services
echo Starting database services...
docker-compose up -d neo4j redis

REM Wait for services
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Start backend
echo Starting backend...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
start "Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
cd ..

REM Start frontend
echo Starting frontend...
cd frontend
if not exist node_modules (
    npm install
)
start "Frontend" cmd /k "npm start"
cd ..

echo.
echo Services started!
echo Frontend: http://localhost:3000
echo Backend: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Neo4j: http://localhost:7474
echo.

pause
