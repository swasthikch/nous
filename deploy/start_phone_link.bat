@echo off
title NOUS - Instant Permanent Phone Gateway
color 0B
cd /d "%~dp0\.."

echo ===================================================================
echo   NOUS - Permanent Remote Phone Gateway (Zero Setup / Zero Cost)
echo ===================================================================
echo.
echo Starting secure tunnel to your NOUS assistant on port 8000...
echo.

npx -y localtunnel --port 8000 --subdomain nous-personal-assistant

pause
