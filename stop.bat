@echo off
chcp 65001 >nul
title 停止视频下载器

echo 正在停止服务...

taskkill /fi "windowtitle eq backend" /f >nul 2>&1
taskkill /fi "windowtitle eq frontend" /f >nul 2>&1
taskkill /im python.exe /f >nul 2>&1
taskkill /im node.exe /f >nul 2>&1

echo 已停止所有服务。
pause
