@echo off
title NOUS Personal AI Assistant
color 0B
cd /d "%~dp0"

echo ===================================================================
echo   NOUS - Personal AI Assistant
echo   "Your Intelligence. Your Memory. Your Assistant."
echo ===================================================================
echo [1/3] Initializing Python Virtual Environment...

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo  [OK] Virtual environment activated (.venv).
) else (
    echo  [WARNING] .venv not found. Using system Python.
)

echo [2/3] Checking Ollama Local Model Engine...
curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo  [OK] Ollama is ONLINE at http://127.0.0.1:11434 (qwen2.5:3b ready).
) else (
    echo  [NOTE] Ollama local service not detected on port 11434.
    echo         If local inference is required, please launch Ollama.
)

echo [3/3] Launching NOUS Web Server on http://127.0.0.1:8000 ...
start "" http://127.0.0.1:8000

python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

pause
