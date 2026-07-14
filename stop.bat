@echo off
title Pulse AI — Shutdown
echo.
echo  Stopping all Pulse AI services...
echo.

:: Kill Streamlit
taskkill /FI "WINDOWTITLE eq Streamlit*" /F >nul 2>&1

:: Kill ngrok
taskkill /FI "WINDOWTITLE eq ngrok*" /F >nul 2>&1
taskkill /IM ngrok.exe /F >nul 2>&1

:: Kill Langflow
taskkill /FI "WINDOWTITLE eq Langflow*" /F >nul 2>&1

:: Kill docs site server
taskkill /FI "WINDOWTITLE eq DocsServer*" /F >nul 2>&1

echo  All services stopped.
echo.
pause
