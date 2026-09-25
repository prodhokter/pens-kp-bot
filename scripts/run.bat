@echo off
setlocal enabledelayedexpansion

:: ==============================================================================
:: PENS KP LOGBOOK SENTINEL - WINDOWS RUNNER SCRIPT
:: Digunakan untuk eksekusi manual atau penjadwalan via Windows Task Scheduler
:: ==============================================================================

cd /d "%~dp0\.."

:: Cek keberadaan Python di virtual environment atau sistem global
if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo [%date% %time%] Menjalankan sinkronisasi logbook KP PENS...
"%PYTHON_EXE%" main.py run %*

if %errorlevel% neq 0 (
    echo [%date% %time%] Eksekusi gagal dengan kode keluar %errorlevel%.
    exit /b %errorlevel%
)

echo [%date% %time%] Eksekusi logbook berhasil diselesaikan.
exit /b 0
