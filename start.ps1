# ==============================================================================
# NOUS - Personal AI Assistant Startup Script (Windows PowerShell)
# "Your Intelligence. Your Memory. Your Assistant."
# ==============================================================================

$Host.UI.RawUI.WindowTitle = "NOUS Personal AI Assistant Engine"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   NOUS - Personal AI Assistant Engine v1.0.0" -ForegroundColor Cyan
Write-Host "   'Your Intelligence. Your Memory. Your Assistant.'" -ForegroundColor DarkCyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Resolve Project Root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# 2. Check Virtual Environment
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    Write-Host "[1/4] Python Environment:" -NoNewline -ForegroundColor White
    Write-Host " (.venv detected) " -NoNewline -ForegroundColor Green
    Write-Host $VenvPython -ForegroundColor Gray
    $PythonCmd = $VenvPython
} else {
    Write-Host "[1/4] Python Environment: Using system PATH python" -ForegroundColor Yellow
    $PythonCmd = "python"
}

# 3. Check SQLite Databases Directory
$DbDir = Join-Path $ScriptDir "data\database"
if (-not (Test-Path $DbDir)) {
    New-Item -ItemType Directory -Path $DbDir -Force | Out-Null
}
$Dbs = Get-ChildItem -Path $DbDir -Filter "*.db" -ErrorAction SilentlyContinue
Write-Host "[2/4] Storage Engines: " -NoNewline -ForegroundColor White
Write-Host "$($Dbs.Count) SQLite WAL databases active in data/database/" -ForegroundColor Green

# 4. Check Ollama Local Engine
Write-Host "[3/4] Ollama Local Engine: " -NoNewline -ForegroundColor White
try {
    $OllamaCheck = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction Stop
    $ModelCount = $OllamaCheck.models.Count
    Write-Host "ONLINE ($ModelCount local models available)" -ForegroundColor Green
} catch {
    Write-Host "OFFLINE (Cloud fallback or local Ollama startup recommended)" -ForegroundColor Yellow
}

# 5. Launch Browser & Server
Write-Host "[4/4] Starting Uvicorn Server (Laptop: http://127.0.0.1:8000 | Phone: http://192.168.1.4:8000) ..." -ForegroundColor Cyan
Start-Process "http://127.0.0.1:8000"

& $PythonCmd -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
