@echo off
title Apex Windows Optimizer - Standalone Executable Builder
cd /d "%~dp0"

echo ========================================================================
echo       APEX WINDOWS OPTIMIZER PRO - STANDALONE EXE COMPILER
echo                   Created by Rajkumar Patil
echo ========================================================================
echo.

python build_exe.py

echo.
echo Press any key to exit...
pause >nul
