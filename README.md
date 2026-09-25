# PENS KP Logbook Sentinel

Sistem otomasi sinkronisasi dan pengisian logbook Kerja Praktek (KP) mahasiswa Politeknik Elektronika Negeri Surabaya (PENS) berbasis Central Authentication Service (CAS) dan Online MIS (`online.mis.pens.ac.id`).

Proyek ini dirancang agar dapat dipasang dan dijalankan secara mandiri pada berbagai perangkat (laptop Windows, macOS, maupun server Linux/VPS) dengan konfigurasi otomatis dan proteksi firewall kampus.

---

## Fitur Utama Sistem

* **Deteksi Metadata Otomatis (Zero-Manual-Lookup):**
  Melalui perintah `python main.py setup`, bot secara otomatis masuk ke SSO CAS PENS, memeriksa nomor minggu aktif, serta mengekstrak `kp_daftar`, `mahasiswa`, `NRP`, dan nama mahasiswa tanpa perlu memeriksa *inspect element* pada peramban web.
* **Dukungan Dual-Session & Single-Session:**
  Mendukung jadwal standar KP PENS 2 sesi per hari (Sesi Pagi 07:00-12:00 WIB dieksekusi pukul 12:00, dan Sesi Sore 13:00-16:00 WIB dieksekusi pukul 16:00), maupun mode tunggal (08:00-16:00 WIB).
* **Idempotency Guard:**
  Bot membaca tabel data historis pada server MIS sebelum mengirim formulir. Jika entri untuk tanggal dan jam mulai terkait sudah tercatat di sistem kampus, bot otomatis melewati pengiriman tanpa membuat duplikasi entri.
* **Sanitasi WAF Kampus (Anti-False-Positive):**
  Melindungi pengiriman data dari blokir Web Application Firewall PENS dengan secara otomatis mengganti istilah teknis manipulasi data SQL (seperti `insert`, `select`, `delete`, `drop`, `union`, dan simbol `&`) menjadi istilah akademis berbahasa Indonesia yang aman.
* **Bank Narasi Multi-Bidang:**
  Menyediakan kumpulan narasi kegiatan harian untuk bidang `software`, `network`, dan `general`, lengkap dengan pembedaan konteks hari kerja, hari Sabtu, dan hari Minggu.
* **Dukungan Berbagai Platform:**
  Dilengkapi skrip otomatisasi untuk **Windows Task Scheduler** (`run.bat`), **Linux Systemd Timer** (`setup_systemd.sh`), dan **macOS Crontab** (`run.sh`).
* **Laporan Notifikasi:**
  Dukungan pengiriman status ringkas pengisian logbook ke akun Telegram (via Telegram Bot API) atau kanal Discord (via Webhook).

---

## Struktur Direktori

```text
pens-kp-bot/
├── core/
│   ├── __init__.py
│   ├── auth.py              # Handler otentikasi PENS CAS & manajemen sesi HTTP
│   ├── client.py            # Pembaca tabel Online MIS & eksekutor submit form
│   ├── discovery.py         # Ekstraktor metadata mahasiswa & ID KP dari portal
│   ├── generator.py         # Generator narasi kegiatan harian & sanitizer WAF
│   └── notifier.py          # Pengirim laporan status ke Telegram dan Discord
├── docs/
│   ├── TUTORIAL_WINDOWS.md  # Panduan visual Windows & Task Scheduler
│   ├── TUTORIAL_LINUX_MAC.md# Panduan instalasi Ubuntu, Debian, dan macOS
│   └── WAF_GUIDELINES.md    # Aturan keamanan WAF kampus & pedoman teks kegiatan
├── scripts/
│   ├── run.bat              # Runner otomatis untuk Windows Task Scheduler
│   ├── run.sh               # Runner otomatis untuk Linux dan macOS
│   └── setup_systemd.sh     # Pemasang service dan timer systemd otomatis di Linux
├── .env.example             # Template variabel lingkungan
├── config.example.yaml      # Template konfigurasi jam kerja dan bank narasi
├── main.py                  # Antarmuka CLI utama
├── requirements.txt         # Dependensi Python
└── LICENSE                  # Lisensi perangkat lunak MIT
```

---

## Panduan Instalasi Cepat

### 1. Kloning Repositori
```bash
git clone https://github.com/prodhokter/pens-kp-bot.git
cd pens-kp-bot
```

### 2. Pasang Virtual Environment & Dependensi
Di Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Di Windows (Command Prompt):
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Jalankan Wizard Pengaturan Otomatis
```bash
python main.py setup
```
Masukkan **PENS NetID** (contoh: `user@student.pens.ac.id`) dan **Kata Sandi**. Script akan melakukan uji koneksi, mengekstrak data pendaftaran KP Anda, dan membuat berkas konfigurasi `.env` dan `config.yaml` secara otomatis.

---

## Referensi Perintah CLI (`main.py`)

| Perintah | Fungsi | Contoh Penggunaan |
| :--- | :--- | :--- |
| `setup` | Menjalankan wizard konfigurasi interaktif awal | `python main.py setup` |
| `test-login` | Menguji koneksi akun ke CAS dan menampilkan data mahasiswa | `python main.py test-login` |
| `preview` | Melihat contoh narasi kegiatan hari ini tanpa mengirim ke portal | `python main.py preview --domain software` |
| `run` | Menjalankan proses pengisian logbook ke Online MIS | `python main.py run` |
| `run --session` | Menjalankan sesi spesifik (`morning`, `afternoon`, atau `all`) | `python main.py run --session morning` |
| `read-portal` | Membaca tabel entri yang sudah tercatat di server MIS | `python main.py read-portal` |
| `status` | Melihat riwayat pengisian lokal pada berkas `logbook_history.json` | `python main.py status` |

---

## Panduan Otomatisasi Penjadwalan

### A. Windows (Task Scheduler - 1-Klik)
Cukup buka **Command Prompt as Administrator** dan jalankan:
```cmd
scripts\install_windows_task.bat
```
Masukkan jam eksekusi yang diinginkan (contoh: `16:15` WIB). Skrip akan otomatis mendaftarkan tugas ke Windows Task Scheduler dengan fitur **Catch-Up**: jika laptop Anda dalam keadaan mati atau tertidur (*sleep*) saat jam jadwal tiba, Windows akan otomatis mengeksekusi pengisian logbook sesegera mungkin saat laptop dinyalakan kembali.

Panduan konfigurasi manual tersedia di `docs/TUTORIAL_WINDOWS.md`.

---

## 4 Pilihan Sumber Keterangan / Narasi Kegiatan

Pada berkas `config.yaml`, teman Anda dapat menentukan dari mana bot mengambil narasi kegiatan logbook harian via parameter `activity_source.type`:

| Pilihan Sumber | Parameter `type` | Cara Kerja & Keunggulan |
| :--- | :--- | :--- |
| **1. Bank Otomatis** | `bank` *(Default)* | **Nol Konfigurasi Tambahan.** Bot otomatis memilih kalimat narasi akademis formal dari bank template bidang kerja (`software`, `network`, `it_support`, `general`). |
| **2. Berkas Teks** | `file` | Membaca draft kalimat dari file `kegiatan.txt` (bisa per tanggal atau daftar baris acak). Contoh format tersedia di `kegiatan.example.txt`. |
| **3. AI Generator** | `ai` | Menggunakan Google Gemini API / Groq API gratis. Bot membuat 2-3 kalimat baru yang bervariasi setiap hari sesuai peran dan nama perusahaan tanpa repetisi. |
| **4. Git Repository** | `git` | Mengekstrak ringkasan pesan commit git harian jika teman Anda aktif mengerjakan proyek pemrograman. |

---

## Penyesuaian Hari & Jam Kerja (`config.yaml`)

Teman Anda dapat mengatur hari apa saja bot aktif mengisi dan rentang jam kerja di `config.yaml`:
```yaml
settings:
  mode: single # 'single' (1x sehari) atau 'dual' (2x sehari)
  
  # Hari aktif pengisian (contoh: Senin sampai Jumat saja)
  active_days:
    - monday
    - tuesday
    - wednesday
    - thursday
    - friday

schedule:
  single:
    start_time: "08:00"
    end_time: "16:00"
    trigger_time: "16:15"
```

### B. Linux (Systemd Timer)
Untuk pengguna VPS atau Linux desktop:
```bash
sudo ./scripts/setup_systemd.sh
```
Skrip ini akan memasang unit `pens-kp.service` dan `pens-kp.timer` yang berjalan otomatis setiap hari pukul 12:00 dan 16:00.

### C. macOS & Linux (Crontab)
Buka crontab dengan perintah `crontab -e` dan tambahkan:
```cron
0 12,16 * * 1-5 /bin/bash -c "cd /path/ke/pens-kp-bot && ./scripts/run.sh >> cron.log 2>&1"
```

---

## Variabel Konfigurasi (`.env`)

```env
# Kredensial PENS CAS
PENS_NETID=namauser@student.pens.ac.id
PENS_PASSWORD=katasandimahasiswa

# Pengaturan Ekstraksi Otomatis (Dihasilkan oleh 'python main.py setup')
PENS_NRP=3124500000
PENS_MAHASISWA_ID=12345
PENS_KP_DAFTAR_ID=6789
PENS_TAHUN=2026
PENS_SEMESTER=1

# Mode Pengisian ('dual' atau 'single')
SUBMISSION_MODE=dual

# Bidang Kerja ('software', 'network', atau 'general')
ACTIVITY_DOMAIN=software

# Tanggal Mulai KP (YYYY-MM-DD)
KP_START_DATE=2026-08-31

# Proxy Jaringan (Opsional, kosongkan jika koneksi langsung dari Indonesia)
PROXY_URL=

# Notifikasi Telegram (Opsional)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Notifikasi Discord (Opsional)
DISCORD_WEBHOOK_URL=
```

---

## Penyelesaian Kendala (Troubleshooting)

1. **Otentikasi CAS Gagal (`NetID atau kata sandi tidak valid`):**
   * Pastikan format NetID sesuai akun resmi (contoh: `nama@student.pens.ac.id` atau `nama@it.student.pens.ac.id`).
   * Pastikan kata sandi tidak mengandung karakter kutip yang tidak ter-escape pada berkas `.env`.
2. **Koneksi Timeout saat Diakses dari Luar Negeri:**
   * Portal `online.mis.pens.ac.id` menerapkan geofencing pada beberapa blok IP luar negeri.
   * Jika bot dijalankan di VPS luar negeri, pasang Tor atau proxy SOCKS5 lokal Indonesia dan isi parameter `PROXY_URL=socks5h://127.0.0.1:9050`. Jika dijalankan di laptop lokal di Indonesia, kosongkan `PROXY_URL`.
3. **Data Sudah Tercatat Sebelumnya:**
   * Bot memiliki fitur proteksi duplikasi. Jika logbook sesi tersebut sudah ada di portal MIS, sistem akan menampilkan `[TERCATAT SEBELUMNYA]` dan tidak mengirim ulang. Gunakan argumen `--force` jika ingin memaksa penyimpanan ulang.

---

## Lisensi

Didistribusikan di bawah lisensi terbuka [MIT License](LICENSE).
