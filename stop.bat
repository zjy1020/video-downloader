@echo off
title 停止视频下载器

echo 正在停止服务...
taskkill /im python.exe /f >nul 2>&1
taskkill /im node.exe /f >nul 2>&1
echo 已停止所有服务。
pause
