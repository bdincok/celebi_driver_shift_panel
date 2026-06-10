@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
title ISTCLB Driver Paket Guncelleme

echo Paketler ve veritabani guncelleniyor...

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
python manage.py migrate --noinput
python manage.py seed_initial_data

echo.
echo Guncelleme tamamlandi. Uygulamayi BASLAT.bat ile acabilirsiniz.
pause
