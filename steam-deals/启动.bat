@echo off
chcp 65001 >nul
title Steam 优惠精选

echo.
echo   🎮 Steam 优惠精选
echo   ━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:: 检查 Python 是否已安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo   ❌ 未找到 Python，请先安装 Python
    echo   📥 下载地址: https://www.python.org/downloads/
    echo   ⚠ 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

:: 运行脚本
python "%~dp0steam-deals.py"

:: 如果脚本异常退出，暂停以便查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo   ⚠ 程序异常退出
    pause
)
