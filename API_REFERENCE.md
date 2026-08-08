# FitTrack AI — API & Architecture Reference

## 1. System Architecture Overview

```
Telegram Client (aiogram 3.x)
          │
          ▼
Handlers / Routers Layer (`app/handlers/`)
          │
          ▼
Application / Service Layer (`app/services/`)
   ├── NutritionService & Food Database
   ├── ActivityService & MET Calculator
   ├── SleepService
   └── ReportService
          │
          ▼
Repository Layer (`app/repositories/`)
   ├── UserRepository
   ├── FoodRepository
   ├── ActivityRepository
   ├── WeightRepository
   ├── SleepRepository
   ├── WaterRepository
   └── SummaryRepository
          │
          ▼
Google Cloud Firestore & Firebase Storage
```

---

## 2. Telegram Commands Reference

| Command | Arguments | Description | Example |
|---|---|---|---|
| `/start` | — | Initializes user profile, goals, and shows main dashboard | `/start` |
| `/help` | — | Shows complete command reference guide | `/help` |
| `/profile` | — | Inspects current user profile, height, weight, and recomposition goals | `/profile` |
| `/progress` | — | Displays weight progress delta and daily score breakdown | `/progress` |
| `/today` / `/dashboard` | — | Shows today's full nutrition, water, activity, and sleep summary | `/today` |
| `/week` / `/stats` | — | Generates 7-day trend analytics report | `/week` |
| `/food` / `/makan` | `[food_name]` | Quick meal logger from Indonesian food database or menu picker | `/makan dada ayam` |
| `[Photo Upload]` | — | AI Vision meal photo analysis with confidence ranges & confirmation card | *(Upload photo)* |
| `/walk` | `[distance] [duration]` | Logs walking distance, steps, and estimated calories burned | `/walk 6 km` |
| `/run` | `[distance] [duration]` | Logs running distance, pace min/km, and active calories | `/run 5 km 35m` |
| `/badminton` | `[matches] [sets] [duration]` | Logs badminton match count, sets, and calorie expenditure | `/badminton 2 matches` |
| `/skipping` | `[repetitions] [duration]` | Logs jump rope repetitions and cardio duration | `/skipping 800` |
| `/workout` | `[duration] [focus]` | Logs resistance / home bodyweight training session | `/workout 35m` |
| `/weight` | `[kg]` | Logs daily weight entry and updates profile | `/weight 74.2` |
| `/water` | `[ml]` | Increments daily water hydration tracker | `/water 500` |
| `/sleep` | `[bedtime] [waketime]` | Logs sleep schedule and duration | `/sleep 23:00 07:00` |
| `/coach` | `[question]` | AI Coach retrieval-augmented advice | `/coach protein aku cukup?` |

---

## 3. Data Flow & Confirmation Pipeline

1. **Food Photo Flow**:
   - User uploads photo.
   - Bot validates file size ($\le 15\text{ MB}$) and MIME magic bytes.
   - Image uploaded to `food-images/{telegram_user_id}/{YYYY}/{MM}/{image_id}.jpg`.
   - Vision Engine returns structured `FoodAnalysis` with `calories_min`, `calories_max`, `protein_g`, `added_sugar_g`, `confidence`, and `assumptions`.
   - Telegram card presents uncertainty range.
   - User confirms with `[✅ Catat]`, `[✏️ Edit]`, or `[❌ Batal]`.
   - On confirmation, record saved to Firestore `users/{user_id}/food_logs/{food_log_id}` and `users/{user_id}/daily_summaries/{YYYY-MM-DD}` is updated.
