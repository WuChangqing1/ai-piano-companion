@echo off
chcp 65001 >nul
title 琴伴 PC 一键演示

echo ========================================
echo         琴伴 - PC 端一键演示
echo ========================================
echo.

:: Check Python backend
echo [1/4] 检查后端服务...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] 后端未启动，正在启动...
    start "AIqinban-Backend" cmd /c "conda activate AIqinban && cd /d %~dp0backend && uvicorn main:app --host 0.0.0.0 --port 8000"
    echo   等待后端就绪...
    timeout /t 5 /nobreak >nul
    curl -s http://localhost:8000/health >nul 2>&1
    if %errorlevel% neq 0 (
        echo   [ERROR] 后端启动失败，请手动启动后再试
        pause
        exit /b 1
    )
)
echo   [OK] 后端服务运行中 (port 8000)

:: Check CosyVoice
echo [2/4] 检查 CosyVoice 服务...
curl -s http://127.0.0.1:9880/ >nul 2>&1
if %errorlevel% neq 0 (
    echo   [WARN] CosyVoice 未启动，TTS 将使用 Edge TTS 兜底
) else (
    echo   [OK] CosyVoice 服务运行中 (port 9880)
)

:: Run pipeline on test3/comody.mp4
echo [3/4] 执行评估流水线 (test3/comody.mp4)...
set "TEST_DIR=%~dp0backend\test_data\test3"
if exist "%TEST_DIR%\comody.mp4" (
    echo   找到测试视频: test3/comody.mp4
    echo   正在评估中，请稍候...
    conda run -n AIqinban python backend/tests/run_full_pipeline.py test3
    if %errorlevel% equ 0 (
        echo   [OK] 评估完成
    ) else (
        echo   [WARN] 评估流程有部分失败，继续...
    )
) else (
    echo   [SKIP] 未找到 test3/comody.mp4，跳过评估
)

:: Open demo page in browser
echo [4/4] 打开演示页面...
echo   浏览器将打开 http://localhost:8000/demo
start "" http://localhost:8000/demo

echo.
echo ========================================
echo   演示已启动!
echo   后端: http://localhost:8000
echo   前端: http://localhost:8000/demo
echo   API文档: http://localhost:8000/docs
echo.
echo   如果后端未自动启动，请手动运行:
echo     conda activate AIqinban
echo     cd backend
echo     uvicorn main:app --host 0.0.0.0 --port 8000
echo ========================================
echo.
pause
