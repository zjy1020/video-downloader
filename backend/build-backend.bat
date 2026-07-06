@echo off
chcp 65001 >nul
echo 正在打包后端为 exe...

pyinstaller ^
  --onefile ^
  --name python-backend ^
  --distpath ..\frontend\src-tauri\binaries ^
  --hidden-import uvicorn ^
  --hidden-import uvicorn.logging ^
  --hidden-import uvicorn.loops ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols ^
  --hidden-import uvicorn.protocols.http ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websocket ^
  --hidden-import uvicorn.protocols.websocket.auto ^
  main.py

move /Y ..\frontend\src-tauri\binaries\python-backend.exe ..\frontend\src-tauri\binaries\python-backend-x86_64-pc-windows-msvc.exe >nul 2>&1

echo 打包完成！
echo 输出: frontend\src-tauri\binaries\python-backend-x86_64-pc-windows-msvc.exe
pause
