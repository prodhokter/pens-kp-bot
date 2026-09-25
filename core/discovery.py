"""
Automated Discovery Engine for Student Profile & KP Metadata in PENS MIS
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any

MENU_KP_URL = "https://online.mis.pens.ac.id/mEntry_Logbook_KP1.php"
ENTRY_KP_BASE_URL = "https://online.mis.pens.ac.id/entry_logbook_kp1.php"

def discover_kp_profile(session: requests.Session, timeout: int = 45) -> Dict[str, Any]:
    """
    Automatically discovers and extracts all required KP parameters:
    - Tahun Akademik & Semester Aktif
    - Minggu KP Berjalan
    - ID Pendaftaran KP (kp_daftar)
    - ID Mahasiswa di Basis Data MIS (mahasiswa)
    - Nama Lengkap & NRP Mahasiswa
    """
    # 1. Fetch main KP menu page to read dynamic initialization arguments
    resp_menu = session.get(MENU_KP_URL, timeout=timeout)
    if "cas/login" in resp_menu.url:
        raise PermissionError("Sesi login CAS telah berakhir. Harap login kembali.")

    # Match onload="showEntry_Logbook_KP1(2026, 1, 14)"
    init_match = re.search(
        r'showEntry_Logbook_KP1\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)',
        resp_menu.text
    )

    if not init_match:
        # Fallback to current year & default semester if regex missed
        raise RuntimeError(
            "Gagal mendeteksi parameter inisialisasi pada mEntry_Logbook_KP1.php. "
            "Pastikan akun Anda memiliki hak akses menu Kerja Praktek di Online MIS."
        )

    tahun = init_match.group(1)
    semester = init_match.group(2)
    minggu = init_match.group(3)

    # 2. Fetch specific form entry using the discovered arguments
    entry_url = f"{ENTRY_KP_BASE_URL}?valTahun={tahun}&valSemester={semester}&valMinggu={minggu}"
    resp_entry = session.get(entry_url, timeout=timeout)
    soup = BeautifulSoup(resp_entry.text, "html.parser")

    # 3. Extract hidden inputs (kp_daftar & mahasiswa)
    input_kp = soup.find("input", {"name": "kp_daftar"})
    input_mhs = soup.find("input", {"name": "mahasiswa"})

    kp_daftar_id = input_kp.get("value", "").strip() if input_kp else ""
    mahasiswa_id = input_mhs.get("value", "").strip() if input_mhs else ""

    if not kp_daftar_id or not mahasiswa_id:
        raise ValueError(
            "ID Pendaftaran KP (kp_daftar) atau ID Mahasiswa tidak ditemukan. "
            "Hal ini biasanya terjadi jika pendaftaran KP Anda belum disetujui atau belum aktif pada semester ini."
        )

    # 4. Extract student identity from form metadata table
    nama = ""
    nrp = ""
    company = ""
    supervisor = ""

    for tr in soup.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(tds) >= 2:
            first = tds[0].lower()
            second = tds[1].replace(":", "").strip()
            if "nama" in first and not nama:
                nama = second
            elif "nrp" in first and not nrp:
                nrp = second
            elif "perusahaan" in first or "tempat" in first:
                company = second
            elif "pembimbing" in first:
                supervisor = second

    # Fallback regex for NRP and Name if table layout differs
    if not nrp or not nama:
        text_match = re.search(r'Surabaya,\s*.*?20\d\d\s+(.*?)\s+NRP\.?\s*(\d+)', resp_entry.text)
        if text_match:
            if not nama:
                nama = text_match.group(1).strip()
            if not nrp:
                nrp = text_match.group(2).strip()

    return {
        "nama": nama,
        "nrp": nrp,
        "kp_daftar": kp_daftar_id,
        "mahasiswa": mahasiswa_id,
        "tahun": tahun,
        "semester": semester,
        "minggu": int(minggu),
        "company": company,
        "supervisor": supervisor
    }
