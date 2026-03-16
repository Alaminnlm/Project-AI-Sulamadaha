# 🏖️ Sulamadaha AI - Chatbot Asisten Wisata

Sulamadaha AI adalah asisten virtual cerdas yang dirancang untuk membantu wisatawan menjelajahi keindahan Pantai Sulamadaha, Maluku Utara. Dibangun dengan framework Flask dan ditenagai oleh Google Gemini AI, aplikasi ini menawarkan pengalaman interaktif dengan antarmuka **Dark Glassmorphism** yang modern dan elegan.

---

## ✨ Fitur Utama

### 🤖 **AI-Powered Chatbot**
- Menggunakan **Google Gemini Pro API** untuk percakapan alami.
- Memberikan informasi akurat seputar rute, persiapan, hingga spot terbaik di Sulamadaha.
- Riwayat percakapan yang dapat disimpan (untuk user terdaftar).

### 🔐 **Sistem Autentikasi**
- **Email & Password**: Registrasi dan login konvensional yang aman.
- **Google OAuth 2.0**: Login cepat dan praktis menggunakan akun Google.
- **Role-Based Access**: Pembedaan hak akses antara User dan Administrator.

### 📊 **Admin Dashboard**
- **Dashboard Overview**: Pantau total user, user online (30 menit terakhir), dan statistik login.
- **User Management**: Lihat detail profil, kelola status aktif akun, dan hapus user.
- **Administrator Management**: Kelola tim admin, tambah admin baru, dan edit profil admin.
- **Activity Logs**: Lacak riwayat aktivitas user (login, signup, chat, logout).
- **Analytics & Reports**: Grafik statistik login mingguan.

### 🎨 **Premium UI/UX**
- **Dark Glassmorphism Design**: Antarmuka transparan dengan efek blur yang modern.
- **Responsive Layout**: Optimal untuk perangkat mobile, tablet, maupun desktop.
- **Micro-animations**: Animasi transisi yang smooth untuk pengalaman user yang lebih premium.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, [Flask](https://flask.palletsprojects.com/)
- **Database**: [SQLite](https://sqlite.org/) (via [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/))
- **Authentication**: [Flask-Login](https://flask-login.readthedocs.io/), Google OAuth 2.0
- **AI Engine**: [Google Gemini Pro](https://ai.google.dev/) via LangChain
- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism), Vanilla JavaScript
- **Icons**: [FontAwesome 6.4.0](https://fontawesome.com/)
- **Fonts**: [Plus Jakarta Sans](https://fonts.google.com/specimen/Plus+Jakarta+Sans)

---

## 📁 Struktur Proyek

```text
Project AI - Flask Versi 2/
├── app.py                # Entry point aplikasi & route chatbot
├── auth.py               # Logika autentikasi (Email & Google OAuth)
├── admin.py              # Dashboard administrator & manajemen data
├── models.py             # Definisi skema database (SQLAlchemy)
├── utils.py              # Helper functions (AI & OAuth)
├── requirements.txt      # Python dependencies
├── .env                  # Konfigurasi environment variables
├── create_admin.py       # Script untuk membuat user administrator baru
├── static/
│   ├── css/              # auth.css, style.css (Dark Theme)
│   ├── js/               # script.js (Chat logic)
│   └── background/       # Aset gambar latar belakang
│   └── Profile/          # Aset foto dari developer
└── templates/
    ├── base.html         # Template utama (Navigation & Layout)
    ├── landing.html      # Landing page utama
    ├── index.html        # Interface Chatbot
    ├── about.html        # Informasi pengembang & aplikasi
    ├── admin/            # Template dashboard administrator
    ├── auth/             # Template login & register
    └── errors/           # Custom error pages (404, 500)
```

---

## 🚀 Panduan Instalasi

### 1. **Kloning & Setup Environment**
```bash
# Buat virtual environment
python -m venv .venv

# Aktivasi venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

### 2. **Instalasi Dependencies**
```bash
pip install -r requirements.txt
```

### 3. **Konfigurasi Environment Variables**
Buat file `.env` di direktori utama dan isi detail berikut:
```env
# Google Gemini API
GOOGLE_API_KEY=your_gemini_api_key

# Flask Secret
SECRET_KEY=generate_a_secure_random_string

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5000/auth/callback

# Database
DATABASE_URL=sqlite:///chatbot.db
```

### 4. **Menjalankan Aplikasi**
```bash
python app.py
```
Aplikasi akan tersedia di `http://localhost:5000`

---

## 🛡️ Akses Administrator

Untuk membuat user administrator pertama kali, gunakan script utility:
```bash
python create_admin.py
```
Ikuti instruksi di terminal untuk mengatur username dan password admin.

---

## 📝 Catatan Pengembangan
- Pastikan Port 5000 tidak digunakan oleh aplikasi lain saat mencoba menjalankan server.
- Pastikan anda sudah mengaktifkan **Google Search API** dan **Generative Language API** di Google Cloud Console untuk fitur AI.
- Redirect URI di Google Cloud Console harus didaftarkan persis seperti yang ada di file `.env`.

---

## 📄 Lisensi
Free for Personal Use.

---
© 2026 Sulamadaha AI Team
