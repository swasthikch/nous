@echo off
title NOUS - Cloudflare Tunnel Gateway
color 0B
cd /d "%~dp0\..\.."

echo ===================================================================
echo   NOUS - Cloudflare Tunnel 24/7 Remote Phone Gateway
echo ===================================================================
echo.
echo Connecting your local NOUS assistant to Cloudflare's global edge network...
echo No public IP or port forwarding required. 100%% Free & Encrypted.
echo.

:: Check if cloudflared is installed in PATH
where cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Detected cloudflared in system PATH.
    set "CLOUDFLARED_BIN=cloudflared"
    goto :RUN_TUNNEL
)

:: Check if cloudflared.exe exists locally in bin
if exist "bin\cloudflared.exe" (
    echo [OK] Detected local bin\cloudflared.exe.
    set "CLOUDFLARED_BIN=bin\cloudflared.exe"
    goto :RUN_TUNNEL
)

:: Prompt installation via winget or direct download
echo [1/2] cloudflared is not installed yet.
echo Attempting to install via winget (recommended)...
winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements >nul 2>&1

where cloudflared >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Successfully installed cloudflared!
    set "CLOUDFLARED_BIN=cloudflared"
    goto :RUN_TUNNEL
)

echo [WARNING] Winget install failed. Downloading standalone cloudflared.exe...
mkdir bin >nul 2>&1
powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'bin\cloudflared.exe'"

if exist "bin\cloudflared.exe" (
    echo  [OK] Downloaded cloudflared.exe to bin\cloudflared.exe.
    set "CLOUDFLARED_BIN=bin\cloudflared.exe"
    goto :RUN_TUNNEL
)

echo [ERROR] Could not download cloudflared. Please install it manually from:
echo https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
pause
exit /b 1

:RUN_TUNNEL
echo.
echo ===================================================================
echo [2/2] Starting Cloudflare Tunnel to http://127.0.0.1:8000 ...
echo ===================================================================
echo Look for the line ending in: https://xxxx.trycloudflare.com
echo Copy that HTTPS URL into your phone's browser!
echo.

%CLOUDFLARED_BIN% tunnel --url http://127.0.0.1:8000

pause
