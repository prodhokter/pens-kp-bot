"""
Academic Activity Narrative Synthesis & Campus WAF Sanitizer
"""

import random
import datetime
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
    """
    Sanitizes logbook text to prevent false positives on PENS campus WAF.
    Replaces SQL keywords and special characters that could trigger web application firewall blocks.
    """
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

def synthesize_activity(
    target_date: datetime.date,
    domain: str = "software",
    session_type: str = "morning",
    config: Optional[Dict[str, Any]] = None,
    explicit_text: Optional[str] = None
) -> str:
    """
    Synthesizes academic KP activity narrative tailored for the specified date and session.
    If explicit_text is provided, it is sanitized and returned.
    """
    date_str = format_date_id(target_date)

    if explicit_text and explicit_text.strip():
        raw_text = explicit_text.strip()
        if not raw_text.startswith(str(target_date.day)):
            raw_text = f"{date_str} {raw_text}"
        return sanitize_for_waf(raw_text)

    cfg = config or {}
    domain_templates = cfg.get("domain_templates", {})
    custom_pool = cfg.get("custom_activities", [])

    # 1. Use custom pool if available
    if custom_pool and isinstance(custom_pool, list) and len(custom_pool) > 0:
        chosen = random.choice(custom_pool)
        return sanitize_for_waf(f"{date_str} {chosen}")

    # 2. Select from domain templates
    domain_data = domain_templates.get(domain, domain_templates.get("general", {}))
    session_data = domain_data.get(session_type, domain_data.get("morning", {}))

    day_idx = target_date.weekday()
    if day_idx == 5:
        day_key = "saturday"
    elif day_idx == 6:
        day_key = "sunday"
    else:
        day_key = "weekday"

    candidates = session_data.get(day_key, [])
    if not candidates:
        # Fallback to weekday candidates
        candidates = session_data.get("weekday", [
            "Melaksanakan tugas operasional teknis harian sesuai dengan arahan pembimbing lapangan. Melakukan verifikasi hasil kerja dan penyusunan dokumentasi progres kerja."
        ])

    body = random.choice(candidates)
    full_narrative = f"{date_str} {body}"

    # 3. Apply WAF sanitizer
    waf_cfg = cfg.get("waf_sanitizer", {})
    if waf_cfg.get("enabled", True):
        replacements = waf_cfg.get("replacements", DEFAULT_WAF_REPLACEMENTS)
        return sanitize_for_waf(full_narrative, replacements)

    return full_narrative
