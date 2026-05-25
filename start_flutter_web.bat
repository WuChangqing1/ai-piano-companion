@echo off
title AI Qinban Flutter Web
cd /d "%~dp0frontend_app\build\web"
python -m http.server 5000
pause
