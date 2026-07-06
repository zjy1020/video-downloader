@echo off
chcp 65001 >nul
title 视频下载器

echo ================================
echo   启动视频下载器...
echo ================================

cd /d "%~dp0"

echo [1/3] 启动后端...
start "backend" cmd /c "cd /d backend && python main.py"
timeout /t 3 /nobreak >nul

echo [2/3] 启动前端...
start "frontend" cmd /c "cd /d frontend && npx vite --host"
timeout /t 4 /nobreak >nul

echo [3/3] 打开浏览器...
start http://127.0.0.1:3000

echo ================================
echo   启动完成！
echo   后端: http://127.0.0.1:8000
echo   前端: http://127.0.0.1:3000
echo   关闭窗口或运行 stop.bat 停止
echo ================================
pause
