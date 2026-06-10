@echo off
chcp 65001 > nul
setlocal
cd /d "%~dp0"
title ISTCLB Driver Yedek Al

if not exist "backups" mkdir backups
if not exist "data\istclbdriver_local.sqlite3" (
    echo Henuz veritabani olusmamis. Once BASLAT.bat ile uygulamayi acin.
    pause
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command "$ts=Get-Date -Format 'yyyyMMdd_HHmmss'; Copy-Item 'data\istclbdriver_local.sqlite3' ('backups\istclbdriver_local_MANUEL_' + $ts + '.sqlite3')"
echo Yedek backups klasorune alindi.
pause
