@echo off
rem 《Football Life：我的足球生涯》双击启动脚本
chcp 65001 >nul
cd /d "%~dp0"

set "PY_DIR=C:\Users\liyumo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python"
set "PYTHON=%PY_DIR%\python.exe"
set "PYTHONW=%PY_DIR%\pythonw.exe"

if not exist "%PYTHON%" (
    echo [错误] 未找到 Codex 捆绑 Python：
    echo %PYTHON%
    echo 请检查 Codex 运行时是否安装完整。
    pause
    exit /b 1
)

rem 优先使用 pythonw.exe（无控制台窗口）；不存在则退回 python.exe
if exist "%PYTHONW%" (
    start "" "%PYTHONW%" main.py
) else (
    start "" "%PYTHON%" main.py
)
