@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
title ISTCLB Driver Yerel Panel

echo =====================================================
echo  ISTCLB DRIVER - YEREL CIFT TIKLA PANEL
echo =====================================================
echo.

if not exist "manage.py" (
    echo HATA: manage.py bulunamadi.
    echo Bu dosyayi ZIP icinden degil, klasore cikardiktan sonra calistirin.
    pause
    exit /b 1
)

if not exist "data" mkdir data
if not exist "backups" mkdir backups

if not exist ".venv\Scripts\python.exe" (
    echo Ilk kurulum yapiliyor. Bu islem ilk acilista biraz surebilir...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo py komutu calismadi, python ile deneniyor...
        python -m venv .venv
    )
)

call ".venv\Scripts\activate.bat"

echo Gerekli paketler kontrol ediliyor...
python -m pip install --upgrade pip
pip install -r requirements.txt

if exist "data\istclbdriver_local.sqlite3" (
    echo Otomatik yedek aliniyor...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$ts=Get-Date -Format 'yyyyMMdd_HHmmss'; Copy-Item 'data\istclbdriver_local.sqlite3' ('backups\istclbdriver_local_' + $ts + '.sqlite3')" > nul 2>&1
)

echo Veritabani hazirlaniyor...
python manage.py migrate --noinput
python manage.py seed_initial_data

echo.
echo Uygulama aciliyor: http://127.0.0.1:8000
echo Kapatmak icin bu siyah ekranda CTRL + C yapabilirsiniz.
echo.
start "" "http://127.0.0.1:8000"
python manage.py runserver 127.0.0.1:8000

pause
