"""
PENS Online MIS Client: Logbook Table Reader & Idempotent Submission Engine
"""

import os
import json
import random
import datetime
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

ENTRY_FORM_URL = "https://online.mis.pens.ac.id/entry_logbook_kp1.php"

def load_local_history(history_file: str) -> Dict[str, Any]:
    """Loads local submission history cache."""
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_local_history(history_file: str, history: Dict[str, Any]) -> None:
    """Saves local submission history cache."""
    dir_name = os.path.dirname(history_file)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def get_remote_mis_entries(
    session: requests.Session,
    nrp: str,
    tahun: str,
    semester: str,
    minggu: int,
    timeout: int = 30
) -> List[Dict[str, str]]:
    """
    Fetches already recorded logbook rows from the PENS Online MIS table for a given week.
    """
    url = (
        f"{ENTRY_FORM_URL}?valnrpMahasiswa={nrp}"
        f"&valTahun={tahun}"
        f"&valSemester={semester}"
        f"&valMinggu={minggu}"
    )
    try:
        resp = session.get(url, timeout=timeout)
        soup = BeautifulSoup(resp.text, "html.parser")
        tables = soup.find_all("table")
        entries = []
        
        # In PENS MIS, table index 4 holds the recorded history list
        for table in tables:
            rows = table.find_all("tr")
            for tr in rows[1:]:
                tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if len(tds) >= 5 and tds[0].isdigit():
                    entries.append({
                        "no": tds[0],
                        "tanggal": tds[1],       # e.g. "25-SEP-26"
                        "jam_mulai": tds[2],     # e.g. "07:00"
                        "jam_selesai": tds[3],   # e.g. "12:00"
                        "kegiatan": tds[4]
                    })
        return entries
    except Exception as e:
        print(f"[!] Peringatan: Gagal membaca entri tabel MIS untuk minggu {minggu}: {e}")
        return []

def is_already_submitted(
    remote_entries: List[Dict[str, str]],
    target_date: datetime.date,
    jam_mulai: str
) -> bool:
    """
    Verifies if a specific date and starting time is already recorded on PENS MIS.
    """
    target_str = target_date.strftime("%d-%b-%y").upper() # e.g. "25-SEP-26"
    for item in remote_entries:
        if item.get("tanggal") == target_str and item.get("jam_mulai") == jam_mulai:
            return True
    return False

def submit_logbook(
    session: requests.Session,
    profile: Dict[str, Any],
    target_date: datetime.date,
    jam_mulai: str,
    jam_selesai: str,
    kegiatan: str,
    minggu: int,
    session_label: str = "Pagi",
    history_file: str = "logbook_history.json",
    check_existing: bool = True,
    timeout: int = 45
) -> Dict[str, Any]:
    """
    Submits a single logbook row to PENS Online MIS with idempotency verification.
    """
    date_iso = target_date.strftime("%Y-%m-%d")
    cache_key = f"{date_iso}_{jam_mulai.replace(':', '')}"

    # 1. Check idempotency on remote MIS portal
    if check_existing:
        remote_entries = get_remote_mis_entries(
            session=session,
            nrp=profile["nrp"],
            tahun=profile["tahun"],
            semester=profile["semester"],
            minggu=minggu,
            timeout=timeout
        )
        if is_already_submitted(remote_entries, target_date, jam_mulai):
            history = load_local_history(history_file)
            history[cache_key] = {
                "date": date_iso,
                "session": session_label,
                "jam_mulai": jam_mulai,
                "jam_selesai": jam_selesai,
                "minggu": minggu,
                "kegiatan": kegiatan,
                "status": "ALREADY_EXISTS",
                "synced_at": datetime.datetime.now().isoformat()
            }
            save_local_history(history_file, history)
            return {
                "success": True,
                "already_exists": True,
                "date": date_iso,
                "session": session_label,
                "jam_mulai": jam_mulai,
                "jam_selesai": jam_selesai,
                "minggu": minggu,
                "kegiatan": kegiatan
            }

    # 2. Build form payload
    payload = {
        "valnrpMahasiswa": profile["nrp"],
        "valTahun": profile["tahun"],
        "valSemester": profile["semester"],
        "Simpan": "1",
        "valMinggu": str(minggu),
        "tanggal": date_iso,
        "jam_mulai": jam_mulai,
        "jam_selesai": jam_selesai,
        "kegiatan": kegiatan,
        "sesuai_kuliah": "2",
        "matakuliah": "",
        "kp_daftar": profile["kp_daftar"],
        "mahasiswa": profile["mahasiswa"],
        "Setuju": "1",
        "sid": str(random.random())
    }

    # 3. Post to portal
    resp = session.post(ENTRY_FORM_URL, data=payload, timeout=timeout)
    success = ("Simpan Data Berhasil" in resp.text) or ("Berhasil" in resp.text)

    # 4. Save local record
    history = load_local_history(history_file)
    history[cache_key] = {
        "date": date_iso,
        "session": session_label,
        "jam_mulai": jam_mulai,
        "jam_selesai": jam_selesai,
        "minggu": minggu,
        "kegiatan": kegiatan,
        "status": "SUCCESS" if success else "FAILED",
        "http_status": resp.status_code,
        "synced_at": datetime.datetime.now().isoformat()
    }
    save_local_history(history_file, history)

    return {
        "success": success,
        "already_exists": False,
        "date": date_iso,
        "session": session_label,
        "jam_mulai": jam_mulai,
        "jam_selesai": jam_selesai,
        "minggu": minggu,
        "kegiatan": kegiatan,
        "http_status": resp.status_code
    }
