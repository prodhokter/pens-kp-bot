#!/usr/bin/env python3
"""
PENS KP Logbook Automation CLI & Entry Point
"""

import os
import sys
import argparse
import datetime
import yaml
from dotenv import load_dotenv

# Ensure local packages are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth import create_session, login_cas
from core.discovery import discover_kp_profile
from core.generator import synthesize_activity, calculate_week, format_date_id
from core.client import submit_logbook, get_remote_mis_entries, load_local_history
from core.notifier import dispatch_notification

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.yaml")
CONFIG_EXAMPLE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.example.yaml")
ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logbook_history.json")

def load_app_config() -> dict:
    """Loads configuration yaml file."""
    path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else CONFIG_EXAMPLE_PATH
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def get_env_credentials():
    """Reads credentials and environment variables."""
    load_dotenv(ENV_PATH, override=True)
    return {
        "netid": os.getenv("PENS_NETID", "").strip(),
        "password": os.getenv("PENS_PASSWORD", "").strip(),
        "proxy_url": os.getenv("PROXY_URL", "").strip() or None,
        "mode": os.getenv("SUBMISSION_MODE", "dual").strip().lower(),
        "domain": os.getenv("ACTIVITY_DOMAIN", "software").strip().lower(),
        "start_date": os.getenv("KP_START_DATE", "2026-08-31").strip(),
        "telegram_token": os.getenv("TELEGRAM_BOT_TOKEN", "").strip() or None,
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", "").strip() or None,
        "discord_webhook": os.getenv("DISCORD_WEBHOOK_URL", "").strip() or None,
        "nrp": os.getenv("PENS_NRP", "").strip(),
        "mahasiswa_id": os.getenv("PENS_MAHASISWA_ID", "").strip(),
        "kp_daftar_id": os.getenv("PENS_KP_DAFTAR_ID", "").strip(),
        "tahun": os.getenv("PENS_TAHUN", "").strip(),
        "semester": os.getenv("PENS_SEMESTER", "").strip()
    }

def command_setup(args):
    """Interactive setup wizard to initialize .env and config.yaml."""
    print("==================================================")
    print("PENS KP LOGBOOK SENTINEL - WIZARD INSTALASI")
    print("==================================================")
    
    existing = get_env_credentials()
    netid = input(f"Masukkan PENS NetID / Email Student [{existing['netid']}]: ").strip() or existing["netid"]
    password = input("Masukkan Kata Sandi PENS CAS: ").strip() or existing["password"]
    proxy = input(f"Proxy URL (kosongkan jika koneksi langsung) [{existing['proxy_url'] or '-'}]: ").strip()
    if proxy == "-":
        proxy = ""
    proxy = proxy or (existing["proxy_url"] or "")

    print("\nMenghubungi PENS Central Authentication Service (CAS)...")
    session = create_session(proxy_url=proxy or None)
    try:
        login_cas(session, netid, password)
        print("[SUKSES] Otentikasi CAS berhasil diverifikasi.")
    except Exception as e:
        print(f"[ERROR] Gagal login ke PENS CAS: {e}")
        return

    print("Membaca data profil mahasiswa dan pendaftaran KP dari Online MIS...")
    try:
        profile = discover_kp_profile(session)
        print("\nDATA MAHASISWA TERVERIFIKASI:")
        print(f"  Nama Lengkap  : {profile['nama']}")
        print(f"  NRP           : {profile['nrp']}")
        print(f"  ID Pendaftaran: {profile['kp_daftar']}")
        print(f"  ID Mahasiswa  : {profile['mahasiswa']}")
        print(f"  Tahun / Sem   : {profile['tahun']} / Semester {profile['semester']}")
        print(f"  Minggu Berjalan: Minggu ke-{profile['minggu']}")
        if profile.get('company'):
            print(f"  Instansi      : {profile['company']}")
    except Exception as e:
        print(f"[ERROR] Gagal mendeteksi profil KP: {e}")
        return

    print("\nPILIHAN MODE OPERASIONAL:")
    print("  1. Single-Session (1x sehari: misal 08:00-16:00 - Rekomendasi)")
    print("  2. Dual-Session (2x sehari: Pagi 07:00-12:00 dan Sore 13:00-16:00)")
    mode_choice = input("Pilih mode [1]: ").strip()
    mode = "dual" if mode_choice == "2" else "single"

    print("\nINFORMASI INSTANSI & JAM KERJA MAGANG:")
    default_company = profile.get('company') or "PT. Perusahaan Tempat KP"
    company_input = input(f"Nama Perusahaan / Tempat KP [{default_company}]: ").strip()
    company_name = company_input if company_input else default_company

    start_time_val = "08:00"
    end_time_val = "16:00"
    if mode == "single":
        start_input = input("Jam Mulai Kerja (format HH:mm) [08:00]: ").strip()
        end_input = input("Jam Selesai Kerja (format HH:mm) [16:00]: ").strip()
        if start_input:
            start_time_val = start_input
        if end_input:
            end_time_val = end_input
    else:
        print("Jam kerja disetel standar dual session: Pagi 07:00-12:00 dan Sore 13:00-16:00.")

    print("\nPILIHAN BIDANG KEGIATAN:")
    print("  1. software   (Software Engineering, Web, Backend)")
    print("  2. network    (Computer Network, Server, Mikrotik/Cisco)")
    print("  3. it_support (IT Support, Hardware, Sistem Operasi)")
    print("  4. general    (Kegiatan umum teknis dan operasional)")
    domain_choice = input("Pilih bidang kegiatan [1]: ").strip()
    domain_map = {"1": "software", "2": "network", "3": "it_support", "4": "general"}
    domain = domain_map.get(domain_choice, "software")

    # Save to .env
    env_content = (
        f"# Konfigurasi Otomatis PENS KP Sentinel\n"
        f"PENS_NETID={netid}\n"
        f"PENS_PASSWORD={password}\n"
        f"PENS_NRP={profile['nrp']}\n"
        f"PENS_MAHASISWA_ID={profile['mahasiswa']}\n"
        f"PENS_KP_DAFTAR_ID={profile['kp_daftar']}\n"
        f"PENS_TAHUN={profile['tahun']}\n"
        f"PENS_SEMESTER={profile['semester']}\n"
        f"SUBMISSION_MODE={mode}\n"
        f"ACTIVITY_DOMAIN={domain}\n"
        f"KP_START_DATE=2026-08-31\n"
        f"PROXY_URL={proxy}\n"
        f"TELEGRAM_BOT_TOKEN=\n"
        f"TELEGRAM_CHAT_ID=\n"
        f"DISCORD_WEBHOOK_URL=\n"
    )

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(env_content)
    print(f"\n[SUKSES] Konfigurasi kredensial tersimpan di: {ENV_PATH}")

    # Generate / update config.yaml with custom company and hours
    cfg_base = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg_base = yaml.safe_load(f) or {}
    elif os.path.exists(CONFIG_EXAMPLE_PATH):
        with open(CONFIG_EXAMPLE_PATH, "r", encoding="utf-8") as f:
            cfg_base = yaml.safe_load(f) or {}

    if cfg_base:
        if "settings" not in cfg_base:
            cfg_base["settings"] = {}
        cfg_base["settings"]["mode"] = mode
        
        if "company" not in cfg_base:
            cfg_base["company"] = {}
        cfg_base["company"]["name"] = company_name

        if "schedule" not in cfg_base:
            cfg_base["schedule"] = {}
        if mode == "single":
            if "single" not in cfg_base["schedule"]:
                cfg_base["schedule"]["single"] = {}
            cfg_base["schedule"]["single"]["start_time"] = start_time_val
            cfg_base["schedule"]["single"]["end_time"] = end_time_val

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(cfg_base, f, allow_unicode=True, sort_keys=False)
        print(f"[SUKSES] Konfigurasi jadwal dan instansi tersimpan di: {CONFIG_PATH}")

    print("\nInstalasi selesai. Anda dapat menjalankan perintah uji:")
    print("  python main.py test-login")
    print("  python main.py preview")
    print("  python main.py run\n")

def command_test_login(args):
    """Tests CAS login and prints current student metadata."""
    creds = get_env_credentials()
    if not creds["netid"] or not creds["password"]:
        print("[ERROR] PENS NetID atau password belum diisi. Jalankan 'python main.py setup' terlebih dahulu.")
        sys.exit(1)

    print(f"Menguji login untuk akun: {creds['netid']}...")
    session = create_session(proxy_url=creds["proxy_url"])
    try:
        login_cas(session, creds["netid"], creds["password"])
        print("[SUKSES] Otentikasi PENS CAS berhasil!")
        
        profile = discover_kp_profile(session)
        print("\nPROFIL TERVERIFIKASI:")
        print(f"  Nama           : {profile['nama']}")
        print(f"  NRP            : {profile['nrp']}")
        print(f"  ID Pendaftaran : {profile['kp_daftar']}")
        print(f"  ID Mahasiswa   : {profile['mahasiswa']}")
        print(f"  Tahun/Semester : {profile['tahun']} (Sem {profile['semester']})")
        print(f"  Minggu Portal  : Minggu ke-{profile['minggu']}")
    except Exception as e:
        print(f"[GAGAL] {e}")
        sys.exit(1)

def command_preview(args):
    """Previews activity narrative without submitting."""
    creds = get_env_credentials()
    config = load_app_config()

    target_date = datetime.date.today()
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("[ERROR] Format tanggal harus YYYY-MM-DD.")
            sys.exit(1)

    domain = args.domain or creds["domain"]
    mode = creds["mode"] or config.get("settings", {}).get("mode", "single")

    print("==================================================")
    print(f"PREVIEW NARASI LOGBOOK - {format_date_id(target_date)}")
    print(f"Mode: {mode.upper()} | Bidang: {domain} | Tanggal: {target_date.strftime('%Y-%m-%d')}")
    print("==================================================")

    if mode == "single":
        single_text = synthesize_activity(target_date, domain=domain, session_type="single", config=config)
        print(f"\n[SESI TUNGGAL / HARIAN]:\n{single_text}\n")
    else:
        pagi = synthesize_activity(target_date, domain=domain, session_type="morning", config=config)
        sore = synthesize_activity(target_date, domain=domain, session_type="afternoon", config=config)
        print(f"\n[SESI PAGI / 07:00 - 12:00 WIB]:\n{pagi}\n")
        print(f"[SESI SORE / 13:00 - 16:00 WIB]:\n{sore}\n")

def command_read_portal(args):
    """Reads entries currently recorded in PENS Online MIS."""
    creds = get_env_credentials()
    session = create_session(proxy_url=creds["proxy_url"])
    login_cas(session, creds["netid"], creds["password"])
    profile = discover_kp_profile(session)

    minggu = args.week if args.week else profile["minggu"]
    print(f"Membaca entri Online MIS untuk Minggu ke-{minggu} (NRP: {profile['nrp']})...")
    
    entries = get_remote_mis_entries(
        session=session,
        nrp=profile["nrp"],
        tahun=profile["tahun"],
        semester=profile["semester"],
        minggu=minggu
    )

    if not entries:
        print(f"Tidak ada data logbook yang tercatat pada Minggu ke-{minggu}.")
        return

    print("----------------------------------------------------------------------------------------------------")
    print(f"{'No':<3} | {'Tanggal':<10} | {'Jam':<13} | {'Kegiatan':<65}")
    print("----------------------------------------------------------------------------------------------------")
    for item in entries:
        jam = f"{item['jam_mulai']}-{item['jam_selesai']}"
        desc = (item['kegiatan'][:62] + "...") if len(item['kegiatan']) > 65 else item['kegiatan']
        print(f"{item['no']:<3} | {item['tanggal']:<10} | {jam:<13} | {desc:<65}")
    print("----------------------------------------------------------------------------------------------------")

def command_status(args):
    """Displays local submission history."""
    history = load_local_history(HISTORY_FILE)
    if not history:
        print("Belum ada riwayat pengisian lokal di logbook_history.json.")
        return

    print("====================================================================================================")
    print("RIWAYAT PENGISIAN LOGBOOK LOKAL")
    print("====================================================================================================")
    print(f"{'Tanggal':<12} | {'Sesi':<8} | {'Jam':<13} | {'Status':<18} | {'Kegiatan':<40}")
    print("----------------------------------------------------------------------------------------------------")
    sorted_keys = sorted(history.keys(), reverse=True)
    for k in sorted_keys[:15]:
        v = history[k]
        jam = f"{v.get('jam_mulai', '')}-{v.get('jam_selesai', '')}"
        desc = (v.get('kegiatan', '')[:37] + "...") if len(v.get('kegiatan', '')) > 40 else v.get('kegiatan', '')
        print(f"{v.get('date', ''):<12} | {v.get('session', ''):<8} | {jam:<13} | {v.get('status', ''):<18} | {desc:<40}")
    print("====================================================================================================")

def command_run(args):
    """Runs automated logbook submission."""
    creds = get_env_credentials()
    config = load_app_config()

    if not creds["netid"] or not creds["password"]:
        print("[ERROR] NetID atau password belum diatur. Jalankan 'python main.py setup'.")
        sys.exit(1)

    target_date = datetime.date.today()
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("[ERROR] Format tanggal tidak valid. Gunakan YYYY-MM-DD.")
            sys.exit(1)

    # Active days check (e.g. monday, tuesday, etc.)
    day_name = target_date.strftime("%A").lower()
    settings = config.get("settings", {})
    active_days = [d.lower() for d in settings.get("active_days", ["monday", "tuesday", "wednesday", "thursday", "friday"])]
    if day_name not in active_days and not args.force:
        print(f"[{format_date_id(target_date)}] Hari {day_name.capitalize()} tidak termasuk dalam jadwal hari aktif {active_days}. Melewati.")
        return

    # Determine session to run
    session_arg = args.session.lower() if args.session else "auto"
    mode = creds["mode"] or settings.get("mode", "single")
    schedule_cfg = config.get("schedule", {})

    sessions_to_run = []
    current_hour = datetime.datetime.now().hour

    if mode == "dual":
        dual_cfg = schedule_cfg.get("dual", {})
        m_cfg = dual_cfg.get("morning", {})
        a_cfg = dual_cfg.get("afternoon", {})
        m_start = m_cfg.get("start_time", "07:00")
        m_end = m_cfg.get("end_time", "12:00")
        a_start = a_cfg.get("start_time", "13:00")
        a_end = a_cfg.get("end_time", "16:00")

        if session_arg == "morning":
            sessions_to_run.append(("morning", "Pagi", m_start, m_end))
        elif session_arg == "afternoon":
            sessions_to_run.append(("afternoon", "Sore", a_start, a_end))
        elif session_arg == "all":
            sessions_to_run.append(("morning", "Pagi", m_start, m_end))
            sessions_to_run.append(("afternoon", "Sore", a_start, a_end))
        else: # auto
            if current_hour < 14:
                sessions_to_run.append(("morning", "Pagi", m_start, m_end))
            else:
                sessions_to_run.append(("afternoon", "Sore", a_start, a_end))
    else: # single mode
        s_cfg = schedule_cfg.get("single", {})
        s_start = s_cfg.get("start_time", "08:00")
        s_end = s_cfg.get("end_time", "16:00")
        s_label = s_cfg.get("label", "Sesi Penuh")
        sessions_to_run.append(("single", s_label, s_start, s_end))

    # Establish connection
    session = create_session(proxy_url=creds["proxy_url"])
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Masuk ke PENS CAS ({creds['netid']})...")
    login_cas(session, creds["netid"], creds["password"])

    # Resolve profile
    profile = {}
    if creds.get("nrp") and creds.get("kp_daftar_id") and creds.get("mahasiswa_id"):
        # Fast path with local config
        profile = {
            "nama": creds.get("netid"),
            "nrp": creds["nrp"],
            "kp_daftar": creds["kp_daftar_id"],
            "mahasiswa": creds["mahasiswa_id"],
            "tahun": creds["tahun"] or str(target_date.year),
            "semester": creds["semester"] or "1",
            "minggu": 1
        }
    
    # Run auto-discovery to ensure accurate week and student name
    try:
        discovered = discover_kp_profile(session)
        profile.update(discovered)
    except Exception as e:
        if not profile.get("kp_daftar"):
            print(f"[ERROR] Gagal mendeteksi profil mahasiswa: {e}")
            sys.exit(1)

    # Calculate week based on start date or portal
    try:
        start_date = datetime.datetime.strptime(creds["start_date"], "%Y-%m-%d").date()
        calculated_minggu = calculate_week(target_date, start_date, base_week=1)
    except Exception:
        calculated_minggu = profile.get("minggu", 1)

    active_minggu = max(calculated_minggu, profile.get("minggu", 1))

    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Mahasiswa: {profile.get('nama')} ({profile.get('nrp')}) | Minggu: {active_minggu}")

    for sess_type, sess_label, jam_m, jam_s in sessions_to_run:
        print(f"\n--- Memproses Sesi {sess_label} ({jam_m} - {jam_s}) untuk {format_date_id(target_date)} ---")
        
        narrative = synthesize_activity(
            target_date=target_date,
            domain=creds["domain"],
            session_type=sess_type,
            config=config,
            explicit_text=args.text
        )

        print(f"Narasi: {narrative[:90]}...")

        res = submit_logbook(
            session=session,
            profile=profile,
            target_date=target_date,
            jam_mulai=jam_m,
            jam_selesai=jam_s,
            kegiatan=narrative,
            minggu=active_minggu,
            session_label=sess_label,
            history_file=HISTORY_FILE,
            check_existing=not args.force,
            timeout=config.get("settings", {}).get("request_timeout", 45)
        )

        if res.get("already_exists"):
            print(f"[STATUS] Sesi {sess_label} tanggal {target_date} SUDAH TERCATAT sebelumnya di Online MIS. Dilewati.")
        elif res.get("success"):
            print(f"[SUKSES] Logbook Sesi {sess_label} berhasil disimpan ke Online MIS!")
        else:
            print(f"[GAGAL] Gagal menyimpan logbook ke Online MIS (HTTP {res.get('http_status')}).")

        # Dispatch notifications
        dispatch_notification(
            result=res,
            profile=profile,
            telegram_token=creds["telegram_token"],
            telegram_chat_id=creds["telegram_chat_id"],
            discord_webhook_url=creds["discord_webhook"]
        )

def main():
    parser = argparse.ArgumentParser(description="PENS Kerja Praktek (KP) Automated Logbook Sentinel")
    subparsers = parser.add_subparsers(dest="command", help="Perintah operasi")

    # Command: setup
    subparsers.add_parser("setup", help="Wizard instalasi interaktif untuk konfigurasi akun & sistem")

    # Command: test-login
    subparsers.add_parser("test-login", help="Uji koneksi dan otentikasi login ke PENS CAS")

    # Command: preview
    p_preview = subparsers.add_parser("preview", help="Lihat preview narasi kegiatan yang akan dibuat")
    p_preview.add_argument("--date", help="Tanggal target (YYYY-MM-DD)")
    p_preview.add_argument("--domain", help="Bidang kerja (software, network, general)")

    # Command: read-portal
    p_read = subparsers.add_parser("read-portal", help="Baca data logbook yang sudah tercatat di Online MIS")
    p_read.add_argument("--week", type=int, help="Nomor minggu yang ingin dibaca")

    # Command: status
    subparsers.add_parser("status", help="Lihat riwayat pengisian lokal")

    # Command: run
    p_run = subparsers.add_parser("run", help="Jalankan pengisian logbook otomatis")
    p_run.add_argument("--session", choices=["auto", "morning", "afternoon", "all"], default="auto", help="Sesi kerja")
    p_run.add_argument("--date", help="Tanggal pengisian (YYYY-MM-DD, default hari ini)")
    p_run.add_argument("--text", help="Narasi kustom spesifik untuk hari ini")
    p_run.add_argument("--force", action="store_true", help="Abaikan pemeriksaan data eksisting (paksa simpan)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "setup":
        command_setup(args)
    elif args.command == "test-login":
        command_test_login(args)
    elif args.command == "preview":
        command_preview(args)
    elif args.command == "read-portal":
        command_read_portal(args)
    elif args.command == "status":
        command_status(args)
    elif args.command == "run":
        command_run(args)

if __name__ == "__main__":
    main()
