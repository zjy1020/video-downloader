@echo off
title 视频下载器

cd /d "%~dp0"

echo [1/3] 启动后端...
powershell -WindowStyle Hidden -Command "Start-Process python -ArgumentList 'main.py' -WorkingDirectory 'backend'"
timeout /t 3 /nobreak >nul

echo [2/3] 启动前端...
powershell -WindowStyle Hidden -Command "Start-Process npx.cmd -ArgumentList 'vite --host' -WorkingDirectory 'frontend'"
timeout /t 4 /nobreak >nul

echo [3/3] 打开浏览器...
start http://127.0.0.1:3000

echo ================================
echo   启动完成！无多余黑框
echo   关闭本窗口或运行 stop.bat 停止
echo ================================
pause
