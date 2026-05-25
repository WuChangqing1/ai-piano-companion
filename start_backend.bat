@echo off
title AI Qinban Backend
cd /d "%~dp0backend"
call ".venv\Scripts\activate"
python main.py
pause
