@echo off
chcp 65001 >nul
title CrewAI Flows 全栈项目启动器

echo.
echo ===== CrewAI Flows 全栈项目启动脚本 =====
echo 作者: MRYO-ga
echo.

:: 设置项目路径
set PROJECT_ROOT=D:\app\CrewAIFlowsFullStack
set BACKEND_PATH=%PROJECT_ROOT%\crewaiFlowsBackend
set FRONTEND_PATH=%PROJECT_ROOT%\crewaiFlowsFrontend
set REDIS_PATH=D:\app\Redis-x64-3.0.504
set MYSQL_WORKBENCH_PATH=C:\Program Files\MySQL\MySQL Workbench 8.0\MySQLWorkbench.exe

:: 检查路径是否存在
if not exist "%BACKEND_PATH%" (
    echo 错误: 后端路径不存在: %BACKEND_PATH%
    pause
    exit /b 1
)

if not exist "%FRONTEND_PATH%" (
    echo 错误: 前端路径不存在: %FRONTEND_PATH%
    pause
    exit /b 1
)

if not exist "%REDIS_PATH%" (
    echo 错误: Redis路径不存在: %REDIS_PATH%
    pause
    exit /b 1
)

if not exist "%MYSQL_WORKBENCH_PATH%" (
    echo 错误: MySQL Workbench路径不存在: %MYSQL_WORKBENCH_PATH%
    pause
    exit /b 1
)

echo 正在启动所有服务...
echo.

:: 1. 启动 Redis Server
echo [1/5] 启动 Redis Server...
start "Redis Server" "%REDIS_PATH%\redis-server.exe"
timeout /t 3 /nobreak >nul

:: 2. 启动 MySQL Workbench
echo [2/5] 启动 MySQL Workbench...
start "MySQL Workbench" "%MYSQL_WORKBENCH_PATH%"
echo MySQL Workbench 启动成功，请手动连接到您的数据库
timeout /t 3 /nobreak >nul

:: 3. 启动后端 API
echo [3/5] 启动后端 API (Port 9000)...
start "后端 API" cmd /k "cd /d %BACKEND_PATH% && conda activate crewai310 && uvicorn main:app --host 0.0.0.0 --port 9000 --reload"
timeout /t 3 /nobreak >nul

:: 4. 启动 Celery Worker
echo [4/5] 启动 Celery Worker...
start "Celery Worker" cmd /k "cd /d %BACKEND_PATH% && conda activate crewai310 && celery -A tasks worker -l info -P eventlet"
timeout /t 3 /nobreak >nul

:: 5. 启动前端应用
echo [5/5] 启动前端应用 (Port 3000)...
start "前端应用" cmd /k "cd /d %FRONTEND_PATH% && npm start"

echo.
echo ===== 所有服务启动完成 =====
echo.
echo 服务访问地址:
echo   前端应用: http://localhost:3000
echo   后端API:  http://localhost:9000
echo   API文档:  http://localhost:9000/docs
echo.
echo 注意事项:
echo   - 每个服务都在独立的命令行窗口中运行
echo   - MySQL Workbench 已启动，请手动连接数据库
echo   - 关闭对应窗口即可停止相应服务
echo   - 如果某个服务启动失败，请检查对应的窗口输出
echo.
echo 按任意键退出...
pause >nul 