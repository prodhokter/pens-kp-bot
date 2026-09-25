param (
    [string]$TriggerTime = "16:15",
    [string]$AppDir = ""
)

if (-not $AppDir) {
    $AppDir = Split-Path -Parent $PSScriptRoot
}

$TaskName = "PENS_KP_Logbook_Sentinel"
$BatchScript = Join-Path $AppDir "scripts\run.bat"

Write-Host "Lokasi Aplikasi : $AppDir"
Write-Host "Target Script   : $BatchScript"
Write-Host "Jam Eksekusi    : $TriggerTime"

# 1. Action: Jalankan run.bat di background/cmd
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchScript`"" -WorkingDirectory $AppDir

# 2. Trigger: Setiap hari pada TriggerTime
$Trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime

# 3. Settings:
# - StartWhenAvailable: JALANKAN SEGERA JIKA JADWAL TERLEWAT (saat laptop mati/sleep)
# - AllowStartIfOnBatteries: Tetap jalan meski laptop memakai baterai
# - DontStopIfGoingOnBatteries: Jangan stop jika charger dicabut
# - ExecutionTimeLimit: Batas waktu eksekusi 15 menit
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -MultipleInstances IgnoreNew

# 4. Daftarkan tugas
try {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Otomasi Pengisian Logbook KP PENS Harian" | Out-Null
    Write-Host "[OK] Task $TaskName berhasil didaftarkan." -ForegroundColor Green
    exit 0
} catch {
    Write-Error "Gagal mendaftarkan Scheduled Task: $_"
    exit 1
}
