# FitTrack AI - System Architecture

## 1. Overview
**FitTrack AI** is an intelligent personal fitness, nutrition, weight, activity, sleep, hydration, and body recomposition assistant running as a 24/7 Telegram Bot built with Python 3.11+, **aiogram 3.x**, and **Firebase (Firestore & Firebase Storage)** as the primary backend database. It integrates Vision-capable Multimodal AI (Gemini / Claude / OpenAI vision) for Indonesian food photo analysis, nutrition label OCR, and an empathetic, habit-focused Indonesian AI Coach.

---

## 2. High-Level Architecture Diagram

```
+-----------------------------------------------------------------------------------+
|                                  Telegram User                                    |
|         (Text Commands, Inline Menus, Food Photos, Fitness Screenshots)           |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ (Telegram Bot API / Long-polling / Webhook)
+-----------------------------------------------------------------------------------+
|                                aiogram 3.x Bot Layer                              |
|  - Routers & Middlewares (Auth, User Context, Error Handling, Throttling)        |
|  - Finite State Machine (FSM) States (Food entry, Weight, Profile editing, Coach) |
|  - Inline Keyboard & Callback Query Handlers                                      |
+-----------------------------------------------------------------------------------+
        │                         │                           │
        ▼                         ▼                           ▼
+──────────────────+     +──────────────────+     +──────────────────────────+
|  Handlers Layer  |     |  AI Engine Layer |     |  Business Services Layer |
| - start / profile|     | - Vision Analyzer|     | - Nutrition & Food DB    |
| - dashboard      |     | - Label OCR      |     | - Activity & Calories    |
| - food / meal log|     | - AI Coach Chat  |     | - Sleep & Schedule       |
| - activity       |     | - Screenshot OCR |     | - Daily Score & Reports  |
| - weight / water |     +──────────────────+     +──────────────────────────+
| - stats / coach  |               │                           │
+──────────────────+               │                           │
        │                          │                           │
        └──────────────────────────┼───────────────────────────┘
                                   ▼
+-----------------------------------------------------------------------------------+
|                        Firebase Service Layer (Data Access)                       |
|  - Firestore Client (Async wrapper for collections, documents, subcollections)    |
|  - Firebase Storage Client (Food photo & screenshot upload/retrieval)            |
|  - Multi-tenant isolation by `telegram_user_id`                                   |
|  - Auto-retries, Pydantic Schema Validation, UTC Timestamps                       |
+-----------------------------------------------------------------------------------+
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                             ▼
+------------------------------------+  +------------------------------------+
|       Google Cloud Firestore       |  |       Google Cloud Storage         |
| - users/{telegram_user_id}         |  | - food-images/{user_id}/YYYY/MM/   |
|   ├── profile, goals, settings     |  |   {image_id}.jpg                   |
|   ├── food_logs/{log_id}           |  | - screenshots/{user_id}/YYYY/MM/   |
|   ├── activities/{act_id}          |  +------------------------------------+
|   ├── weights/{weight_id}          |
|   ├── sleep_logs/{sleep_id}        |
|   ├── water_logs/{water_id}        |
|   ├── daily_summaries/{date}       |
|   └── ai_conversations/{conv_id}   |
+------------------------------------+
```

---

## 3. Technology Stack Breakdown

| Layer | Component | Choice | Rationale |
|---|---|---|---|
| **Runtime** | Language | Python 3.11+ / 3.12 | Native typing, modern `asyncio`, performance improvements. |
| **Bot Framework** | Telegram Bot API | `aiogram 3.x` | Modern asynchronous Telegram framework, FSM context, Magic Filter `F.data`, robust Dispatcher/Router architecture. |
| **Database** | Primary NoSQL DB | **Google Cloud Firestore** (via Firebase Admin SDK) | Flexible document structure, subcollections per user, fast queries by timestamp, scalable, fully managed. |
| **Media Storage** | Cloud Storage | **Firebase Storage / GCS Bucket** | Secure binary storage for user meal pictures and screenshots; URLs/paths linked in Firestore documents. |
| **Data Validation** | Schema & Models | **Pydantic v2** | Strong typing, serialization/deserialization for Firestore documents, clean DTOs. |
| **AI / Multimodal** | Vision & LLM | Multimodal Vision API (Google Gemini / OpenAI compatible) | Accurate identification of Indonesian dishes, OCR for nutrition facts, friendly conversational coaching. |
| **Configuration** | Environment | `pydantic-settings` / `python-dotenv` | Secure `.env` loading, validation of Telegram tokens and Firebase credentials. |

---

## 4. Key Architectural Modules

### 4.1. Telegram Layer (`app/bot/` & `app/handlers/`)
- **Dispatcher & Routers**: Modular handler registration using `aiogram.Router`. Each domain (food, activity, weight, sleep, water, dashboard, coach) is encapsulated in its own handler module.
- **Middleware**:
  - `UserAuthMiddleware`: Ensures user document exists in Firestore before routing; caches user profile in handler context data.
  - `LoggingMiddleware`: Structured logs of incoming commands and callbacks without exposing sensitive tokens.
- **FSM States (`app/bot/states.py`)**: Manages multi-step inputs (e.g. editing food details, custom profile updates, AI coaching conversations).
- **Keyboards (`app/bot/keyboards.py`)**: Reusable inline keyboard builders with standardized callback prefixes (e.g., `nav:`, `food:`, `act:`, `confirm:`).

### 4.2. Firebase Service Layer (`app/services/firebase_service.py`)
- Acts as the single source of truth for all database queries and storage uploads.
- **Encapsulation**: Handlers **never** import `firebase_admin` or call Firestore directly.
- **Async Execution**: Wraps blocking Firebase Admin SDK calls in `asyncio.to_thread` or utilizes async client abstractions to avoid event loop blocking.
- **Data Isolation**: Every query strictly includes `telegram_user_id` in the document path (`users/{telegram_user_id}/...`), preventing cross-tenant data leakage.

### 4.3. Business Services Layer (`app/services/`)
- `nutrition_service.py`: Computes daily macronutrients, natural vs added sugar differentiation, Indonesian food database lookup, progress bar rendering.
- `activity_service.py`: MET-based caloric expenditure calculation for walking, running, skipping, and home workouts; calculates pace/distance.
- `sleep_service.py`: Distinguishes sleep duration from circadian timing/consistency; non-judgmental schedule analysis.
- `report_service.py`: Daily Score calculation (weighted composite across nutrition, protein, sugar, activity, sleep, hydration) and weekly trend aggregations.

### 4.4. AI Intelligence Layer (`app/ai/`)
- `vision.py`: Pre-processes uploaded meal photos, submits prompts with Indonesian cuisine context to Vision LLM, returns structured JSON estimates with uncertainty markers (Low/Medium/High).
- `nutrition_analyzer.py`: Nutrition facts label parser (OCR + structured extraction) and Indonesian food name fuzzy-matcher.
- `coach.py`: Retrieval-Augmented Coach. Injects recent Firestore summary (today's calories, protein, sugar, activity, sleep, hydration, weight goal) into prompt. Maintains friendly Indonesian casual tone ("santai, suportif, no guilt").

---

## 5. Security & Privacy Architecture
1. **Credentials Management**:
   - `TELEGRAM_BOT_TOKEN`, `FIREBASE_PROJECT_ID`, `FIREBASE_CLIENT_EMAIL`, `FIREBASE_PRIVATE_KEY`, and `AI_API_KEY` stored exclusively in `.env`.
   - `.env` excluded in `.gitignore`.
2. **Access Control**:
   - All collection queries resolve relative to `users/{telegram_user_id}`.
   - User IDs are derived directly from the authenticated Telegram update (`message.from_user.id` or `callback_query.from_user.id`).
3. **Data Retention & Privacy**:
   - Photos uploaded to Storage are assigned unique nonces and access tokens.
   - Logs redact private tokens and personal identifiers.

---

## 6. Error Handling & Resilience
- **Network / API Retries**: Exponential backoff on transient Firebase and AI API failures using decorators.
- **Graceful Fallbacks**: If Firebase is unreachable or credentials are not yet configured during local offline unit testing, the service layer supports a local/mock adapter for seamless development and CI testing.
- **User-Friendly Error Messages**: Clear Indonesian error prompts when inputs are invalid or format is incorrect, providing example syntax (e.g. `/walk 6 km`, `/sleep 23:00 07:00`).
