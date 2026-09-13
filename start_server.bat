@echo off
title SmartCart AI Server (Do Not Close)
cd /d C:\Users\hp\Desktop\smartcart-agent
echo ========================================================
echo        SmartCart AI Server - Running on Port 3000
echo ========================================================
:loop
py -3.12 server.py
echo [SmartCart] Server exited. Restarting in 2 seconds...
timeout /t 2 /nobreak >nul
goto loop
