@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONPATH=%CD%\site-packages;%PYTHONPATH%
start "" /B pythonw launcher.py
exit
