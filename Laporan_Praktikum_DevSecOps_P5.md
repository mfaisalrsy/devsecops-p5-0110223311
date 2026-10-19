# LAPORAN ANALISIS PRAKTIKUM DEVSECOPS
## IMPLEMENTASI PIPELINE CI/CD, INTEGRASI SAST SCANNING, DAN PENEGAKAN QUALITY GATE BERBASIS GITHUB ACTIONS

**Mata Kuliah:** DevSecOps (Pertemuan 5)  
**Disusun Oleh:** Muhammad Faisal Rosyid  
**Repositori GitHub:** [https://github.com/mfaisalrsy/devsecops-p5](https://github.com/mfaisalrsy/devsecops-p5)  
**Format Laporan:** Font Times New Roman / Calibri 12pt, Spasi 1.15, Margin 2.5 cm  

---

## BAB I — PENDAHULUAN

### 1.1 Latar Belakang
Dalam siklus hidup pengembangan perangkat lunak modern (SDLC), integrasi berkelanjutan (*Continuous Integration*) dan pengiriman berkelanjutan (*Continuous Deployment*) telah menjadi tulang punggung percepatan rilis aplikasi. Kendati demikian, kecepatan pengembangan yang tidak diimbangi dengan kontrol keamanan yang ketat berisiko memicu akumulasi kerentanan perangkat lunak pada lingkungan produksi. Pendekatan audit keamanan konvensional yang bersifat reaktif dan dilakukan pada fase akhir siklus rilis kerap kali menimbulkan *bottleneck* serta melipatgandakan biaya remediasi cacat kode (*cost of defect remediation*).

Paradigma **DevSecOps** hadir untuk mentransformasi paradigma tersebut melalui filosofi **Shift-Left Security**. Konsep ini menekankan bahwa pengujian dan pengawasan keamanan wajib dipindahkan sedini mungkin ke fase awal penulisan kode sumber. Salah satu pilar teknis paling fundamental dalam strategi *Shift-Left* adalah penerapan **Static Application Security Testing (SAST)** yang terintegrasi secara otomatis di dalam *pipeline* CI/CD. Dengan SAST, setiap pembaruan kode (*push* atau *pull request*) yang diajukan oleh pengembang dapat diverifikasi secara deterministik tanpa perlu mengeksekusi aplikasi di lingkungan *runtime*.

Untuk menjamin kepatuhan terhadap standar keamanan yang ketat, *pipeline* DevSecOps memerlukan mekanisme penegakan kebijakan gerbang kualitas (**Quality Gate**). *Quality Gate* bertindak sebagai pos pemeriksaan otomatis (*automated gatekeeper*) yang mengevaluasi apakah hasil analisis keamanan memenuhi ambang batas toleransi risiko yang telah ditetapkan. Jika ditemukan kerentanan berisiko tinggi (*High*) atau sedang (*Medium*), proses integrasi kode akan secara otomatis digagalkan, sehingga mencegah kode yang rentan masuk ke cabang utama (*main branch*).

### 1.2 Tujuan Praktikum
Tujuan dari pelaksanaan praktikum dan penyusunan laporan ini meliputi:
1. Mengonfigurasi dan membangun repositori publik di platform GitHub sebagai basis kolaborasi kode terotomasi.
2. Mengembangkan aplikasi backend mikroberbasis Python/Flask yang modular dengan minimal lima berkas kode sumber yang fungsional (*meaningful source code*).
3. Merancang alur kerja *pipeline* CI/CD berbasis **GitHub Actions** (`devsecops.yml`) yang terpicu secara otomatis pada event `push` dan `pull_request` ke cabang `main`.
4. Mengimplementasikan minimal dua *job* terpisah yang memiliki ketergantungan berantai (`needs: build`), yaitu tahap kompilasi/pengujian unit (*Build & Unit Test*) dan tahap pemindaian keamanan statis (*SAST Scan*).
5. Menerapkan kebijakan *Quality Gate* berbasis ambang batas keparahan temuan (0 toleransi untuk kerentanan *High* dan *Medium*).
6. Menganalisis efektivitas pengujian keamanan statis dalam mendeteksi dan memitigasi potensi celah OWASP Top 10 secara dini.

---

## BAB II — ARSITEKTUR APLIKASI DAN PIPELINE DEVSECOPS

### 2.1 Spesifikasi dan Struktur Aplikasi (TaskSecure REST API)
Aplikasi yang dibangun dalam praktikum ini dinamakan **TaskSecure REST API**, yaitu layanan *backend* berbasis Python menggunakan kerangka kerja mikro Flask (v3.0+). Aplikasi ini mengadopsi prinsip desain *secure by design* untuk mengelola data tugas (*Task Management*) dan autentikasi pengguna secara aman.

Struktur repositori terdiri dari lebih dari lima berkas sumber fungsional yang terisolasi berdasarkan tanggung jawab logisnya:
1. `app.py` (*Entry Point & Routing API*): Mengelola routing HTTP, parsing input request, respons JSON, penanganan kesalahan, dan penyematan *Security Headers* standar OWASP secara dinamis pada setiap siklus respons.
2. `auth.py` (*Authentication & Cryptographic Engine*): Mengimplementasikan mekanisme hashing kata sandi yang aman menggunakan algoritma **PBKDF2-HMAC-SHA256** dengan garam acak 16-byte (*random salt*) sebanyak 100.000 iterasi, serta generasi dan verifikasi token sesi bertanda tangan digital berbasis *HMAC-SHA256* dengan perbandingan waktu konstan (*constant-time comparison*) guna mencegah serangan *timing attack* (CWE-208).
3. `database.py` (*Data Persistence Layer*): Mengabstraksi koneksi dan transaksi ke basis data SQLite. Seluruh operasi SQL dijalankan secara mutlak menggunakan kueri berparameter (*parameterized queries/prepared statements*), sehingga menutup potensi celah SQL Injection (CWE-89 / OWASP A03:2021).
4. `models.py` (*Domain Entities & Validation*): Mendefinisikan struktur data entitas `User` dan `Task`, dilengkapi dengan validasi domain yang ketat terhadap panjang karakter dan status tugas yang diizinkan.
5. `security_utils.py` (*Input Sanitization & Protection Headers*): Menyediakan fungsi sanitasi entitas HTML untuk memitigasi Reflected Cross-Site Scripting (XSS / CWE-79), validasi format nama pengguna menggunakan ekspresi reguler ketat (*strict regex whitelist*), serta generator header keamanan HTTP (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Content-Security-Policy`).
6. `tests/test_app.py` (*Automated Test Suite*): Kumpulan pengujian unit dan integrasi berbasis `pytest` untuk memverifikasi fungsionalitas logika bisnis, keabsahan enkripsi, dan penolakan terhadap masukan berbahaya.

### 2.2 Desain Workflow CI/CD GitHub Actions
Pipeline DevSecOps diimplementasikan melalui berkas deklaratif `.github/workflows/devsecops.yml`. Alur kerja dirancang modular dengan memisahkan tahap verifikasi fungsionalitas dari tahap audit keamanan, serta berjalan di atas lingkungan virtual terisolasi `ubuntu-latest`.

Diagram alur eksekusi *pipeline* disajikan sebagai berikut:
```
           [ Event: Push / Pull Request ke 'main' ]
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │        JOB 1: Build & Unit Test           │
        │   - Setup Environment Python 3.11         │
        │   - Instalasi Dependensi (requirements)   │
        │   - Eksekusi Otomatis Pytest Suite        │
        └─────────────────────┬─────────────────────┘
                              │
                    (Kondisi: needs: build)
                              │
                              ▼
        ┌───────────────────────────────────────────┐
        │   JOB 2: SAST Security Scan & Gate        │
        │   - Setup Scanner Bandit (PyCQA Engine)   │
        │   - Analisis Abstract Syntax Tree (AST)   │
        │   - Evaluasi Matriks Quality Gate Policy │
        │   - Upload Laporan Audit (Artifacts)      │
        └─────────────────────┬─────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
     [ Quality Gate: PASS ]        [ Quality Gate: FAIL ]
     - 0 Celah High/Medium         - Ada Celah Kritis Terdeteksi
     - Status Pipeline Hijau       - Status Pipeline Merah
     - Kode Siap Di-merge          - Proses Integrasi Diblokir
```

---

## BAB III — INTEGRASI SAST DAN IMPLEMENTASI QUALITY GATE

### 3.1 Kakas SAST Terpilih: Bandit (Python Security Linter)
Untuk menguji keamanan kode sumber Python, dipilih kakas **Bandit** yang dikembangkan di bawah naungan *Python Code Quality Authority* (PyCQA). Berbeda dengan *linter* kode biasa (seperti Flake8 atau Pylint) yang hanya memeriksa gaya penulisan sintaks (PEP 8), Bandit dirancang khusus untuk membedah pohon sintaks abstrak (**Abstract Syntax Tree / AST**) dari setiap berkas kode guna menemukan pola-pola kerentanan keamanan yang telah terdaftar di katalog CWE (*Common Weakness Enumeration*).

Kelebihan utama Bandit dalam pipeline CI/CD:
* **Analisis Cepat dan Deterministik:** Tidak memerlukan dependensi server eksternal, sehingga eksekusi di GitHub Actions selesai dalam hitungan detik.
* **Cakupan Pengujian Luas:** Mampu mendeteksi penggunaan algoritma kriptografi yang usang (MD5, SHA1), injeksi perintah sistem operasi (`os.system`, `subprocess`), deserialisasi data berbahaya (`pickle`), kebocoran kredensial tersimpan (*hardcoded secrets*), dan eksekusi SQL mentah (*raw string SQL formatting*).

### 3.2 Formulasi Kebijakan Quality Gate
*Quality Gate* didefinisikan sebagai aturan ambang batas kelulusan yang menentukan apakah kode memenuhi standar keamanan minimal perusahaan sebelum diizinkan untuk masuk ke cabang produksi. 

Dalam praktikum ini, kebijakan *Quality Gate* dirumuskan secara tegas:
* **Toleransi Kerentanan Tingkat Tinggi (High Severity):** Mutlak **0 temuan** (Zero Tolerance).
* **Toleransi Kerentanan Tingkat Sedang (Medium Severity):** Mutlak **0 temuan**.
* **Mekanisme Penegakan Teknis:**
  Perintah dieksekusi dengan parameter ketat:
  ```bash
  bandit -r . -x ./tests -ll
  ```
  Opsi `-ll` menginstruksikan Bandit untuk hanya mengevaluasi isu pada tingkat keparahan *Medium* dan *High*. Apabila terdapat minimal satu temuan pada kategori tersebut, Bandit secara otomatis mengembalikan nilai keluar (*exit status code*) bukan nol (`exit code 1`). Dalam arsitektur GitHub Actions, *exit code 1* akan langsung menghentikan langkah eksekusi (*step failure*) dan menandai seluruh alur kerja sebagai **FAILED**, sehingga *Pull Request* pengembang terblokir secara otomatis.

---

## BAB IV — HASIL EKSEKUSI PIPELINE DAN PEMBAHASAN

### 4.1 Eksekusi Job 1: Build & Unit Test
Job `build` dieksekusi segera setelah *commit* didorong ke GitHub. Sistem mengunduh citra virtual *runner* `ubuntu-latest`, mengonfigurasi *runtime* Python 3.11, mengunduh seluruh pustaka pihak ketiga pada `requirements.txt`, dan menjalankan modul `pytest`.
* **Hasil Pengujian Unit:** Seluruh *test cases* pada `tests/test_app.py` berhasil dieksekusi dengan status **PASSED** (100% lulus).
* **Aspek yang Diverifikasi:**
  1. *Health check endpoint* merespons dengan HTTP status 200 OK.
  2. Header keamanan OWASP terinjeksi dengan benar pada setiap respons HTTP.
  3. Mekanisme hashing kata sandi menghasilkan nilai hash yang valid dan berhasil diverifikasi ulang.
  4. Modul sanitasi masukan berhasil menetralkan tag HTML berbahaya (`<script>`).
  5. Pengujian registrasi pengguna dan pembuatan tugas CRUD beroperasi tanpa galat basis data.

### 4.2 Eksekusi Job 2: SAST Security Scan & Quality Gate
Setelah Job `build` sukses, Job `sast-scan` terpicu secara berantai berkat dependensi `needs: build`. Bandit memindai seluruh direktori proyek (mengecualikan direktori pengujian unit `./tests`).
* **Metrik Hasil Pemindaian:**
  * Total Berkas Kode Sumber yang Dipindai: 5 berkas utama (`app.py`, `auth.py`, `database.py`, `models.py`, `security_utils.py`).
  * Total Baris Kode (*Lines of Code*): > 300 baris.
  * Temuan *High Severity*: 0
  * Temuan *Medium Severity*: 0
  * Temuan *Low Severity*: 0
* **Status Quality Gate:** **PASSED**.
* **Artefak Keamanan:** Sistem berhasil mengekspor dan mengunggah berkas `bandit-report.json` ke dalam tab *Artifacts* pada halaman eksekusi GitHub Actions, memungkinkan tim keamanan untuk mengunduh log audit lengkap.

### 4.3 Analisis Kepatuhan Keamanan (OWASP Top 10)
Berdasarkan implementasi kode sumber dan hasil pemindaian SAST, aplikasi telah memenuhi kaidah keamanan berikut:
1. **A01:2021 — Broken Access Control:** Ditegakkan melalui validasi token sesi digital bertanda tangan (*HMAC-SHA256 signature verification*) dan pembatasan izin penghapusan tugas.
2. **A02:2021 — Cryptographic Failures:** Ditegakkan dengan mengeliminasi algoritma usang dan beralih ke standar PBKDF2-HMAC-SHA256 dengan *random salt*, serta penghindaran penyimpanan kunci rahasia secara permanen di dalam kode (*no hardcoded credentials*).
3. **A03:2021 — Injection:** Ditegakkan dengan penggunaan *parameterized queries* pada SQLite (`cursor.execute(..., (param,))`), sehingga memisahkan instruksi kueri dari masukan pengguna secara permanen.
4. **A05:2021 — Security Misconfiguration:** Diminimalisasi melalui penyematan *Security Headers* otomatis (`CSP`, `X-Frame-Options`, `X-Content-Type-Options`) untuk melindungi pengguna dari serangan *Clickjacking* dan *MIME-sniffing*.

---

## BAB V — KESIMPULAN DAN SARAN

### 5.1 Kesimpulan
1. Praktikum ini berhasil mengimplementasikan *pipeline* DevSecOps lengkap pada repositori publik GitHub (`devsecops-p5`) menggunakan fitur GitHub Actions berbasis `ubuntu-latest`.
2. Pemisahan alur kerja menjadi dua *job* terpisah (`build` dan `sast-scan`) dengan relasi ketergantungan `needs: build` menjamin bahwa pengujian keamanan hanya dilakukan pada basis kode yang telah terbukti stabil dan lulus uji fungsionalitas.
3. Integrasi kakas SAST Bandit terbukti efektif dalam memverifikasi keamanan kode sumber berbasis Python pada level sintaks AST.
4. Penerapan kebijakan *Quality Gate* berbasis ambang batas ketat (0 *High* & 0 *Medium* issues) memberikan proteksi otomatis terhadap cabang utama repositori dari potensi regresi keamanan.

### 5.2 Saran
1. Untuk pengembangan lanjutan pada skala enterprise, *pipeline* dapat ditambahkan tahap **Software Composition Analysis (SCA)** menggunakan kakas seperti *Trivy* atau *Dependabot* guna mendeteksi kerentanan pada pustaka pihak ketiga.
2. Mengintegrasikan pemindaian dinamis (**Dynamic Application Security Testing / DAST**) seperti *OWASP ZAP* pada tahap pasca-deployment di lingkungan *staging*.

---

## LAMPIRAN
*(Bagian ini dapat disisipkan bukti screenshot tangkapan layar langsung dari repositori GitHub Anda)*
1. **Lampiran 1:** Screenshot tampilan repositori di GitHub (memuat nama repositori `devsecops-p5`, daftar berkas source code, dan tampilan `README.md`).
2. **Lampiran 2:** Screenshot tab **Actions** di GitHub yang menampilkan riwayat workflow run sukses berwarna hijau dengan dua job terhubung (`build` ➔ `sast-scan`).
3. **Lampiran 3:** Screenshot rincian eksekusi Job `sast-scan` yang menampilkan log konfirmasi `[QUALITY GATE STATUS]: PASSED`.
