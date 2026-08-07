# FitTrack AI - Firestore & Storage Schema Specification

## 1. Firestore Database Architecture

FitTrack AI utilizes a hierarchical user-centric subcollection layout in Google Cloud Firestore. This ensures total data isolation per Telegram user, clean indexing, and simple query authorization.

```
users/ (Root Collection)
  └── {telegram_user_id}/ (Document)
        ├── [fields]: profile, goals, settings, created_at, updated_at
        │
        ├── food_logs/ (Subcollection)
        │     └── {food_log_id} (Document)
        │
        ├── activities/ (Subcollection)
        │     └── {activity_id} (Document)
        │
        ├── weights/ (Subcollection)
        │     └── {weight_id} (Document)
        │
        ├── sleep_logs/ (Subcollection)
        │     └── {sleep_id} (Document)
        │
        ├── water_logs/ (Subcollection)
        │     └── {water_log_id} (Document)
        │
        ├── daily_summaries/ (Subcollection)
        │     └── {YYYY-MM-DD} (Document)
        │
        └── ai_conversations/ (Subcollection)
              └── {conversation_id} (Document)
```

---

## 2. Document & Field Schemas

### 2.1. User Document: `users/{telegram_user_id}`
Represents the user's primary profile, body recomposition targets, and system preferences.

```json
{
  "telegram_user_id": 123456789,
  "username": "fatirgibran",
  "first_name": "Fatir",
  "profile": {
    "age": 20,
    "gender": "male",
    "height_cm": 175.0,
    "current_weight_kg": 75.0,
    "target_weight_kg": 70.0,
    "activity_level": "moderate",
    "main_muscle_focus": ["chest", "arms", "shoulders", "core"],
    "preferred_exercises": ["walking", "running", "skipping", "home workout"],
    "diet_preference": {
      "reduce_added_sugar": true,
      "food_style": "normal affordable Indonesian food",
      "no_extreme_dieting": true
    }
  },
  "goals": {
    "goal_type": "recomposition",
    "daily_calories_target": 2100,
    "protein_target_min_g": 90.0,
    "protein_target_max_g": 120.0,
    "carbs_target_g": 240.0,
    "fat_target_g": 60.0,
    "added_sugar_max_g": 25.0,
    "fiber_target_g": 25.0,
    "water_target_ml": 2500,
    "sleep_target_hours": 8.0,
    "weekly_workout_days": 4
  },
  "settings": {
    "timezone": "Asia/Jakarta",
    "language": "id",
    "reminders_enabled": true,
    "daily_score_notifications": true
  },
  "created_at": "2026-08-07T16:00:00Z",
  "updated_at": "2026-08-07T16:00:00Z"
}
```

---

### 2.2. Food Logs Subcollection: `users/{telegram_user_id}/food_logs/{food_log_id}`
Stores logged meals from manual input, food photos, or scanned nutrition labels.

```json
{
  "food_log_id": "food_20260807_a1b2c3d4",
  "telegram_user_id": 123456789,
  "food_name": "Nasi Putih + Dada Ayam Bakar + Sayur Sop",
  "meal_type": "lunch",
  "portion": "1 piring sedang (150g nasi, 120g ayam, 1 mangkuk sop)",
  "items": [
    {
      "name": "Nasi Putih",
      "estimated_grams": 150,
      "calories": 195,
      "protein_g": 4.0,
      "carbs_g": 43.0,
      "fat_g": 0.4,
      "sugar_g": 0.1,
      "is_added_sugar": false
    },
    {
      "name": "Dada Ayam Bakar",
      "estimated_grams": 120,
      "calories": 198,
      "protein_g": 37.2,
      "carbs_g": 0.0,
      "fat_g": 4.3,
      "sugar_g": 0.0,
      "is_added_sugar": false
    },
    {
      "name": "Sayur Sop",
      "estimated_grams": 100,
      "calories": 45,
      "protein_g": 1.8,
      "carbs_g": 8.0,
      "fat_g": 0.8,
      "sugar_g": 2.5,
      "is_added_sugar": false
    }
  ],
  "calories": 438,
  "protein_g": 43.0,
  "carbs_g": 51.0,
  "fat_g": 5.5,
  "total_sugar_g": 2.6,
  "added_sugar_g": 0.0,
  "fiber_g": 3.2,
  "sodium_mg": 480,
  "confidence": "high",
  "source": "photo_ai",
  "image_reference": "food-images/123456789/2026/08/img_987654.jpg",
  "image_url": "https://storage.googleapis.com/...",
  "notes": "Dada ayam tanpa kulit, minyak minim",
  "logged_date": "2026-08-07",
  "created_at": "2026-08-07T05:30:00Z"
}
```

*Meal Types*: `breakfast`, `lunch`, `dinner`, `snack`
*Confidence Levels*: `manual` (100%), `label_ocr` (high), `photo_ai` (medium/high), `estimate` (low/medium)
*Sources*: `manual_text`, `photo_ai`, `nutrition_label_ocr`, `quick_preset`

---

### 2.3. Activities Subcollection: `users/{telegram_user_id}/activities/{activity_id}`
Stores physical activities logged via commands (`/walk`, `/run`, `/skipping`, `/workout`) or screenshot OCR.

```json
{
  "activity_id": "act_20260807_e5f6g7h8",
  "telegram_user_id": 123456789,
  "activity_type": "running",
  "distance_km": 5.0,
  "duration_minutes": 42.0,
  "repetitions": null,
  "steps": 6200,
  "pace_min_per_km": 8.4,
  "estimated_calories": 360,
  "source": "command",
  "notes": "Lari santai sore di komplek",
  "activity_date": "2026-08-07",
  "created_at": "2026-08-07T10:15:00Z"
}
```

*Supported Activity Types*: `walking`, `running`, `skipping`, `home_workout`, `cycling`, `other`

---

### 2.4. Weight Tracking Subcollection: `users/{telegram_user_id}/weights/{weight_id}`
Tracks weigh-ins and historical body composition changes.

```json
{
  "weight_id": "w_20260807",
  "telegram_user_id": 123456789,
  "weight_kg": 74.5,
  "starting_weight_kg": 75.0,
  "target_weight_kg": 70.0,
  "difference_from_start_kg": -0.5,
  "difference_from_previous_kg": -0.2,
  "logged_date": "2026-08-07",
  "created_at": "2026-08-07T01:00:00Z"
}
```

---

### 2.5. Sleep Tracking Subcollection: `users/{telegram_user_id}/sleep_logs/{sleep_id}`
Differentiates between **Sleep Duration** (amount of sleep) and **Circadian Timing** (bedtime/wake time schedule) to encourage consistency without shaming night owls.

```json
{
  "sleep_id": "sleep_20260807",
  "telegram_user_id": 123456789,
  "bedtime": "23:30",
  "wake_time": "07:30",
  "duration_hours": 8.0,
  "quality_rating": 4,
  "timing_assessment": "consistent",
  "duration_assessment": "optimal",
  "notes": "Bangun segar",
  "sleep_date": "2026-08-07",
  "created_at": "2026-08-07T01:30:00Z"
}
```

---

### 2.6. Hydration Subcollection: `users/{telegram_user_id}/water_logs/{water_log_id}`
Tracks incremental water intakes throughout the day.

```json
{
  "water_log_id": "water_20260807_1234",
  "telegram_user_id": 123456789,
  "amount_ml": 500,
  "logged_date": "2026-08-07",
  "created_at": "2026-08-07T03:00:00Z"
}
```

---

### 2.7. Daily Summaries Subcollection: `users/{telegram_user_id}/daily_summaries/{YYYY-MM-DD}`
Aggregated snapshot of the user's daily totals, score, and AI coaching summary.

```json
{
  "summary_date": "2026-08-07",
  "telegram_user_id": 123456789,
  "nutrition": {
    "total_calories": 1950,
    "target_calories": 2100,
    "total_protein_g": 105.0,
    "target_protein_range": [90.0, 120.0],
    "total_carbs_g": 210.0,
    "total_fat_g": 55.0,
    "total_sugar_g": 18.0,
    "added_sugar_g": 12.0,
    "added_sugar_max_g": 25.0,
    "total_fiber_g": 22.0,
    "meal_count": 3
  },
  "activity": {
    "total_calories_burned": 420,
    "total_active_minutes": 55,
    "activity_count": 2
  },
  "sleep": {
    "duration_hours": 8.0,
    "bedtime": "23:30",
    "wake_time": "07:30"
  },
  "hydration": {
    "total_water_ml": 2500,
    "target_water_ml": 2500
  },
  "daily_score": {
    "score": 8.8,
    "max_score": 10.0,
    "components": {
      "nutrition": "green",
      "protein": "green",
      "sugar": "green",
      "activity": "green",
      "sleep": "green",
      "hydration": "green"
    }
  },
  "ai_feedback": "Nutrisi dan protein hari ini sangat solid! Asupan gula terkendali di 12g. Tetap konsisten untuk progres rekomposisi tubuhmu.",
  "updated_at": "2026-08-07T15:00:00Z"
}
```

---

### 2.8. AI Conversations Subcollection: `users/{telegram_user_id}/ai_conversations/{conversation_id}`
Logs conversational coaching turns with context for seamless conversational memory.

```json
{
  "conversation_id": "conv_20260807_123456",
  "telegram_user_id": 123456789,
  "user_message": "aku boleh makan bakso sore ini?",
  "coach_response": "Boleh banget! Bakso adalah sumber protein yang oke. Pilih kuah bening dan kurangi gorengan tambahannya kalau mau jaga kalori. Karena kamu sudah jalan 5 km tadi pagi, ada ruang kalori yang aman.",
  "context_snapshot": {
    "calories_left": 850,
    "protein_logged_g": 65.0,
    "sugar_logged_g": 8.0
  },
  "created_at": "2026-08-07T08:30:00Z"
}
```

---

## 3. Firebase Storage Hierarchy

Meal pictures and workout screenshots are organized cleanly by Telegram user ID and year/month hierarchy:

```
gs://{firebase_bucket_name}/
  ├── food-images/
  │     └── {telegram_user_id}/
  │           └── {YYYY}/
  │                 └── {MM}/
  │                       ├── {image_id}.jpg
  │                       └── {image_id}_thumb.jpg
  │
  └── fitness-screenshots/
        └── {telegram_user_id}/
              └── {YYYY}/
                    └── {MM}/
                          └── {screenshot_id}.jpg
```

### Storage Metadata Attributes
When uploading binary images via `upload_food_image()`, the following custom metadata is attached:
- `Content-Type`: `image/jpeg`
- `customMetadata`:
  - `telegram_user_id`: `{telegram_user_id}`
  - `uploaded_at`: ISO 8601 UTC timestamp
  - `source`: `telegram_bot`
  - `food_log_id`: (linked after confirmation)
