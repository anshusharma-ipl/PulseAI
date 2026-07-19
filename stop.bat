@echo off
title Pulse AI - Shutdown
echo.
echo  Stopping all Pulse AI services...
echo.

echo  Killing ngrok tunnels...
taskkill /f /im ngrok.exe >nul 2>&1

echo  Killing Streamlit...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8501 " ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1

echo  Killing docs server (port 5500)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":5500 " ^| findstr LISTENING') do taskkill /f /pid %%p >nul 2>&1

echo.
echo  Done. Langflow Desktop must be closed manually.
echo.
pause
