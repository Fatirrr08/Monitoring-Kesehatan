# FitTrack AI — Database & Storage Guide

## 1. Cloud Firestore Architecture

Google Cloud Firestore is the **exclusive primary database** for FitTrack AI.

### Collection Hierarchy:
```
users/
  └── {telegram_user_id}
        ├── profile: { age, height_cm, current_weight_kg, target_weight_kg, ... }
        ├── goals: { daily_calories_target, protein_target_min_g, added_sugar_max_g, ... }
        ├── settings: { timezone, language, ... }
        │
        ├── food_logs/
        │     └── {food_log_id} -> { food_name, calories, protein_g, added_sugar_g, confidence, source, ... }
        │
        ├── activities/
        │     └── {activity_id} -> { activity_type, distance_km, duration_minutes, matches, sets, calories, ... }
        │
        ├── weights/
        │     └── {weight_id} -> { weight_kg, starting_weight_kg, difference_from_start_kg, logged_date, ... }
        │
        ├── sleep_logs/
        │     └── {sleep_id} -> { bedtime, wake_time, duration_hours, sleep_date, ... }
        │
        ├── water_logs/
        │     └── {water_log_id} -> { amount_ml, logged_date, created_at }
        │
        ├── daily_summaries/
        │     └── {YYYY-MM-DD} -> { total_calories, total_protein_g, added_sugar_g, total_water_ml, daily_score, ... }
        │
        └── ai_conversations/
              └── {conversation_id} -> { user_message, coach_response, context_snapshot, ... }
```

---

## 2. Firebase Storage Paths

- **Food Images**: `food-images/{telegram_user_id}/{YYYY}/{MM}/{image_id}.jpg`
- **Screenshots**: `screenshots/{telegram_user_id}/{YYYY}/{MM}/{image_id}.jpg`

> [!IMPORTANT]
> Image binaries/base64 are NEVER stored directly in Firestore. Only clean storage paths, download URLs, and metadata are persisted.

---

## 3. Firestore Cost Control Strategy

1. **Pre-aggregated Daily Summaries**:
   - `/today` and dashboard operations directly fetch the single document at `users/{user_id}/daily_summaries/{YYYY-MM-DD}`.
   - Avoids full collection scans on every user message.
2. **Deterministic In-Memory Sorting**:
   - Subcollection queries filter on `logged_date` and are sorted deterministically in Python memory to prevent composite index requirements and redundant indexing billing.
