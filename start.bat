@echo off
chcp 65001 >nul
title 视频下载工具

cd /d "%~dp0"

echo ================================
echo   Step 1/4: 安装 Python 依赖
echo ================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python！
    echo 请先安装 Python 3.8+（装的时候记得勾选"Add Python to PATH"）
    echo 下载: https://www.python.org/downloads/
    pause
    exit /b 1
)

python -m pip install -r backend/requirements.txt
if %errorlevel% neq 0 (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ================================
echo   Step 2/4: 安装前端依赖
echo ================================
cd frontend
if not exist "node_modules" (
    npm install
    if %errorlevel% neq 0 (
        echo [错误] npm install 失败
        pause
        exit /b 1
    )
) else (
    echo node_modules 已存在，跳过
)
cd ..

echo.
echo ================================
echo   Step 3/4: 启动后端 (端口 8000)
echo ================================
start "后端" cmd /c "cd /d "%~dp0backend" && python main.py"

echo.
echo ================================
echo   Step 4/4: 启动前端 (端口 3000)
echo ================================
start "前端" cmd /c "cd /d "%~dp0frontend" && npx vite --host"

timeout /t 3 /nobreak >nul

echo.
echo ================================
echo   启动完成，浏览器打开：
echo   http://127.0.0.1:3000
echo ================================
echo.
echo 关闭本窗口不会停止服务，请用 stop.bat 停止。
pause