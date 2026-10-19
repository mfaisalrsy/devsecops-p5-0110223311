# TaskSecure REST API 🛡️

[![DevSecOps Pipeline](https://github.com/mfaisalrsy/devsecops-p5/actions/workflows/devsecops.yml/badge.svg)](https://github.com/mfaisalrsy/devsecops-p5/actions/workflows/devsecops.yml)
[![SAST: Bandit](https://img.shields.io/badge/SAST-Bandit-blue.svg)](https://github.com/PyCQA/bandit)
[![Python: 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Repository ini dibangun untuk memenuhi tugas praktikum mata kuliah **DevSecOps** (Pertemuan 5) mengenai implementasi pipeline CI/CD otomatis, pengujian keamanan statis (**Static Application Security Testing / SAST**), dan penegakan kebijakan gerbang kualitas (**Quality Gate**).

---

## 1. Nama Aplikasi & Fungsinya
* **Nama Aplikasi:** `TaskSecure REST API`
* **Fungsi Aplikasi:**
  `TaskSecure REST API` adalah layanan *backend microservice* yang menyediakan fungsionalitas manajemen tugas (*Task Management*) dan autentikasi pengguna secara aman (*secure by design*). Fitur-fitur utama meliputi:
  * **User Management & Authentication:** Registrasi dan login pengguna dengan hashing kata sandi berbasis *PBKDF2-HMAC-SHA256* dan token sesi bertanda tangan digital (*HMAC-SHA256 signature*).
  * **Task Management (CRUD):** Pembuatan, pembacaan, dan penghapusan data tugas menggunakan kueri berparameter (*parameterized queries*) untuk memitigasi serangan SQL Injection (CWE-89).
  * **Input Sanitization & Security Headers:** Sanitasi otomatis terhadap entitas HTML guna mencegah Cross-Site Scripting (XSS / CWE-79) serta penyematan *Security Headers* standar OWASP (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`).
  * **Health Check Endpoint:** Endpoint `/api/health` untuk memantau status operasional service secara real-time.

---

## 2. Bahasa & Framework yang Digunakan
* **Bahasa Pemrograman:** Python (versi 3.11+)
* **Framework Web:** Flask (v3.0+)
* **Database Engine:** SQLite (dengan driver native `sqlite3` dan isolasi *parameterized statements*)
* **Testing Framework:** `pytest` (v8.0+)
* **SAST Security Scanner:** `Bandit` (v1.7+) dari Python Code Quality Authority (PyCQA)
* **CI/CD Platform:** GitHub Actions dengan runner `ubuntu-latest`

### Struktur Berkas Source Code (5+ File Inti)
Aplikasi ini memiliki arsitektur modular dengan berkas sumber yang fungsional dan terstruktur rapi:
```text
devsecops-p5/
├── .github/
│   └── workflows/
│       └── devsecops.yml       # Konfigurasi Pipeline GitHub Actions (Build & SAST)
├── tests/
│   └── test_app.py             # Berkas Unit & Integration Testing (Pytest)
├── app.py                      # File 1: Entry Point & Routing API Flask
├── auth.py                     # File 2: Modul Autentikasi & Hashing PBKDF2-SHA256
├── database.py                 # File 3: Layer Akses Basis Data (Parameterized Queries)
├── models.py                   # File 4: Model Data & Validasi Domain (User & Task)
├── security_utils.py           # File 5: Utilitas Sanitasi Input & Security Headers
├── requirements.txt            # Dependensi Aplikasi & Testing
├── .gitignore                  # Pengecualian Berkas Repositori
└── README.md                   # Dokumentasi Resmi Proyek
```

---

## 3. Cara Menjalankan Aplikasi

### Prasyarat
* Python 3.10 atau versi lebih baru terpasang di sistem.
* Git terpasang di sistem.

### Langkah-Langkah Instalasi & Menjalankan Lokal

1. **Clone repositori ini:**
   ```bash
   git clone https://github.com/mfaisalrsy/devsecops-p5.git
   cd devsecops-p5
   ```

2. **Buat dan aktifkan virtual environment (direkomendasikan):**
   * Di Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * Di Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```

3. **Install seluruh dependensi:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Jalankan unit test secara lokal:**
   ```bash
   pytest -v
   ```

5. **Jalankan pemindaian keamanan SAST lokal (Bandit):**
   ```bash
   bandit -r . -x ./tests -ll
   ```

6. **Jalankan server aplikasi:**
   ```bash
   python app.py
   ```
   Aplikasi akan aktif di alamat: `http://127.0.0.1:5000`

7. **Uji endpoint health check:**
   ```bash
   curl http://127.0.0.1:5000/api/health
   ```
   *Response output:*
   ```json
   {
     "service": "TaskSecure API",
     "status": "healthy",
     "version": "1.0.0"
   }
   ```

---

## 4. Overview Pipeline CI/CD & DevSecOps yang Diimplementasikan

Pipeline DevSecOps diotomatisasi menggunakan **GitHub Actions** yang didefinisikan pada file [`.github/workflows/devsecops.yml`](.github/workflows/devsecops.yml). Pipeline ini mengadopsi prinsip **Shift-Left Security**, yaitu memverifikasi stabilitas fungsionalitas dan keamanan kode sedini mungkin sebelum diintegrasikan ke cabang utama (`main`).

### Alur Kerja (*Workflow Architecture*)
```
[ Developer Git Push / Pull Request ]
                 │
                 ▼
   ┌───────────────────────────┐
   │        JOB 1: BUILD       │
   │  - Setup Python 3.11      │
   │  - Install Dependencies   │
   │  - Run Pytest Unit Tests  │
   └─────────────┬─────────────┘
                 │ (needs: build)
                 ▼
   ┌───────────────────────────┐
   │     JOB 2: SAST-SCAN      │
   │  - Install Bandit Scanner │
   │  - Scan AST Source Code   │
   │  - Enforce Quality Gate   │
   │  - Upload Report Artifact │
   └─────────────┬─────────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
[ PASSED ✅ ]         [ FAILED ❌ ]
Build Sukses        Quality Gate Gagal
Merge Diizinkan     Merge Diblokir
```

### Penjelasan Rinci Tiap Job:

1. **Trigger Event:**
   Workflow secara otomatis terpicu pada setiap aktivitas:
   * `push` ke branch `main`.
   * `pull_request` yang menargetkan branch `main`.

2. **Job 1 — `build` (Build & Unit Testing):**
   * **Runner:** `ubuntu-latest`
   * **Aktivitas:** Mengunduh kode sumber, mengonfigurasi Python 3.11, menginstal seluruh pustaka yang terdaftar di `requirements.txt`, dan menjalankan rangkaian *unit tests* menggunakan `pytest`.
   * **Tujuan:** Memastikan bahwa tidak ada kesalahan sintaks (*syntax error*) dan seluruh logika bisnis berfungsi normal.

3. **Job 2 — `sast-scan` (Static Application Security Testing & Quality Gate):**
   * **Runner:** `ubuntu-latest`
   * **Dependency:** Menggunakan deklarasi `needs: build`, artinya pengujian keamanan hanya akan dijalankan apabila Job `build` telah berhasil 100% tanpa galat.
   * **Kakas SAST:** `Bandit` (menganalisis struktur AST Python untuk mengidentifikasi celah keamanan seperti kelemahan kriptografi, *hardcoded secrets*, injeksi perintah, dan kerentanan injeksi SQL).
   * **Quality Gate Policy:**
     * **Kriteria Ambang Batas:** Toleransi **0 temuan** dengan keparahan *High* atau *Medium* (`0 High & 0 Medium Severity Vulnerabilities`).
     * **Mekanisme Penegakan:** Dieksekusi melalui perintah `bandit -r . -x ./tests -ll`. Jika terdapat kerentanan berstatus Medium atau High, Bandit akan menghasilkan *exit code* bukan nol (`exit code 1`), yang secara otomatis menggagalkan pipeline dan memblokir integrasi kode ke branch produksi.
   * **Artifact Upload:** Laporan audit keamanan (`bandit-report.json`) diunggah secara otomatis ke *GitHub Workflow Artifacts* agar dapat diunduh untuk kebutuhan audit kepatuhan.

---
*Dibuat oleh: M. Faisal R. (NIM)*  
*Mata Kuliah DevSecOps — 2026*
