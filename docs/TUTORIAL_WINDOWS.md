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

## 6. Otomatisasi Harian via Windows Task Scheduler (1-Klik)

Agar logbook terisi otomatis setiap hari kerja tanpa perlu membuka terminal atau klik tombol apapun, gunakan skrip pemasang otomatis yang telah disediakan:

### Cara 1-Klik (Rekomendasi Utama):
1. Buka **Command Prompt (CMD)** sebagai **Administrator** (klik kanan icon CMD -> *Run as administrator*).
2. Arahkan ke folder proyek:
   ```cmd
   cd /d %USERPROFILE%\Documents\pens-kp-bot
   ```
3. Jalankan skrip pemasang otomatis:
   ```cmd
   scripts\install_windows_task.bat
   ```
4. Masukkan jam eksekusi harian yang Anda inginkan (contoh: `16:15` atau tekan `Enter` untuk default).

### Keunggulan Fitur Catch-Up Otomatis:
Skrip ini secara otomatis mengaktifkan fitur `StartWhenAvailable`. Artinya:
* **Jika laptop Anda sedang mati atau dalam mode Sleep/Tertidur pada pukul 16:15:**
  Begitu laptop Anda dinyalakan kembali (misalnya malam hari jam 19:00 atau keesokan paginya), Windows akan **langsung mengeksekusi pengisian logbook hari tersebut secara otomatis di latar belakang** tanpa interupsi.
* **Tetap berjalan saat memakai baterai:** Penjadwal tidak akan tertunda meskipun laptop sedang tidak terhubung ke charger.

---

## 7. Mengatur Sumber Keterangan Kegiatan Logbook

Di dalam berkas `config.yaml`, teman Anda dapat memilih bagaimana narasi kegiatan logbook diisi:

| Tipe Sumber | Nilai `activity_source.type` | Deskripsi & Cara Kerja |
| :--- | :--- | :--- |
| **1. Bank Otomatis** | `bank` *(Default)* | **100% Otomatis tanpa ketik apapun.** Bot akan memilih narasi akademis formal secara bergantian dari bank template bidang yang dipilih (`software`, `network`, `it_support`, `general`). |
| **2. Berkas Teks** | `file` | Membaca dari berkas `kegiatan.txt`. Teman Anda dapat menulis daftar kegiatan atau menetapkan tanggal spesifik (lihat `kegiatan.example.txt`). |
| **3. AI Generator** | `ai` | Menggunakan Google Gemini API gratis atau Groq API. Bot membuat 2-3 kalimat baru yang bervariasi setiap hari sesuai peran dan nama perusahaan. |
| **4. Git Repository** | `git` | Mengambil pesan commit git harian jika teman Anda mengerjakan proyek berbasis pemrograman. |

---

## 8. Pemantauan & Laporan

* Untuk melihat riwayat pengisian lokal:
  ```cmd
  python main.py status
  ```
* Untuk melihat tabel data yang sudah masuk di server PENS MIS:
  ```cmd
  python main.py read-portal
  ```
