@echo off
title Apex Windows Optimizer
cd /d "%~dp0"

:: Check for administrative rights
net session >nul 2>&1
if %errorlevel% == 0 (
    echo [Apex Optimizer] Running with Administrator privileges...
    python main.py
) else (
    echo [Apex Optimizer] Requesting administrative elevation...
    powershell -NoProfile -Command "Start-Process python -ArgumentList 'main.py' -Verb RunAs"
)
