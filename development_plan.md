# FitTrack AI - Development & Implementation Plan

## 1. Project Overview & Core Philosophy
**FitTrack AI** is a personal fitness, nutrition, weight, activity, sleep, hydration, and body recomposition assistant designed specifically for Indonesian lifestyle and cuisine, operating via Telegram Bot (`aiogram 3.x`) and backed by **Google Cloud Firebase (Firestore & Firebase Storage)**.

### Guiding Principles
- **Body Recomposition**: Prioritize fat loss while preserving/building lean muscle (chest, arms, shoulders, core).
- **Sustainable Habits**: No starvation, no extreme calorie deficits, no demonizing staple foods like white rice, and no guilt around flexible meals.
- **Supportive & Friendly Tone**: Empathetic Indonesian casual coaching style ("santai, suportif, konsisten").
- **Clear Uncertainty Markers**: Visually separate AI estimations (e.g. food photos) from high-confidence data (e.g. nutrition facts labels or manual inputs).

---

## 2. Architecture & Service Layer Design

### Service Layer Principle
Telegram handlers **never** interact directly with Firebase or external AI APIs. Handlers only consume domain services:
- `FirebaseService`: Abstracted Firestore queries, batch updates, Storage uploads. Includes graceful local fallback/mocking for offline development and testing.
- `NutritionService`: Macro calculations, natural vs added sugar differentiation, Indonesian food database queries, visual progress bar rendering.
- `ActivityService`: Activity logging, duration/distance tracking, MET-based estimated caloric burn.
- `SleepService`: Separate sleep duration assessment from schedule timing assessment.
- `ReportService`: Daily score multi-metric evaluation, weekly summary analytics.
- `VisionService` & `AICoachService`: Multimodal meal analysis, label OCR parsing, retrieval-augmented contextual AI coaching.

---

## 3. Comprehensive Telegram Bot Flow

```
User -> /start -> Init Profile (Default / Custom) -> Show Main Menu Keyboard
                                                          │
   ┌──────────────┬──────────────┬──────────────┬─────────┴────┬──────────────┬──────────────┐
   ▼              ▼              ▼              ▼              ▼              ▼              ▼
🏠 Dashboard   🍱 Log Food   📸 Food Photo   🏃 Activity   ⚖️ Weight      😴 Sleep       💧 Water
(/today)      (Menu/Text)    (Vision AI)     (/walk, etc)  (/weight)      (/sleep)       (/water)
   │              │              │              │              │              │              │
   ▼              ▼              ▼              ▼              ▼              ▼              ▼
Firestore -> Return Visual Summary / Progress Bar / Daily Score / Friendly Recommendations
```

### Main Menu Inline Keyboard
- 🏠 `Dashboard`
- 🍱 `Catat Makanan`
- 📸 `Foto Makanan`
- 🏃 `Aktivitas`
- ⚖️ `Berat Badan`
- 😴 `Tidur`
- 💧 `Air`
- 📊 `Statistik`
- 🎯 `Target`
- 🤖 `AI Coach`
- ⚙️ `Pengaturan`

---

## 4. Phase-by-Phase Roadmap

### Phase 1: Working Telegram MVP (Current Phase)
- [x] Project structure setup (`fittrack-ai/` with clean modular architecture)
- [x] Dependencies definition (`requirements.txt`, `.env.example`, `.gitignore`, `Dockerfile`, `README.md`)
- [x] Pydantic Schemas (`User`, `Profile`, `Goals`, `FoodLog`, `ActivityLog`, `WeightLog`, `SleepLog`, `WaterLog`, `DailySummary`)
- [x] Firebase Service Layer (`app/services/firebase_service.py`) with complete Firestore CRUD, Storage mock/live client, async wrappers, retry handling, and local adapter fallback
- [x] Indonesian Food Database (`app/services/food_database.py`) with common dishes (nasi putih, dada ayam, tempe, tahu, jambu merah, americano, jamu kunyit asam, etc.)
- [x] Business Services:
  - `nutrition_service.py` (macro computations, sugar filtering, progress bars)
  - `activity_service.py` (MET calculations for walking, running, skipping, workout)
  - `sleep_service.py` (duration vs schedule timing)
  - `report_service.py` (daily summary & score calculator)
- [x] aiogram 3.x Telegram Handlers:
  - `/start` with default profile setup & editing
  - Dashboard & `/today` with visual summary
  - Manual food logging & quick preset picker
  - Weight logging (`/weight 74.5`) & history
  - Activity logging (`/walk 6 km`, `/run 5 km 42m`, `/skipping 800`, `/workout 35m`)
  - Sleep logging (`/sleep 23:00 07:00` or `/sleep 07:00 15:00`)
  - Water tracking (`/water 500` and quick button increments)
  - Target & Settings view and updates
- [x] Unit and Integration Test Suite verifying all services and handlers.

### Phase 2: Food Photo Analysis, Nutrition Label OCR & Firebase Storage
- [ ] Multimodal AI Vision engine integration (`app/ai/vision.py`)
- [ ] Food portion and dish identification with confidence levels (🔴 Low, 🟡 Medium, 🟢 High)
- [ ] Confirmation UI (✅ Catat, ✏️ Edit, ❌ Batal)
- [ ] Nutrition Label OCR extraction (calories, protein, carbs, fat, sat fat, sugar, sodium, fiber, lactose)
- [ ] Storage upload pipeline for meal images.

### Phase 3: Conversational AI Coach & Weekly Reports
- [ ] Retrieval-Augmented AI Coach (`app/ai/coach.py`) querying Firestore user context
- [ ] Natural conversation answering questions ("aku boleh makan bakso?", "proteinku kurang?")
- [ ] Multi-metric Daily Score engine (Nutrition, Protein, Sugar, Activity, Sleep, Hydration)
- [ ] `/week` comprehensive weekly analytics and progress insights.

### Phase 4: Charts, Fitness Screenshot Analysis & Personalized Workouts
- [ ] Automated visual charts for weight trends and macro distributions
- [ ] Fitness app screenshot OCR parser (Strava, Apple Fitness, Garmin, Nike Run Club)
- [ ] Dynamic muscle-group focused home workout recommendations (chest, arms, shoulders, core).

---

## 5. Testing & Verification Checklist
1. **Pydantic Validation**: Models enforce correct bounds, data types, and default values.
2. **Firebase Service**:
   - `create_user()` stores default profile.
   - `get_user()` retrieves profile.
   - `log_food()`, `log_activity()`, `log_weight()`, `log_sleep()`, `log_water()` write to respective subcollections.
   - `get_daily_summary()` aggregates all logged entries for the date.
3. **Telegram Handlers**:
   - Commands `/start`, `/today`, `/weight`, `/walk`, `/run`, `/skipping`, `/workout`, `/sleep`, `/water` execute without errors.
   - Inline callbacks trigger correct view renders.
4. **Indonesian Food Database**:
   - Correct natural vs added sugar differentiation (e.g. jambu merah = 0g added sugar; boba/manis = added sugar).
5. **Static Code Quality**:
   - All modules type-annotated and linted with clean imports.
