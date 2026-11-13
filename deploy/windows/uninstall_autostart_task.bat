@echo off
title Uninstall NOUS 24/7 Autostart Background Task
color 0C

set "TASK_NAME=NOUS_Assistant_247"

echo ===================================================================
echo   NOUS - Uninstall 24/7 Autostart Background Task
echo ===================================================================
echo.
echo Removing scheduled task '%TASK_NAME%'...
schtasks /delete /tn "%TASK_NAME%" /f

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Task '%TASK_NAME%' removed successfully.
) else (
    echo.
    echo [NOTE] Task '%TASK_NAME%' was not found or already removed.
)

pause
