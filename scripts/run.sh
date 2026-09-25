#!/usr/bin/env bash
# ==============================================================================
# PENS KP LOGBOOK SENTINEL - LINUX & MACOS RUNNER SCRIPT
# Digunakan untuk eksekusi manual atau penjadwalan via cron / launchd
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${SCRIPT_DIR}"

# Deteksi Python Virtual Environment
if [[ -f "${SCRIPT_DIR}/venv/bin/python3" ]]; then
    PYTHON_BIN="${SCRIPT_DIR}/venv/bin/python3"
elif [[ -f "${SCRIPT_DIR}/.venv/bin/python3" ]]; then
    PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python3"
else
    PYTHON_BIN="python3"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Menjalankan otomasi logbook KP PENS..."
"${PYTHON_BIN}" main.py run "$@"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Selesai."
