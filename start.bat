@echo off
setlocal EnableDelayedExpansion
title Pulse AI - Startup

echo.
echo  ==========================================
echo   Pulse AI - One-click startup
echo  ==========================================
echo.

set LF_ACCOUNT_FLOW=c94cf6ad-4f38-4d92-9f6b-d33c50ca5ba5
set LF_PORTFOLIO_FLOW=c94cf6ad-4f38-4d92-9f6b-d33c50ca5ba5
set LF_PORT=7860
set ST_PORT=8501
set NGROK_TOKEN=3GVU6b2fVRoNp05anGr18SFKqbT_2TAAE5i7GUmaz8CngPL8g

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install from https://python.org
    pause & exit /b 1
)

ngrok version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] ngrok not found. Download from https://ngrok.com/download
    pause & exit /b 1
)

echo [1/5] Configuring ngrok auth token...
ngrok config add-authtoken %NGROK_TOKEN% >nul 2>&1

echo [2/5] Checking Langflow Desktop is running on port %LF_PORT%...
echo       If not open yet, launch Langflow Desktop now.
:wait_lf
timeout /t 2 /nobreak >nul
curl -s http://localhost:%LF_PORT%/health >nul 2>&1
if errorlevel 1 (
    echo       Langflow not detected yet - waiting...
    goto wait_lf
)
echo       Langflow is ready.

echo [3/5] Opening ngrok tunnel...
start "ngrok" /min cmd /c "ngrok http %LF_PORT% --log stdout > %TEMP%\ngrok_pulse.log 2>&1"

echo       Waiting for ngrok tunnel...
set NGROK_URL=
:wait_ngrok
timeout /t 2 /nobreak >nul
for /f "delims=" %%i in ('curl -s http://localhost:4040/api/tunnels 2^>nul ^| python -c "import sys,json; d=json.load(sys.stdin); print([t[\"public_url\"] for t in d.get(\"tunnels\",[]) if t[\"public_url\"].startswith(\"https\")][0])" 2^>nul') do set NGROK_URL=%%i
if "!NGROK_URL!"=="" goto wait_ngrok
echo       ngrok URL: !NGROK_URL!

set LF_URL=!NGROK_URL!/api/v1/run/%LF_ACCOUNT_FLOW%
set LF_PORTFOLIO_URL=!NGROK_URL!/api/v1/run/%LF_PORTFOLIO_FLOW%

echo [4/5] Starting Streamlit on port %ST_PORT%...
start "Streamlit" /min cmd /c "python -m streamlit run app\pulse_app.py --server.port %ST_PORT%"

echo [5/5] Writing URL updater page...
set UPDATER=%TEMP%\pulse_update_urls.html
python -c "open(r'%UPDATER%','w').write('<html><head><meta charset=UTF-8><title>Pulse AI</title></head><body><script>var s=JSON.parse(localStorage.getItem(\"pulseai.langflow.settings.v1\")||\"{}}\");s.url=\"%LF_URL%\";s.portfolioUrl=\"%LF_PORTFOLIO_URL%\";localStorage.setItem(\"pulseai.langflow.settings.v1\",JSON.stringify(s));setTimeout(function(){window.location.href=\"http://localhost:5500\";},1500);</script><p style=\"font-family:sans-serif;padding:40px\">Updating connection, redirecting...</p></body></html>')"

if not exist "%UPDATER%" (
    echo [ERROR] Failed to write updater page.
    pause & exit /b 1
)

echo       Starting docs site server on port 5500...
start "DocsServer" /min cmd /c "python -m http.server 5500"

timeout /t 4 /nobreak >nul
start "" "%UPDATER%"

echo.
echo  ==========================================
echo   All services running:
echo   Langflow  : http://localhost:%LF_PORT%
echo   ngrok     : !NGROK_URL!
echo   Streamlit : http://localhost:%ST_PORT%
echo   Docs      : http://localhost:5500
echo   Run stop.bat to shut everything down.
echo  ==========================================
echo.
pause