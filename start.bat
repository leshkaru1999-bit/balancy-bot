@echo off
title Balancy Bot
echo.
echo  ========================================
echo   BALANCY — Запуск
echo  ========================================
echo.
echo  1. Убедись что ngrok запущен в другом окне:
echo     ngrok http 8000
echo.
echo  2. Запускаю бота...
echo.
call venv\Scripts\activate.bat
python -m bot.main
pause
