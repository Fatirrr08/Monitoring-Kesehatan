# FitTrack AI - Personal Fitness & Nutrition Telegram Assistant

**FitTrack AI** adalah asisten personal untuk pemantauan nutrisi, berat badan, aktivitas fisik, kualitas tidur, hidrasi, dan rekomposisi tubuh (*fat loss + muscle gain*) yang berjalan sebagai Telegram Bot 24/7 menggunakan **Python 3.11+**, **aiogram 3.x**, dan **Google Cloud Firebase (Firestore & Firebase Storage)** sebagai database utama.

---

## 🌟 Fitur Utama

- 🏠 **Dashboard Harian (`/today`)**: Rangkuman visual kalori harian, protein progress bar (`████████░░`), karbohidrat, lemak, gula tambahan, tidur, aktivitas, dan hidrasi.
- 🍱 **Pencatatan Makanan & Database Lokal**: Terintegrasi dengan database makanan khas Indonesia (nasi putih, dada ayam, tempe, tahu, jambu biji merah, opor, sayur sop, americano, dll).
- 🍬 **Sugar Monitoring Terpisah**: Membedakan secara tegas gula alami buah (contoh: jambu merah) dari *added sugar* (maksimal $\le 25\text{ g/hari}$).
- 💪 **Protein Tracking Dinamis**: Target awal 90–120 g/hari dengan bar visual untuk mendukung pembentukan otot tanpa diet ekstrem.
- 📸 **Food Photo Vision AI**: Analisis otomatis foto makanan/piring dengan indikator keyakinan (🟢 High, 🟡 Medium, 🔴 Low) dan tombol konfirmasi (✅ Catat, ✏️ Edit, ❌ Batal).
- 🥛 **Nutrition Label Scanner**: Ekstraksi fakta nutrisi kemasan produk (kalori, protein, lemak jenuh, gula, laktosa, natrium).
- ⚖️ **Weight Tracking (`/weight 74.5`)**: Pemantauan progres berat badan mingguan dan bulanan tanpa menghakimi fluktuasi air harian.
- 🏃 **Activity Logging**: Perintah cepat `/walk 6 km`, `/run 5 km 42m`, `/skipping 800`, `/workout 35m` dengan estimasi kalori berbasis MET.
- 😴 **Sleep & Recovery (`/sleep 23:00 07:00` atau `/sleep 07:00 15:00`)**: Evaluasi durasi tidur terpisah dari jadwal sirkadian secara suportif.
- 💧 **Water Tracking (`/water 500`)**: Pemantauan hidrasi dengan tombol cepat +250ml, +500ml, +600ml, +1000ml.
- 🤖 **AI Coach Santai**: Konsultasi berbasis AI berbahasa Indonesia kasual, memahami konteks jurnal harian tanpa *food shaming*, dan mendukung konsep *flexible meal*.
- ⭐ **Daily Score & Weekly Report (`/week`)**: Evaluasi 6 dimensi kebiasaan sehat jangka panjang.

---

## 🏗️ Struktur Proyek

```
fittrack-ai/
├── app/
│   ├── bot/
│   │   ├── bot.py             # Bot & Dispatcher setup
│   │   ├── keyboards.py       # Inline Keyboards & Menu Navigasi
│   │   └── states.py          # FSM States (aiogram 3.x)
│   ├── handlers/
│   │   ├── start.py           # /start & inisialisasi profil
│   │   ├── dashboard.py       # /today & ringkasan harian
│   │   ├── food.py            # Pencatatan makanan & konfirmasi AI
│   │   ├── activity.py        # /walk, /run, /skipping, /workout
│   │   ├── weight.py          # /weight & riwayat timbangan
│   │   ├── sleep.py           # /sleep & analisis istirahat
│   │   ├── water.py           # /water & tombol hidrasi
│   │   ├── statistics.py      # /stats, /score, /week
│   │   └── coach.py           # AI Coach chat handler
│   ├── services/
│   │   ├── firebase_service.py # Core Firebase Firestore & Storage service layer
│   │   ├── food_database.py    # Database makanan Indonesia & klasifikasi gula
│   │   ├── nutrition_service.py # Kalkulasi makronutrisi & progress bar
│   │   ├── activity_service.py  # Estimasi pembakaran kalori MET
│   │   ├── sleep_service.py     # Analisis durasi vs ritme tidur
│   │   └── report_service.py    # Daily score & weekly summary
│   ├── ai/
│   │   ├── vision.py           # Vision AI piring makanan
│   │   ├── nutrition_analyzer.py # OCR label informasi nilai gizi
│   │   └── coach.py            # Conversational Indonesian AI Coach
│   ├── models/
│   │   └── schemas.py          # Pydantic v2 schemas Firestore
│   ├── utils/
│   │   ├── formatting.py       # ASCII progress bar & format teks
│   │   └── logger.py           # Structured logging
│   └── config.py               # Settings & .env loading
├── tests/
│   ├── test_schemas.py
│   ├── test_firebase_service.py
│   ├── test_nutrition.py
│   ├── test_activities.py
│   ├── test_sleep.py
│   ├── test_water.py
│   └── test_handlers.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── README.md
└── main.py
```

---

## 🚀 Panduan Menjalankan Bot

### 1. Kloning & Buat Virtual Environment
```bash
git clone https://github.com/Fatirrr08/Monitoring-Kesehatan.git
cd Monitoring-Kesehatan

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Konfigurasi Environment (`.env`)
Salin file `.env.example` ke `.env`:
```bash
cp .env.example .env
```
Isi variabel berikut:
```ini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRstuvWXyz
FIREBASE_PROJECT_ID=fittrack-ai-prod
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@fittrack-ai-prod.iam.gserviceaccount.com
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_STORAGE_BUCKET=fittrack-ai-prod.appspot.com
AI_API_KEY=AIzaSy...
```

### 3. Menjalankan Pengujian Unit & Integrasi
```bash
pytest
```

### 4. Menjalankan Bot
```bash
python main.py
```

---

## 🔒 Keamanan & Isolasi Data
- Setiap pengguna Telegram memiliki ruang data terisolasi menggunakan `telegram_user_id` di Firestore path `users/{telegram_user_id}/...`.
- Foto makanan disimpan di Google Cloud Storage pada path `food-images/{telegram_user_id}/YYYY/MM/`.
- Token bot dan kredensial Firebase tidak pernah di-commit ke Git (`.env` dan `serviceAccountKey.json` dilindungi oleh `.gitignore`).
