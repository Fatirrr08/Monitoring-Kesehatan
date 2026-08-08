# FitTrack AI — Testing & Quality Assurance Guide

## 1. Running the Automated Test Suite

Run tests via `pytest`:
```bash
source .venv/bin/activate
pytest -v
```

### Coverage by Module:
- `tests/test_validation.py`: Pydantic boundary checks for age, height (100–250 cm), weight (20–300 kg), water (0–10,000 ml), sleep duration, and activity models.
- `tests/test_activities.py`: Badminton command parsing (matches, sets, duration, calorie ranges), walking, running, and skipping.
- `tests/test_food_analysis.py`: Structured AI food parsing, confidence scoring, and uncertainty range formatting.
- `tests/test_firebase_service.py`: User creation, profile updates, food logging, weight tracking, water hydration, daily score aggregation, and storage fallback.
- `tests/test_nutrition.py`: Indonesian food database lookup, natural vs added sugar differentiation (e.g. jambu biji 0g added sugar vs teh manis), and ASCII macro progress bars.
- `tests/test_sleep.py`: Sleep duration calculation across midnight shifts and consistency evaluations.
- `tests/test_water.py`: Water progress bar visualization.
- `tests/test_handlers.py`: Router registrations and Telegram bot initialization.

---

## 2. Code Quality & Linting

Run `ruff` to ensure clean PEP 8 and Pythonic standards:
```bash
source .venv/bin/activate
ruff check .
```
