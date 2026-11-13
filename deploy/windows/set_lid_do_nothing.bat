@echo off
title Configure Laptop to Run With Lid Closed (24/7 Mode)
color 0B

echo ===================================================================
echo   NOUS - Configure Laptop to Run With Lid Closed (24/7 Mode)
echo ===================================================================
echo.
echo This script sets Windows power options so closing the laptop lid
echo DOES NOT put the laptop to sleep when plugged in.
echo (The screen will turn off, but NOUS and Wi-Fi will stay running 24/7).
echo.

:: Check for Administrative Privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [NOTE] Requesting Administrator permissions...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [1/3] Setting 'When I close the lid (Plugged in)' to 'Do nothing'...
powercfg /setacvalueindex SCHEME_CURRENT 4f971e89-eebd-4455-a8de-9e59040e7347 5ca83367-6e45-459f-a27b-476b1d01c936 0

echo [2/3] Setting 'Sleep after (Plugged in)' to 'Never'...
powercfg /change standby-timeout-ac 0

echo [3/3] Applying changes to active power scheme...
powercfg /setactive SCHEME_CURRENT

echo.
echo ===================================================================
echo  [SUCCESS] Laptop is now configured for 24/7 closed-lid operation!
echo ===================================================================
echo  - When plugged into power, you can close the lid at any time.
echo  - The laptop will stay awake, Wi-Fi will stay active, and NOUS
echo    will continue running minute-to-minute for your phone!
echo.
pause
