# FitTrack AI — Master Engineering Audit (CODE_AUDIT.md)

**Audit Date**: 2026-08-09  
**Lead Auditor**: Senior Backend & Systems Architect  
**Project**: FitTrack AI (Telegram Personal Nutrition & Fitness Assistant)  
**Primary Database**: Google Cloud Firestore & Firebase Storage  

---

## 1. Executive Summary
This comprehensive engineering audit analyzes the current FitTrack AI codebase against production-grade software engineering standards. While the initial MVP implements the core user flows, several architectural enhancements, security controls, repository abstractions, data validation boundaries, and AI orchestration structures must be established to ensure the product is clean, secure, testable, scalable, observable, and production-ready.

---

## 2. Detailed Audit by Category

### A. Architecture Quality & Layering
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **ARCH-01** | **HIGH** | `app/services/firebase_service.py` | Monolithic service mixing persistence queries with business summary recalculation. | Violates Single Responsibility Principle. Hard to mock repositories in unit tests and couples data access with domain logic. | Extract clean **Repository Pattern** (`UserRepository`, `FoodRepository`, `ActivityRepository`, `WeightRepository`, `SleepRepository`, `WaterRepository`, `SummaryRepository`) under `app/repositories/`. Services become pure business orchestrators. | **P0** |
| **ARCH-02** | **MEDIUM** | `app/handlers/` | Handlers contain inline text-parsing heuristics and direct business logic. | Telegram handlers should only handle UI, argument extraction, and delegating to application services. | Move all parsing, calculations, and domain formatting into dedicated services (`ActivityService`, `NutritionService`, `SleepService`, `ProfileService`). | **P1** |
| **ARCH-03** | **HIGH** | `app/services/firebase_service.py` | Realtime Database was mixed into Firestore service. | The master specification requires Cloud Firestore as the **exclusive primary database**. Dual writes add network latency and inconsistency risk. | Refactor persistence layer to strictly target **Google Cloud Firestore** collections and subcollections with a local test repository adapter for unit tests. | **P0** |

---

### B. Code Quality & Modularity
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **CODE-01** | **MEDIUM** | `app/services/activity_service.py` | Magic numbers used for MET multipliers and step estimation without explicit constants or enum mapping. | Hard to maintain, calibrate, or extend with new sports like Badminton. | Implement typed `ActivityType` enum and a structured `MET_TABLE` configuration module. | **P1** |
| **CODE-02** | **HIGH** | `app/handlers/activity.py` | Badminton activity not implemented as a first-class citizen (`/badminton 2 matches` or natural language "2 match, 2 set"). | Core specification requires badminton tracking with match and set breakdown. | Create dedicated `BadmintonParser` and activity model supporting matches, sets, and estimated exertion. | **P0** |
| **CODE-03** | **MEDIUM** | `app/bot/keyboards.py` | Inline keyboards lack explicit command shortcuts for `/help`, `/profile`, `/progress`. | Navigation is incomplete according to command spec. | Implement `/help`, `/profile`, `/progress` routers and expand keyboard builder with typed callbacks. | **P1** |

---

### C. Security & Data Protection
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **SEC-01** | **CRITICAL** | `app/handlers/food.py:143` | Photo download lacks MIME type and file size validation before uploading to Firebase Storage. | Malicious users could upload executable payloads or gigantic files causing DoS and security vulnerabilities. | Validate file size ($\le 15\text{ MB}$) and verify image header magic bytes (JPEG, PNG, WebP) before storage. | **P0** |
| **SEC-02** | **HIGH** | `app/services/firebase_service.py` | Storage path does not sanitize user inputs or enforce strict user-id hierarchy. | Arbitrary storage path traversal or cross-tenant collision risk. | Enforce rigid template paths: `food-images/{telegram_user_id}/{YYYY}/{MM}/{image_id}.jpg` and `screenshots/{telegram_user_id}/{YYYY}/{MM}/{image_id}.jpg`. | **P0** |
| **SEC-03** | **HIGH** | `app/utils/logger.py` | Logger does not scrub or filter sensitive environment keys or tokens if passed into exception messages. | Risk of credential leakage in production logs or monitoring systems. | Implement safe logging filter that redacts API keys, bot tokens, and private keys. | **P0** |

---

### D. Firebase Implementation & Firestore Cost Control
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **FIRE-01** | **HIGH** | `app/services/firebase_service.py` | `get_daily_summary` recalculation previously ran N+1 subcollection queries on every read if summary was missing. | High Firestore read count leading to unnecessary billing and latency. | Write to `users/{user_id}/daily_summaries/{YYYY-MM-DD}` incrementally whenever an activity, food log, sleep, or water entry is saved. `/today` only reads the single summary document. | **P0** |
| **FIRE-02** | **MEDIUM** | `app/services/firebase_service.py` | Subcollection references use ad-hoc string concatenation across multiple methods. | Risk of path typos or inconsistent document keys. | Centralize Firestore collection path builders (`users/{uid}`, `users/{uid}/food_logs/{id}`, etc.) in typed repository constants. | **P1** |

---

### E. AI Integration & Estimation Principles
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **AI-01** | **HIGH** | `app/ai/vision.py` | AI Vision prompt returned point estimates instead of structured uncertainty ranges (`calories_min`, `calories_max`, `confidence`, `assumptions`). | Visual estimation is inherently imprecise. Presenting single exact numbers misleads users. | Enforce structured `FoodAnalysisResult` schema with `calories_min`, `calories_max`, `protein_g_min`, `protein_g_max`, `confidence` (0.0–1.0), and `assumptions`. | **P0** |
| **AI-02** | **MEDIUM** | `app/ai/coach.py` | Conversational context retrieval fetches unsummarized raw history. | Excess token consumption and potential prompt bloat. | Implement `UserContextSummary` builder extracting only today's summary, weight delta, muscle focus, and recent activity. | **P1** |
| **AI-03** | **HIGH** | `app/handlers/food.py` | Temporary pending food confirmation held in a global dictionary without TTL. | Memory leak over time if users send photos but never click confirmation buttons. | Implement TTL cache or FSM-backed state with auto-cleanup for pending food confirmations. | **P1** |

---

### F. Data Validation & Boundary Checking
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **VAL-01** | **HIGH** | `app/models/schemas.py` | Validation limits on weight, height, age, water amount, and activity numbers were either loose or missing validators. | Invalid or corrupt inputs (e.g. weight: -5 kg or water: 50,000 ml) could corrupt database state. | Add strict Pydantic `Field(ge=..., le=...)` constraints (Weight: 20–300 kg, Height: 100–250 cm, Age: 10–120, Water: 0–10,000 ml). | **P0** |
| **VAL-02** | **HIGH** | `app/services/food_database.py` | Added sugar could default to 0 if unspecified rather than tracking `None` / `null` when unknown. | Falsely assumes unknown sugar is zero added sugar. | Explicitly distinguish `added_sugar_g = 0.0` (verified whole fruit) vs `added_sugar_g = None` (unknown/unspecified). | **P1** |

---

### G. Error Handling & Telegram UX
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **ERR-01** | **HIGH** | `app/bot/bot.py` | Unhandled network disconnects or API errors could propagate unformatted errors to users. | Poor user experience and potential stack trace exposure. | Standardize global error interceptor with Indonesian friendly user prompt: `"⚠️ Maaf, data belum berhasil diproses. Coba lagi sebentar."` and log technical details internally. | **P0** |
| **ERR-02** | **MEDIUM** | `app/handlers/` | Callback query handlers did not consistently acknowledge `callback.answer()` before long async tasks. | Telegram UI shows loading spinner on button and may trigger timeout. | Always call `await callback.answer()` immediately upon receiving query. | **P1** |

---

### H. Testing & Quality Assurance
| Issue ID | Severity | Location | Problem | Why It Matters | Recommended Solution | Priority |
|---|---|---|---|---|---|---|
| **TEST-01** | **HIGH** | `tests/` | Unit tests lacked boundary checks, validation failure tests, badminton activity tests, and AI structured parsing mock tests. | Edge cases and invalid inputs not covered by regression testing. | Add `test_validation.py`, `test_food_analysis.py`, badminton tests in `test_activities.py`, and comprehensive repository tests with mock Firestore client. | **P0** |

---

## 3. Prioritized Implementation Roadmap

### Phase 1: Architecture & Repository Refactoring (P0)
1. Build `app/repositories/` abstraction:
   - `user_repository.py`
   - `food_repository.py`
   - `activity_repository.py`
   - `weight_repository.py`
   - `sleep_repository.py`
   - `water_repository.py`
   - `summary_repository.py`
2. Refactor `app/services/firebase_service.py` to use repositories and provide pure service-level methods.
3. Remove Realtime DB dual-write complexity and anchor directly on Cloud Firestore with local mock adapter.

### Phase 2: Domain Logic, Badminton & Validation (P0)
1. Implement strict Pydantic input validators (`app/models/schemas.py`).
2. Add first-class Badminton tracking in `ActivityService` (`/badminton 2 matches`, sets, calories).
3. Add missing Telegram commands: `/help`, `/profile`, `/progress`.
4. Ensure timezone conversions (`Asia/Jakarta`) for date strings and daily summaries.

### Phase 3: AI Structuring & Confirmation Pipeline (P1)
1. Update `VisionService` and `NutritionAnalyzer` to output min/max ranges and confidence scores (0.0–1.0).
2. Clean up confirmation UI with TTL cache to prevent memory leaks.
3. Implement `UserContextSummary` in `AICoachService`.

### Phase 4: Security, Observability & Full Test Suite (P0)
1. Add MIME type & file size validation for photos.
2. Add credential-redacting logging filter.
3. Build comprehensive test suite in `tests/` covering validation, repositories, nutrition, badminton, sleep, water, and handlers.
4. Run static checks (`ruff`, `pytest`).
5. Create `API_REFERENCE.md`, `DATABASE_GUIDE.md`, and `TESTING_GUIDE.md`.
