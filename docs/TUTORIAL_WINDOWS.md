# Panduan Lengkap Pemasangan di Windows (Windows 10 & 11)

Dokumen ini memandu langkah demi langkah pemasangan, konfigurasi, dan otomatisasi **PENS KP Logbook Sentinel** pada komputer atau laptop berbasis sistem operasi Windows menggunakan **Windows Task Scheduler (Penjadwal Tugas)**.

---

## 1. Persyaratan Sistem

Pastikan perangkat Anda telah memenuhi kebutuhan dasar berikut:
* **Python 3.10 atau versi lebih baru**: Dapat diunduh melalui [python.org](https://www.python.org/downloads/).
  > **PENTING saat instalasi Python:** Beri centang pada opsi **"Add python.exe to PATH"** di halaman pertama installer sebelum menekan tombol *Install Now*.
* **Git for Windows**: Dapat diunduh melalui [git-scm.com](https://git-scm.com/download/win).
* Akun login resmi PENS CAS (NetID email student dan kata sandi).

---

## 2. Kloning Repositori & Persiapan Direktori

Buka **Command Prompt (CMD)** atau **PowerShell**, lalu jalankan perintah berikut:

```cmd
:: Pindah ke folder tempat Anda ingin menyimpan proyek (misal Documents)
cd /d %USERPROFILE%\Documents

:: Kloning repositori dari GitHub
git clone https://github.com/prodhokter/pens-kp-bot.git
cd pens-kp-bot
```

---

## 3. Pembuatan Virtual Environment & Instalasi Dependensi

Jalankan perintah berikut di dalam folder `pens-kp-bot`:

```cmd
:: Buat virtual environment bernama 'venv'
python -m venv venv

:: Aktifkan virtual environment
venv\Scripts\activate

:: Perbarui pip dan instal seluruh dependensi
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika berhasil, terminal Anda akan menampilkan awalan `(venv)`.

---

## 4. Menjalankan Wizard Konfigurasi Otomatis

Jalankan wizard instalasi interaktif:

```cmd
python main.py setup
```

Wizard akan memandu Anda secara otomatis:
1. Meminta **NetID** (contoh: `namaanda@student.pens.ac.id` atau `namaanda@it.student.pens.ac.id`).
2. Meminta **Kata Sandi PENS CAS**.
3. Meminta **Proxy URL** (tekan `Enter` untuk mengosongkan jika Anda berada di Indonesia / jaringan langsung).
4. Melakukan otentikasi ke PENS CAS dan otomatis mendeteksi:
   * Nama Lengkap & NRP Mahasiswa
   * ID Pendaftaran KP (`kp_daftar`)
   * ID Mahasiswa di Basis Data MIS (`mahasiswa`)
   * Tahun Akademik & Semester Aktif
   * Nomor Minggu KP Berjalan
5. Memilih **Mode Operasional**:
   * Pilihan `1`: Dual-Session (Pagi 07:00-12:00 dan Sore 13:00-16:00 - Standar PENS)
   * Pilihan `2`: Single-Session (1x sehari 08:00-16:00)
6. Memilih **Bidang Kerja**: `software`, `network`, atau `general`.

Semua data akan otomatis tersimpan rapi di berkas `.env` dan `config.yaml`.

---

## 5. Pengujian Manual

Sebelum mengaktifkan penjadwal otomatis, lakukan pengujian berikut:

### A. Uji Koneksi & Otentikasi
```cmd
python main.py test-login
```
*Pastikan terminal menampilkan status `[SUKSES] Otentikasi PENS CAS berhasil!` beserta data profil Anda.*

### B. Uji Preview Narasi
```cmd
python main.py preview
```
*Melihat contoh narasi kegiatan akademis yang akan diisikan ke portal hari ini.*

### C. Uji Eksekusi Riil
```cmd
python main.py run
```
*Script akan memeriksa tabel di Online MIS. Jika belum ada entri untuk sesi saat ini, script akan otomatis mengisikan logbook dan memverifikasi status penyimpanan.*

---

## 6. Otomatisasi Harian via Windows Task Scheduler

Agar logbook terisi otomatis setiap hari kerja tanpa perlu membuka terminal, pasang penjadwalan via **Windows Task Scheduler**:

### Langkah Pembuatan Task Sesi Siang (Pukul 12:05 WIB):
1. Tekan tombol `Windows + R`, ketik `taskschd.msc`, lalu tekan `Enter`.
2. Pada panel kanan, klik **Create Task...** (Buat Tugas).
3. **Tab General:**
   * Name: `PENS KP Logbook - Sesi Siang`
   * Beri centang pada opsi **Run whether user is logged on or not** (atau *Run only when user is logged on* jika tidak ingin diminta password Windows).
   * Beri centang **Run with highest privileges**.
4. **Tab Triggers:**
   * Klik **New...**
   * Begin the task: `On a schedule`
   * Pilih **Daily** (Harian), atur jam ke `12:05:00`.
   * Klik **OK**.
5. **Tab Actions:**
   * Klik **New...**
   * Action: `Start a program`
   * Program/script: `C:\Windows\System32\cmd.exe`
   * Add arguments: `/c "scripts\run.bat"`
   * Start in: Masukkan path lengkap folder proyek Anda, contoh: `C:\Users\NamaAnda\Documents\pens-kp-bot`
   * Klik **OK**.
6. **Tab Conditions:**
   * Hilangkan centang pada *Start the task only if the computer is on AC power* (agar tetap berjalan saat laptop menggunakan baterai).
   * Beri centang pada *Wake the computer to run this task* (opsional).
7. Klik **OK** untuk menyimpan.

### Langkah Pembuatan Task Sesi Sore (Pukul 16:05 WIB):
* Ulangi langkah di atas dengan nama `PENS KP Logbook - Sesi Sore` dan Trigger diatur pada jam `16:05:00`.

---

## 7. Pemantauan & Laporan

* Untuk melihat riwayat pengisian lokal:
  ```cmd
  python main.py status
  ```
* Untuk melihat tabel data yang sudah masuk di server PENS MIS:
  ```cmd
  python main.py read-portal
  ```
