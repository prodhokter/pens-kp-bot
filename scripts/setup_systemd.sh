#!/usr/bin/env bash
# ==============================================================================
# PEMASANGAN OTOMASI SYSTEMD SERVICE & TIMER UNTUK LINUX
# Menjadwalkan pengisian otomatis:
# 1. Sesi Pagi : Pukul 12:00 WIB (05:00 UTC)
# 2. Sesi Sore : Pukul 16:00 WIB (09:00 UTC)
# ==============================================================================

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
   echo "[ERROR] Skrip ini harus dijalankan dengan hak akses root (sudo)." 
   exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_EXEC="${REPO_DIR}/venv/bin/python3"

if [[ ! -f "${PYTHON_EXEC}" ]]; then
    PYTHON_EXEC="$(which python3)"
fi

echo "Direktori instalasi: ${REPO_DIR}"
echo "Eksekutor Python   : ${PYTHON_EXEC}"

# 1. Buat Service Unit
cat <<EOF > /etc/systemd/system/pens-kp.service
[Unit]
Description=PENS KP Automated Logbook Sentinel Service
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=${SUDO_USER:-root}
WorkingDirectory=${REPO_DIR}
ExecStart=${PYTHON_EXEC} ${REPO_DIR}/main.py run
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 2. Buat Timer Unit
cat <<EOF > /etc/systemd/system/pens-kp.timer
[Unit]
Description=Trigger Pengisian Logbook KP PENS 2 Kali Sehari (12:00 dan 16:00)

[Timer]
# Sesi Siang (Pukul 12:00)
OnCalendar=*-*-* 12:00:00
# Sesi Sore (Pukul 16:00)
OnCalendar=*-*-* 16:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 3. Reload & Enable
systemctl daemon-reload
systemctl enable --now pens-kp.timer

echo ""
echo "=== SYSTEMD TIMER BERHASIL DIPASANG ==="
systemctl list-timers --all | grep pens-kp || true
echo "Status log dapat dipantau via: journalctl -u pens-kp.service -f"
