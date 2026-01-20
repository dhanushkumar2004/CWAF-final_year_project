@echo off
title WAF Security Dashboard
color 0A

echo ========================================
echo    WAF Security Dashboard
echo ========================================
echo.
echo Starting services...
echo.

start "Proxy Server" cmd /k "mitmdump -s proxy.py"
timeout /t 3 /nobreak > nul

start "Dashboard Server" cmd /k "cd dashboard && python app.py"
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo Services started!
echo.
echo Proxy:     http://127.0.0.1:8080
echo Dashboard: http://127.0.0.1:5000
echo ========================================
echo.
pause