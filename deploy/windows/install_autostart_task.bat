@echo off
title Install NOUS 24/7 Autostart Background Task
color 0B
cd /d "%~dp0\..\.."

set "PROJECT_ROOT=%CD%"
set "TASK_NAME=NOUS_Assistant_247"
set "LAUNCH_SCRIPT=%PROJECT_ROOT%\run_nous.bat"

echo ===================================================================
echo   NOUS - Install 24/7 Autostart Background Task
echo ===================================================================
echo.
echo This registers a Windows Scheduled Task so NOUS starts automatically
echo whenever your computer boots or you log in.
echo.
echo Project Path: %PROJECT_ROOT%
echo Script:       %LAUNCH_SCRIPT%
echo.

:: Create task in Task Scheduler using schtasks
schtasks /create /tn "%TASK_NAME%" /tr "\"%LAUNCH_SCRIPT%\"" /sc onlogon /rl highest /f

if %errorlevel% equ 0 (
    echo.
    echo ===================================================================
    echo  [SUCCESS] Autostart task '%TASK_NAME%' registered successfully!
    echo ===================================================================
    echo  - NOUS will automatically start on login and run 24/7.
    echo  - You can manage or delete this task anytime in Task Scheduler
    echo    or by running 'deploy\windows\uninstall_autostart_task.bat'.
    echo.
) else (
    echo.
    echo [ERROR] Failed to register task. Please right-click this script
    echo and choose 'Run as administrator'.
    echo.
)

pause
