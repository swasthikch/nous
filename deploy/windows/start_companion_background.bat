@echo off
cd /d "E:\nous"
"E:\nous\.venv\Scripts\python.exe" -m desktop.companion "http://127.0.0.1:8000" > "E:\nous\data\companion.log" 2>&1
