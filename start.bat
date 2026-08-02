@echo off
rem Football Life launcher - double-click to play.
cd /d "%~dp0"

set "PY_DIR=C:\Users\liyumo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python"
set "PYTHON=%PY_DIR%\python.exe"
set "PYTHONW=%PY_DIR%\pythonw.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Codex bundled Python not found:
    echo %PYTHON%
    echo Please check your Codex runtime installation.
    pause
    exit /b 1
)

rem Prefer pythonw.exe (no console window); fall back to python.exe.
if exist "%PYTHONW%" (
    start "" "%PYTHONW%" main.py
) else (
    start "" "%PYTHON%" main.py
)
