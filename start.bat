@echo off
setlocal EnableDelayedExpansion
title Pulse AI - Startup

echo.
echo  ==========================================
echo   Pulse AI - One-click startup
echo  ==========================================
echo.

set LF_ACCOUNT_FLOW=23c05a7b-e595-4ffb-b783-56bad5ab65dc
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

echo [1/6] Configuring ngrok auth token...
ngrok config add-authtoken %NGROK_TOKEN% >nul 2>&1

echo [2/6] Checking Langflow Desktop is running on port %LF_PORT%...
echo       If not open yet, launch Langflow Desktop now.
:wait_lf
timeout /t 2 /nobreak >nul
curl -s http://localhost:%LF_PORT%/health >nul 2>&1
if errorlevel 1 (
    echo       Langflow not detected yet - waiting...
    goto wait_lf
)
echo       Langflow is ready.

echo [3/6] Opening ngrok tunnels (Langflow + Streamlit)...
start "ngrok-lf" /min cmd /c "ngrok http %LF_PORT% --log stdout > %TEMP%\ngrok_lf.log 2>&1"

echo       Waiting for Langflow ngrok tunnel...
set NGROK_LF_URL=
:wait_ngrok_lf
timeout /t 2 /nobreak >nul
for /f "delims=" %%i in ('curl -s http://localhost:4040/api/tunnels 2^>nul ^| python -c "import sys,json; d=json.load(sys.stdin); t=[x[\"public_url\"] for x in d.get(\"tunnels\",[]) if x[\"public_url\"].startswith(\"https\")]; print(t[0]) if t else print(\"\")" 2^>nul') do set NGROK_LF_URL=%%i
if "!NGROK_LF_URL!"=="" goto wait_ngrok_lf
echo       Langflow ngrok URL: !NGROK_LF_URL!

echo [4/6] Starting Streamlit on port %ST_PORT%...
start "Streamlit" /min cmd /c "python -m streamlit run app\pulse_app.py --server.port %ST_PORT%"

echo       Waiting for Streamlit to start...
:wait_st
timeout /t 3 /nobreak >nul
curl -s http://localhost:%ST_PORT%/_stcore/health >nul 2>&1
if errorlevel 1 (
    echo       Streamlit not ready yet - waiting...
    goto wait_st
)
echo       Streamlit is ready.

echo [5/6] Opening ngrok tunnel for Streamlit...
start "ngrok-st" /min cmd /c "ngrok http %ST_PORT% --log stdout > %TEMP%\ngrok_st.log 2>&1"

echo       Waiting for Streamlit ngrok tunnel...
set NGROK_ST_URL=
:wait_ngrok_st
timeout /t 2 /nobreak >nul
for /f "delims=" %%i in ('curl -s http://localhost:4040/api/tunnels 2^>nul ^| python -c "import sys,json; d=json.load(sys.stdin); t=[x[\"public_url\"] for x in d.get(\"tunnels\",[]) if x[\"public_url\"].startswith(\"https\") and \":%ST_PORT%\" not in x.get(\"config\",{}).get(\"addr\",\"\")]; print(t[-1]) if t else print(\"\")" 2^>nul') do set NGROK_ST_URL=%%i
if "!NGROK_ST_URL!"=="" goto wait_ngrok_st
echo       Streamlit ngrok URL: !NGROK_ST_URL!

set LF_URL=!NGROK_LF_URL!/api/v1/run/%LF_ACCOUNT_FLOW%
set LF_PORTFOLIO_URL=!NGROK_LF_URL!/api/v1/run/%LF_PORTFOLIO_FLOW%

echo [6/6] Writing URL updater page and starting docs site...
start "DocsServer" /min cmd /c "python -m http.server 5500"

set UPDATER=%TEMP%\pulse_update_urls.html
python -c "open(r'%UPDATER%','w').write('<html><head><meta charset=UTF-8><title>Pulse AI</title></head><body><script>var s=JSON.parse(localStorage.getItem(\"pulseai.langflow.settings.v1\")||\"{}}\");s.url=\"%LF_URL%\";s.portfolioUrl=\"%LF_PORTFOLIO_URL%\";s.key=s.key||\"\" ;s.streamlitUrl=\"%NGROK_ST_URL%\";localStorage.setItem(\"pulseai.langflow.settings.v1\",JSON.stringify(s));setTimeout(function(){window.location.href=\"http://localhost:5500\";},1500);</script><p style=\"font-family:sans-serif;padding:40px\">Updating connection settings, redirecting to Pulse AI...</p></body></html>')"

if not exist "%UPDATER%" (
    echo [ERROR] Failed to write updater page.
    pause & exit /b 1
)

timeout /t 3 /nobreak >nul
start "" "%UPDATER%"

echo.
echo  ==========================================
echo   All services running:
echo   Langflow  : http://localhost:%LF_PORT%
echo   Langflow  : !NGROK_LF_URL! (public)
echo   Streamlit : http://localhost:%ST_PORT%
echo   Streamlit : !NGROK_ST_URL! (public)
echo   Docs      : http://localhost:5500
echo   Run stop.bat to shut everything down.
echo  ==========================================
echo.
pause
