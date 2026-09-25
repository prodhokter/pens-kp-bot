"""
Academic Activity Narrative Synthesis & Campus WAF Sanitizer
Mendukung 4 Sumber Data:
1. 'bank' : Bank template narasi akademis otomatis (rotasi cerdas tanpa perlu ketik)
2. 'file' : Membaca berkas teks sederhana (kegiatan.txt atau kegiatan.json)
3. 'ai'   : Sintesis dinamis via Google Gemini / Groq API (opsional)
4. 'git'  : Mengambil ringkasan riwayat commit git lokal
"""

import os
import json
import random
import datetime
import subprocess
import requests
from typing import Dict, Any, Optional, List

MONTH_NAMES_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
]

DEFAULT_WAF_REPLACEMENTS = {
    "&": "dan",
    "identity insert": "identity insersi",
    "insert ": "penyisipan ",
    "hard delete": "penghapusan permanen",
    "soft delete": "penonaktifan lunak",
    "delete ": "penghapusan ",
    "drop ": "pelepasan ",
    "select ": "pemilihan ",
    "union ": "penggabungan ",
    "truncate ": "pengosongan "
}

def sanitize_for_waf(text: str, custom_rules: Optional[Dict[str, str]] = None) -> str:
    """Sanitizes text to prevent false positives on PENS campus WAF."""
    rules = custom_rules or DEFAULT_WAF_REPLACEMENTS
    cleaned = text
    for target, replacement in rules.items():
        cleaned = cleaned.replace(target, replacement)
        cleaned = cleaned.replace(target.upper(), replacement)
        cleaned = cleaned.replace(target.capitalize(), replacement)
    return cleaned

def format_date_id(target_date: datetime.date) -> str:
    """Formats date in Indonesian: '25 September 2026'."""
    month_name = MONTH_NAMES_ID[target_date.month - 1]
    return f"{target_date.strftime('%d')} {month_name} {target_date.year}"

def calculate_week(target_date: datetime.date, start_date: datetime.date, base_week: int = 1) -> int:
    """Calculates active week number based on start date."""
    delta_days = (target_date - start_date).days
    if delta_days < 0:
        return base_week
    return base_week + (delta_days // 7)

def _read_from_file_source(target_date: datetime.date, file_path: str) -> Optional[str]:
    """Reads description from a user-provided file (txt or json)."""
    if not os.path.exists(file_path):
        return None

    date_str = target_date.strftime("%Y-%m-%d")
    date_id_prefix = format_date_id(target_date)

    # 1. JSON File (key: "YYYY-MM-DD" or list of entries)
    if file_path.endswith(".json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if date_str in data:
                    val = data[date_str]
                    return val if isinstance(val, str) else str(val)
            elif isinstance(data, list) and data:
                # Rotate by day of year if list of strings
                day_index = target_date.timetuple().tm_yday % len(data)
                return str(data[day_index])
        except Exception as e:
            print(f"[!] Gagal membaca berkas JSON {file_path}: {e}")
            return None

    # 2. TXT File
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
        
        # Check if line starts with YYYY-MM-DD
        for line in lines:
            if line.startswith(date_str):
                parts = line.split(":", 1) if ":" in line else line.split(" ", 1)
                if len(parts) > 1:
                    return parts[1].strip()

        # Fallback: Pick a line based on day of year to ensure deterministic rotation
        if lines:
            idx = target_date.timetuple().tm_yday % len(lines)
            return lines[idx]
    except Exception as e:
        print(f"[!] Gagal membaca berkas teks {file_path}: {e}")

    return None

def _generate_from_ai_source(
    target_date: datetime.date,
    company: str,
    role: str,
    api_key: str,
    provider: str = "gemini"
) -> Optional[str]:
    """Generates 2-3 sentences of academic internship narrative via Gemini / Groq."""
    if not api_key:
        return None

    prompt = (
        f"Buatkan satu paragraf narasi kegiatan harian resmi untuk logbook Kerja Praktek (KP) mahasiswa "
        f"tanggal {format_date_id(target_date)}. "
        f"Instansi: {company}. Peran/Tugas: {role}. "
        f"Format: 2-3 kalimat formal bahasa Indonesia baku, realistis, dan berbobot akademis. "
        f"JANGAN gunakan kata 'insert', 'delete', 'select', 'drop', 'union', atau simbol ampersand (&). "
        f"Tulis langsung narasinya saja tanpa pembuka, tanpa tanda kutip, dan tanpa awalan tanggal."
    )

    try:
        if provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = requests.post(url, json=payload, timeout=20)
            data = resp.json()
            narrative = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return narrative
        elif provider == "groq":
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}"}
            payload = {
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=20)
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[!] Generator AI gagal: {e}. Mengalihkan ke bank template.")
        return None

def _read_from_git_source(target_date: datetime.date, git_dir: str) -> Optional[str]:
    """Extracts git commit messages for the given date from a local repository."""
    if not git_dir or not os.path.exists(git_dir):
        return None

    date_str = target_date.strftime("%Y-%m-%d")
    cmd = [
        "git", "-C", git_dir, "log",
        f"--since={date_str} 00:00:00",
        f"--until={date_str} 23:59:59",
        "--pretty=format:%s"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        lines = [l.strip() for l in res.stdout.splitlines() if l.strip()]
        if lines:
            commits_summary = ". ".join(lines[:3])
            return f"Melakukan pengembangan dan perbaikan kode: {commits_summary}."
    except Exception:
        pass
    return None

def synthesize_activity(
    target_date: datetime.date,
    domain: str = "software",
    session_type: str = "single",
    config: Optional[Dict[str, Any]] = None,
    explicit_text: Optional[str] = None
) -> str:
    """
    Synthesizes academic KP activity narrative from the configured source:
    1. explicit_text CLI argument (highest priority)
    2. File source (kegiatan.txt / kegiatan.json)
    3. AI source (Gemini / Groq)
    4. Git source (local git commits)
    5. Template bank (built-in robust rotation)
    """
    date_str = format_date_id(target_date)

    # 1. Priority: Explicit text argument
    if explicit_text and explicit_text.strip():
        raw_text = explicit_text.strip()
        if not raw_text.startswith(str(target_date.day)):
            raw_text = f"{date_str} {raw_text}"
        return sanitize_for_waf(raw_text)

    cfg = config or {}
    source_cfg = cfg.get("activity_source", {})
    source_type = source_cfg.get("type", "bank").lower()
    body_text = None

    # 2. File Source
    if source_type == "file":
        file_path = source_cfg.get("file_path", "kegiatan.txt")
        body_text = _read_from_file_source(target_date, file_path)

    # 3. AI Source
    elif source_type == "ai":
        api_key = os.getenv("AI_API_KEY", source_cfg.get("api_key", ""))
        provider = source_cfg.get("provider", "gemini")
        company = cfg.get("company", {}).get("name", "Tempat Kerja Praktek")
        role = source_cfg.get("role_description", f"Mahasiswa magang bidang {domain}")
        body_text = _generate_from_ai_source(target_date, company, role, api_key, provider)

    # 4. Git Source
    elif source_type == "git":
        git_dir = source_cfg.get("git_repo_path", "")
        body_text = _read_from_git_source(target_date, git_dir)

    # 5. Default Fallback: Template Bank
    if not body_text:
        custom_pool = cfg.get("custom_activities", [])
        if custom_pool and isinstance(custom_pool, list) and len(custom_pool) > 0:
            body_text = random.choice(custom_pool)
        else:
            domain_templates = cfg.get("domain_templates", {})
            domain_data = domain_templates.get(domain, domain_templates.get("general", {}))
            
            # Map session type: if 'single', fallback to 'morning' or 'single' if defined
            session_data = domain_data.get(session_type, domain_data.get("single", domain_data.get("morning", {})))
            
            day_idx = target_date.weekday()
            day_key = "saturday" if day_idx == 5 else ("sunday" if day_idx == 6 else "weekday")
            candidates = session_data.get(day_key, [])
            if not candidates:
                candidates = session_data.get("weekday", [
                    "Melaksanakan tugas operasional teknis harian sesuai dengan arahan pembimbing lapangan. Melakukan verifikasi hasil kerja dan penyusunan dokumentasi progres kerja."
                ])
            body_text = random.choice(candidates)

    # Ensure date prefix
    if not body_text.startswith(str(target_date.day)):
        full_narrative = f"{date_str} {body_text}"
    else:
        full_narrative = body_text

    # Apply WAF sanitizer
    waf_cfg = cfg.get("waf_sanitizer", {})
    if waf_cfg.get("enabled", True):
        replacements = waf_cfg.get("replacements", DEFAULT_WAF_REPLACEMENTS)
        return sanitize_for_waf(full_narrative, replacements)

    return full_narrative
