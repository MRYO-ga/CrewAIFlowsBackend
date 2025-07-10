@echo off
title CrewAI Flows Starter

echo Starting services...

rem Set paths
set BACKEND_PATH=D:\app\CrewAIFlowsFullStack\crewaiFlowsBackend
set FRONTEND_PATH=D:\app\CrewAIFlowsFullStack\crewaiFlowsFrontend

rem Start frontend app in a new window
echo Starting frontend app (Port 3000)...
start "Frontend App" cmd /k "cd /d "%FRONTEND_PATH%" && npm start"

rem Wait 2 seconds
ping 127.0.0.1 -n 3 > nul

echo.
echo Frontend started at: http://localhost:3000
echo.
echo Starting backend API (Port 9000) in current window...
echo Backend API will be available at: http://localhost:9000
echo API Docs will be available at: http://localhost:9000/docs
echo.
echo Press Ctrl+C to stop the backend server
echo.

rem Start backend API in the current window
cd /d "%BACKEND_PATH%" && conda activate crewai310 && uvicorn main:app --host 0.0.0.0 --port 9000 