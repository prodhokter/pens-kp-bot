@echo off
setlocal

:: ==============================================================================
:: PENS KP LOGBOOK SENTINEL - WINDOWS AUTO-SCHEDULER INSTALLER (1-KLIK)
:: Memasang tugas terjadwal otomatis di Windows Task Scheduler dengan fitur catch-up
:: (Jika laptop mati/tidur saat jam jadwal, tugas otomatis jalan saat laptop nyala)
:: ==============================================================================

cd /d "%~dp0\.."

echo ==============================================================================
echo PEMASANG PENJADWAL OTOMATIS WINDOWS (PENS KP LOGBOOK SENTINEL)
echo ==============================================================================
echo.

:: Minta jam eksekusi harian (default 16:15)
set "TRIGGER_TIME=16:15"
set /p "USER_TIME=Masukkan jam eksekusi harian (format HH:mm, default 16:15): "
if not "%USER_TIME%"=="" set "TRIGGER_TIME=%USER_TIME%"

echo.
echo Mengonfigurasi Windows Task Scheduler untuk berjalan setiap hari pada pukul %TRIGGER_TIME% WIB...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_windows_task.ps1" -TriggerTime "%TRIGGER_TIME%" -AppDir "%CD%"

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Gagal memasang tugas otomatis. Pastikan Anda menjalankan Command Prompt sebagai Administrator.
    pause
    exit /b %errorlevel%
)

echo.
echo ==============================================================================
echo [SUKSES] Penjadwalan otomatis berhasil terpasang di Windows Task Scheduler!
echo Nama Tugas : PENS_KP_Logbook_Sentinel
echo Jam Eksekusi: %TRIGGER_TIME% WIB (Setiap hari kerja)
echo Fitur Aktif : Catch-Up otomatis saat laptop menyala jika jam jadwal terlewat.
echo ==============================================================================
echo.
pause
