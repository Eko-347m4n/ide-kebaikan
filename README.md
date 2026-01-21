# ✨ Ide Kebaikan: Gamifikasi Karakter Berbasis AI

**Ide Kebaikan** adalah aplikasi interaktif berbasis Desktop (Kiosk) yang dirancang untuk lingkungan sekolah. Aplikasi ini bertujuan menanamkan kebiasaan positif pada siswa melalui gamifikasi. Siswa dapat login menggunakan pengenalan wajah (Face Recognition), menuliskan kebaikan yang mereka lakukan, dan mendapatkan skor serta umpan balik instan dari kecerdasan buatan (AI).

---

## 🚀 Fitur Utama

### 1. 📷 Smart Face Recognition & Liveness Detection
Sistem login tanpa password, cukup dengan wajah. Dilengkapi fitur keamanan tingkat lanjut:
*   **Liveness Challenge:** Mencegah pemalsuan menggunakan foto dengan tantangan interaktif (Senyum 😊, Kedip 😉, Buka Mulut 😮).
*   **Identity Locking:** Optimasi CPU cerdas yang mengunci identitas saat wajah stabil.
*   **Fast Search (KDTree):** Pencarian identitas super cepat ($O(\log N)$) menggunakan struktur data *KDTree*, mendukung ribuan siswa tanpa *lag*.

### 2. 🧠 AI Brain & NLP (Natural Language Processing)
Otak di balik penilaian ide kebaikan:
*   **Analisis Teks:** Menggunakan **TF-IDF** dan **KNN (K-Nearest Neighbors)** untuk mengklasifikasikan teks (Teman, Diri Sendiri, Lingkungan, atau Junk/Spam).
*   **Smart Scoring (SAW):** Metode *Simple Additive Weighting* untuk menghitung skor berdasarkan Kualitas Ide, Target Kebaikan, dan Panjang Teks.
*   **Anti-Plagiarisme:** Menggunakan algoritma **Jaccard Similarity** (pre-filter) dan **Sequence Matcher** untuk mendeteksi siswa yang mencontek ide temannya.
*   **Lazy Loading:** Model bahasa (Sastrawi) dimuat secara *lazy* agar aplikasi terbuka instan.

### 3. 🎮 Gamifikasi & Leaderboard
*   **Real-time Feedback:** Siswa mendapat respon unik dan motivasi berdasarkan kategori kebaikan mereka.
*   **Leaderboard:** Papan peringkat otomatis untuk memacu semangat berkompetisi dalam kebaikan.
*   **Streak System:** Mencatat konsistensi siswa dalam berbuat baik.

### 4. ⚡ High Performance Engineering
*   **Multithreaded Camera:** Pemrosesan visi komputer berjalan di thread terpisah, menjaga antarmuka (UI) tetap mulus di 60 FPS.
*   **Confusion Check:** Logika anti-ambiguitas untuk mencegah sistem salah mengenali dua wajah yang sangat mirip.

---

## 🛠️ Teknologi yang Digunakan

*   **Bahasa:** Python 3.10+
*   **GUI:** `customtkinter` (Modern UI)
*   **Computer Vision:** `opencv-python`, `dlib`, `face_recognition`
*   **AI/ML:** `scikit-learn` (KNN, KDTree, TF-IDF), `pandas`, `numpy`
*   **NLP:** `Sastrawi` (Stemming Bahasa Indonesia)
*   **Database:** SQLite3

---

## ⚙️ Instalasi & Cara Menjalankan

### Prasyarat
Pastikan Python 3.10 ke atas dan CMake sudah terinstall (untuk library `dlib`).

### 1. Clone Repository
```bash
git clone https://github.com/username/ide-kebaikan.git
cd ide-kebaikan
```

### 2. Install Dependensi
```bash
pip install -r requirements.txt
```
*Catatan: Instalasi `dlib` dan `face_recognition` mungkin memerlukan waktu beberapa menit untuk kompilasi C++.*

### 3. Jalankan Aplikasi
```bash
python app.py
```

---

## 📂 Struktur Proyek

```
ide-kebaikan/
├── app.py                  # Entry point utama aplikasi (GUI Controller)
├── core/                   # Logika Inti & Backend
│   ├── brain.py            # Logika AI, NLP, Database, dan Scoring
│   ├── camera_manager.py   # Pengelola Thread Kamera & Logika Game
│   ├── vision.py           # Pemrosesan Citra (Face Rec, Landmark, KDTree)
│   ├── constants.py        # Konfigurasi & Teks Statis
│   ├── rules.py            # Aturan Bahasa, Slang Dict, Feedback Bank
│   └── logger.py           # Sistem Logging Rotasi
├── ui/                     # Komponen Antarmuka (Pages)
│   ├── camera_page.py      # Tampilan Kamera
│   ├── input_page.py       # Input Teks Kebaikan
│   ├── result_page.py      # Tampilan Hasil & Skor
│   └── ...
├── data/                   # Penyimpanan Data
│   ├── kebaikan.db         # Database SQLite (User & Logs)
│   ├── training_data.csv   # Dataset awal untuk AI
│   ├── learned_data.csv    # Data baru yang dipelajari AI secara otomatis
│   └── rejected_data.csv   # Log input yang ditolak (spam/pendek)
└── logs/                   # Log sistem harian
```

---

## 🧠 Cara Kerja AI (Technical Deep Dive)

### Alur Visi (Vision Pipeline)
1.  **Capture:** Frame diambil dari webcam via Thread terpisah.
2.  **Detection:** `dlib` mendeteksi wajah.
3.  **Liveness:** Menghitung *Aspect Ratio* mata (untuk kedip) dan mulut (untuk senyum/buka mulut) berdasarkan 68 titik landmark wajah.
4.  **Recognition:**
    *   Jika wajah stabil, encoding 128-dimensi diekstrak.
    *   Sistem query ke **KDTree** untuk mencari tetangga terdekat (Nearest Neighbor).
    *   Jika jarak (Euclidean Distance) < 0.48, wajah dikenali.

### Alur Teks (Text Pipeline)
1.  **Preprocessing:** Normalisasi slang (sy -> saya), Stopword removal, Stemming.
2.  **Vectorization:** Mengubah teks menjadi angka menggunakan TF-IDF.
3.  **Prediction:** KNN memprediksi Kategori (Friend/Self/Enemy) dan Kualitas.
4.  **Scoring (SAW):**
    $$Score = (Level \times 0.5) + (Quality \times 0.3) + (Length \times 0.2) + RandomVar$$

---

## 🤝 Kontribusi
Proyek ini terbuka untuk pengembangan lebih lanjut. Silakan buat *Issue* atau *Pull Request* jika ingin menambahkan fitur baru.

---

**Dibuat dengan ❤️ untuk pendidikan Indonesia.**
