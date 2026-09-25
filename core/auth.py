"""
PENS Central Authentication Service (CAS) Session & Auth Handler
"""

import time
import requests
from bs4 import BeautifulSoup
from typing import Optional

LOGIN_ENTRY_URL = "https://online.mis.pens.ac.id/index.php?Login=1&halAwal=1"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)

def create_session(proxy_url: Optional[str] = None) -> requests.Session:
    """Creates a configured requests.Session with headers and optional proxy."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "id,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
    })
    
    if proxy_url and proxy_url.strip():
        proxy_clean = proxy_url.strip()
        session.proxies = {
            "http": proxy_clean,
            "https": proxy_clean
        }
        
    return session

def login_cas(session: requests.Session, netid: str, password: str, timeout: int = 45) -> bool:
    """
    Authenticates into PENS CAS and captures SSO session cookies.
    Raises RuntimeError on failure after retries.
    """
    if not netid or not password:
        raise ValueError("PENS NetID dan kata sandi tidak boleh kosong. Periksa file .env Anda.")

    last_error = None
    for attempt in range(1, 4):
        try:
            # 1. Access portal entry to initiate SSO handshake
            resp = session.get(LOGIN_ENTRY_URL, timeout=timeout)
            
            # If already logged in (active session cookie)
            if "cas/login" not in resp.url and "login.pens.ac.id" not in resp.url:
                if "Logout" in resp.text or "Mahasiswa" in resp.text:
                    return True

            # 2. Parse CAS login form & LT ticket
            soup = BeautifulSoup(resp.text, "html.parser")
            form = soup.find("form")
            if not form:
                raise RuntimeError("Form login CAS tidak ditemukan pada halaman otentikasi.")

            action = form.get("action", "")
            if not action.startswith("http"):
                action = "https://login.pens.ac.id" + action

            lt_input = soup.find("input", {"name": "lt"})
            if not lt_input:
                raise RuntimeError("Tiket 'lt' CAS tidak ditemukan. Halaman mungkin berubah atau terblokir.")

            # 3. Submit credentials to CAS
            payload = {
                "username": netid.strip(),
                "password": password.strip(),
                "lt": lt_input["value"],
                "_eventId": "submit",
                "submit": "LOGIN"
            }

            auth_resp = session.post(action, data=payload, timeout=timeout)
            
            # 4. Check for invalid credentials
            text_upper = auth_resp.text.upper()
            if "TIDAK VALID" in text_upper or "GAGAL" in text_upper or "SALAH" in text_upper:
                raise RuntimeError("Otentikasi CAS gagal: NetID atau kata sandi tidak valid.")

            # 5. Follow redirect to verify final landing
            portal_check = session.get("https://online.mis.pens.ac.id/index.php", timeout=timeout)
            if "Logout" in portal_check.text or "mEntry_Logbook_KP1" in portal_check.text:
                return True

            return True

        except Exception as exc:
            last_error = exc
            if "tidak valid" in str(exc).lower():
                raise exc
            time.sleep(3)

    raise RuntimeError(f"Gagal otentikasi PENS CAS setelah 3 percobaan: {last_error}")
