"""
Notification Dispatcher for Telegram Bot & Discord Webhook
"""

import requests
from typing import Dict, Any, Optional

def dispatch_notification(
    result: Dict[str, Any],
    profile: Dict[str, Any],
    telegram_token: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
    discord_webhook_url: Optional[str] = None
) -> None:
    """Dispatches submission status report to Telegram or Discord."""
    date_str = result.get("date", "")
    session_label = result.get("session", "Sesi Kerja")
    jam = f"{result.get('jam_mulai', '')} - {result.get('jam_selesai', '')} WIB"
    minggu = result.get("minggu", "")
    nama = profile.get("nama", "Mahasiswa")
    nrp = profile.get("nrp", "")
    company = profile.get("company", "Tempat Kerja Praktek")
    
    if result.get("already_exists"):
        status_tag = "[TERCATAT SEBELUMNYA]"
    elif result.get("success"):
        status_tag = "[SUKSES DISIMPAN]"
    else:
        status_tag = "[GAGAL MENYIMPAN]"

    kegiatan = result.get("kegiatan", "")

    # 1. Telegram Message (Markdown)
    if telegram_token and telegram_chat_id:
        tg_text = (
            f"*STATUS LOGBOOK KP PENS - {status_tag}*\n"
            f"--------------------------------------------------\n"
            f"*Mahasiswa:* {nama} ({nrp})\n"
            f"*Instansi:* {company}\n"
            f"*Tanggal:* {date_str} (Minggu ke-{minggu})\n"
            f"*Sesi:* {session_label} ({jam})\n"
            f"--------------------------------------------------\n"
            f"*Narasi Kegiatan:*\n"
            f"_{kegiatan}_\n"
            f"--------------------------------------------------\n"
            f"Status Sistem: Online MIS Sinkron"
        )
        try:
            tg_url = f"https://api.telegram.org/bot{telegram_token.strip()}/sendMessage"
            requests.post(tg_url, json={
                "chat_id": telegram_chat_id.strip(),
                "text": tg_text,
                "parse_mode": "Markdown"
            }, timeout=10)
        except Exception as e:
            print(f"[!] Gagal mengirim notifikasi Telegram: {e}")

    # 2. Discord Webhook
    if discord_webhook_url and discord_webhook_url.strip():
        discord_payload = {
            "content": (
                f"**STATUS LOGBOOK KP PENS - {status_tag}**\n"
                f"**Mahasiswa:** {nama} ({nrp})\n"
                f"**Tanggal:** {date_str} | **Sesi:** {session_label} ({jam})\n"
                f"**Kegiatan:** {kegiatan}"
            )
        }
        try:
            requests.post(discord_webhook_url.strip(), json=discord_payload, timeout=10)
        except Exception as e:
            print(f"[!] Gagal mengirim webhook Discord: {e}")
