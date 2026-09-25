# Panduan Pemasangan di Linux & macOS

Dokumen ini memandu langkah demi langkah pemasangan, konfigurasi, dan otomatisasi **PENS KP Logbook Sentinel** pada sistem operasi berbasis Linux (Ubuntu, Debian, Fedora, Arch) dan macOS (Apple Silicon M1/M2/M3 & Intel) menggunakan **Systemd Timer** atau **Cron**.

---

## 1. Persyaratan Sistem

* **Python 3.10+** dan `python3-venv`
* **Git**
* Hak akses internet langsung ke portal PENS MIS (`online.mis.pens.ac.id`) atau proxy pendukung jika di luar negeri.

Di Ubuntu/Debian, siapkan paket pendukung:
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git
```

Di macOS via Homebrew:
```bash
brew install python git
```

---

## 2. Kloning Repositori & Virtual Environment

```bash
# Kloning repositori
git clone https://github.com/prodhokter/pens-kp-bot.git ~/pens-kp-bot
cd ~/pens-kp-bot

# Buat dan aktifkan virtual environment
python3 -m venv venv
source venv/bin/activate

# Instalasi dependensi
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Konfigurasi Otomatis (Wizard)

Jalankan wizard interaktif untuk menghubungkan akun PENS Anda:

```bash
python3 main.py setup
```

Program akan memverifikasi login CAS, mengekstrak ID pendaftaran KP (`kp_daftar`) dan ID mahasiswa (`mahasiswa`) secara otomatis, lalu menyimpan berkas `.env` dan `config.yaml`.

---

## 4. Pengujian Awal

Pastikan seluruh fungsi berjalan lancar sebelum menjadwalkan:

```bash
# 1. Uji autentikasi CAS
python3 main.py test-login

# 2. Uji pratinjau narasi akademis
python3 main.py preview

# 3. Uji pengisian logbook hari ini
python3 main.py run
```

---

## 5. Otomatisasi Penjadwalan

Pilih salah satu metode penjadwalan sesuai lingkungan sistem Anda:

### Opsi A: Systemd Timer (Rekomendasi untuk Linux & VPS)
Metode ini paling andal karena memiliki fitur `Persistent=true` (jika komputer mati saat jam jadwal tiba, tugas akan segera dijalankan saat komputer menyala kembali).

Jalankan skrip pemasangan otomatis dengan hak akses sudo:
```bash
sudo ./scripts/setup_systemd.sh
```

Periksa status timer:
```bash
systemctl list-timers | grep pens-kp
```

Pantau log eksekusi secara real-time:
```bash
journalctl -u pens-kp.service -f
```

---

### Opsi B: Crontab (Untuk macOS atau Linux tanpa Systemd)
Buka editor crontab pengguna:
```bash
crontab -e
```

Tambahkan baris berikut untuk menjalankan pengisian otomatis setiap hari Senin sampai Jumat pada pukul 12:00 dan 16:00 WIB:

```cron
# PENS KP Logbook Sentinel: Sesi Siang (12:00 WIB) dan Sesi Sore (16:00 WIB)
0 12,16 * * 1-5 /bin/bash -c "cd $HOME/pens-kp-bot && ./scripts/run.sh >> $HOME/pens-kp-bot/cron.log 2>&1"
```

Jika jadwal kerja mencakup akhir pekan (Sabtu dan Minggu), ganti `1-5` menjadi `*`:
```cron
0 12,16 * * * /bin/bash -c "cd $HOME/pens-kp-bot && ./scripts/run.sh >> $HOME/pens-kp-bot/cron.log 2>&1"
```

---

## 6. Integrasi Notifikasi Telegram (Opsional)

Jika Anda ingin menerima laporan pengisian langsung di ponsel Anda via Telegram:
1. Hubungi `@BotFather` di Telegram untuk membuat bot baru dan dapatkan **Bot Token**.
2. Hubungi `@userinfobot` untuk mendapatkan **Chat ID** akun Anda.
3. Buka berkas `.env` dan isi variabel berikut:
   ```env
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
   TELEGRAM_CHAT_ID=987654321
   ```
Setiap kali pengisian logbook berhasil atau dilewati, bot akan otomatis mengirimkan laporan ringkas ke Telegram Anda.
