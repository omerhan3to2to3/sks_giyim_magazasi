@echo off
cd /d "%~dp0"
echo Giyim Magazasi Masaustu Uygulamasi baslatiliyor...
python -m pip install -r client\requirements.txt -q
python client\main.py
pause
