# Panduan Keamanan Kampus & Aturan Sanitasi WAF PENS

Portal **Online MIS PENS** (`online.mis.pens.ac.id`) dilindungi oleh sistem keamanan jaringan dan Web Application Firewall (WAF) kampus. Dokumen ini menjelaskan mekanisme perlindungan dan aturan penulisan narasi kegiatan agar request penyimpanan logbook tidak terblokir.

---

## 1. Mekanisme & Karakteristik WAF PENS

WAF kampus PENS melakukan inspeksi muatan (*deep packet inspection*) terhadap seluruh nilai formulir POST yang dikirimkan ke `entry_logbook_kp1.php`. 

Jika muatan teks mengandung pola yang menyerupai kueri SQL Injection atau karakter khusus tertentu, WAF akan secara otomatis memutus koneksi (HTTP 403 Forbidden atau silent connection drop).

### Kata Kunci & Karakter yang Rawan Memicu False Positive:
1. **Karakter Ampersand (`&`)**:
   * Sering digunakan sebagai pemisah parameter HTTP dalam form POST. Penggunaan karakter ini di dalam teks bebas dapat merusak struktur parsing payload atau memicu filter validasi input.
2. **Klausa Manipulasi Data SQL**:
   * `insert ` (contoh: "melakukan insert data...")
   * `select ` (contoh: "melakukan select kolom...")
   * `delete ` atau `hard delete` (contoh: "menjalankan script delete...")
   * `drop ` (contoh: "melakukan drop table...")
   * `union ` (contoh: "membuat union schema...")
   * `truncate ` (contoh: "melakukan truncate cache...")
   * `identity insert`

---

## 2. Solusi Otomatis: Sanitizer Bawaan Bot

Bot ini telah dilengkapi dengan modul **WAF Sanitizer** otomatis pada `core/generator.py` yang secara cerdas mendeteksi dan mengganti kata-kata rawan tersebut sebelum formulir dikirim ke server MIS.

Tabel penggantian terstandar:

| Kata Kunci Asli | Pengganti Akademik yang Aman |
| :--- | :--- |
| `&` | `dan` |
| `insert ` | `penyisipan ` |
| `identity insert` | `identity insersi` |
| `delete ` | `penghapusan ` |
| `hard delete` | `penghapusan permanen` |
| `soft delete` | `penonaktifan lunak` |
| `select ` | `pemilihan ` |
| `drop ` | `pelepasan ` |
| `union ` | `penggabungan ` |
| `truncate ` | `pengosongan ` |

---

## 3. Panduan Menulis Narasi Kegiatan Mandiri

Jika Anda menambahkan template kegiatan sendiri pada berkas `config.yaml` di bagian `custom_activities`, terapkan pedoman penulisan berikut:

1. **Gunakan Istilah Bahasa Indonesia yang Baku:**
   * Contoh: daripada menulis `"debugging error insert record"`, tulis `"melakukan pelacakan galat pada modul penyisipan data"`.
2. **Hindari Menempelkan Potongan Kode SQL / Bash Mentah:**
   * Jangan menyertakan perintah shell seperti `rm -rf`, `DROP TABLE`, atau simbol tanda kutip ganda berlebih di dalam kolom kegiatan.
3. **Format Awalan Tanggal:**
   * Awali narasi dengan format tanggal resmi berbahasa Indonesia (contoh: `25 September 2026 ...`) sesuai dengan konvensi pembimbing akademik PENS.
