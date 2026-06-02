@echo off
cd /d "%~dp0"
echo Giyim Magazasi API Sunucusu baslatiliyor...
python -m pip install -r server\requirements.txt -q
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
pause
