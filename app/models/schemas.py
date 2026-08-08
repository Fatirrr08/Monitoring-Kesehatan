from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def today_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class DietPreference(BaseModel):
    reduce_added_sugar: bool = Field(default=True, description="Target <= 25g added sugar")
    food_style: str = Field(default="normal affordable Indonesian food", description="Cuisine preference")
    no_extreme_dieting: bool = Field(default=True, description="Sustainable nutrition without extreme deficit")


class UserProfile(BaseModel):
    age: int = Field(default=20, ge=10, le=120, description="Age in years (10–120)")
    gender: Literal["male", "female", "other"] = Field(default="male")
    height_cm: float = Field(default=175.0, ge=100.0, le=250.0, description="Height in cm (100–250)")
    current_weight_kg: float = Field(default=75.0, ge=20.0, le=300.0, description="Current weight in kg (20–300)")
    target_weight_kg: float = Field(default=70.0, ge=20.0, le=300.0, description="Target weight in kg (20–300)")
    activity_level: str = Field(default="moderate", description="Activity level: light, moderate, high")
    main_muscle_focus: list[str] = Field(
        default_factory=lambda: ["chest", "arms", "shoulders", "core"],
        description="Muscle groups targeted for recomposition"
    )
    preferred_exercises: list[str] = Field(
        default_factory=lambda: ["walking", "running", "badminton", "skipping", "home workout"],
        description="Preferred exercise types"
    )
    diet_preference: DietPreference = Field(default_factory=DietPreference)


class UserGoals(BaseModel):
    goal_type: Literal["recomposition", "fat_loss", "muscle_gain", "maintenance"] = Field(
        default="recomposition",
        description="Primary fitness goal: fat loss + muscle gain"
    )
    daily_calories_target: int = Field(default=2100, ge=1000, le=5000, description="Daily caloric budget in kcal")
    protein_target_min_g: float = Field(default=90.0, ge=30.0, le=300.0, description="Initial min protein in grams")
    protein_target_max_g: float = Field(default=120.0, ge=30.0, le=350.0, description="Initial max protein in grams")
    carbs_target_g: float = Field(default=240.0, ge=20.0, le=600.0, description="Carbohydrates target in grams")
    fat_target_g: float = Field(default=60.0, ge=10.0, le=200.0, description="Fat target in grams")
    added_sugar_max_g: float = Field(default=25.0, ge=0.0, le=100.0, description="Maximum added sugar in grams")
    fiber_target_g: float = Field(default=25.0, ge=5.0, le=80.0, description="Daily fiber target in grams")
    water_target_ml: int = Field(default=2500, ge=500, le=10000, description="Daily water target in ml")
    sleep_target_hours: float = Field(default=8.0, ge=4.0, le=14.0, description="Daily sleep target in hours")
    weekly_workout_days: int = Field(default=4, ge=1, le=7, description="Target workout sessions per week")


class UserSettings(BaseModel):
    timezone: str = Field(default="Asia/Jakarta")
    language: str = Field(default="id")
    reminders_enabled: bool = Field(default=True)
    daily_score_notifications: bool = Field(default=True)


class UserDocument(BaseModel):
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    profile: UserProfile = Field(default_factory=UserProfile)
    goals: UserGoals = Field(default_factory=UserGoals)
    settings: UserSettings = Field(default_factory=UserSettings)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class FoodItemEstimate(BaseModel):
    name: str
    estimated_weight_g: float | None = None
    calories_min: int = 0
    calories_max: int = 0
    protein_g_min: float = 0.0
    protein_g_max: float = 0.0
    carbs_g_min: float = 0.0
    carbs_g_max: float = 0.0
    fat_g_min: float = 0.0
    fat_g_max: float = 0.0
    sugar_g_min: float = 0.0
    sugar_g_max: float = 0.0
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class FoodAnalysis(BaseModel):
    food_name: str
    portion: str = "1 porsi"
    foods: list[FoodItemEstimate] = Field(default_factory=list)
    calories: int = 0
    calories_min: int = 0
    calories_max: int = 0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    total_sugar_g: float = 0.0
    added_sugar_g: float | None = None  # None if unknown, 0.0 if fruit natural
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    overall_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    assumptions: list[str] = Field(default_factory=list)


class FoodLog(BaseModel):
    food_log_id: str
    telegram_user_id: int
    food_name: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = "lunch"
    portion: str = "1 porsi"
    calories: int = 0
    calories_min: int | None = None
    calories_max: int | None = None
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    total_sugar_g: float = 0.0
    added_sugar_g: float | None = None
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: Literal["manual_text", "preset", "photo_ai", "nutrition_label_ocr", "database"] = "manual_text"
    image_reference: str | None = None
    image_url: str | None = None
    notes: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    logged_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class ActivityLog(BaseModel):
    activity_id: str
    telegram_user_id: int
    activity_type: Literal["walking", "running", "badminton", "skipping", "home_workout", "cycling", "other"] = "walking"
    distance_km: float | None = Field(default=None, ge=0.0, le=200.0)
    duration_minutes: float | None = Field(default=None, ge=0.0, le=1440.0)
    matches: int | None = Field(default=None, ge=0, le=50, description="Badminton match count")
    sets: int | None = Field(default=None, ge=0, le=100, description="Badminton sets count")
    repetitions: int | None = Field(default=None, ge=0, le=100000)
    steps: int | None = Field(default=None, ge=0, le=200000)
    pace_min_per_km: float | None = None
    estimated_calories: int = Field(default=0, ge=0, le=10000)
    calories_min: int | None = None
    calories_max: int | None = None
    source: Literal["command", "screenshot_ocr", "manual"] = "command"
    notes: str | None = None
    activity_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class WeightLog(BaseModel):
    weight_id: str
    telegram_user_id: int
    weight_kg: float = Field(ge=20.0, le=300.0)
    starting_weight_kg: float = Field(default=75.0, ge=20.0, le=300.0)
    target_weight_kg: float = Field(default=70.0, ge=20.0, le=300.0)
    difference_from_start_kg: float = 0.0
    difference_from_previous_kg: float | None = None
    logged_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class SleepLog(BaseModel):
    sleep_id: str
    telegram_user_id: int
    bedtime: str = "23:00"  # HH:MM
    wake_time: str = "07:00"  # HH:MM
    duration_hours: float = Field(default=8.0, ge=0.0, le=24.0)
    quality_rating: int | None = Field(default=None, ge=1, le=5)
    timing_assessment: str = "consistent"
    duration_assessment: str = "optimal"
    notes: str | None = None
    sleep_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class WaterLog(BaseModel):
    water_log_id: str
    telegram_user_id: int
    amount_ml: int = Field(default=250, ge=0, le=10000)
    logged_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class DailySummary(BaseModel):
    summary_date: str
    telegram_user_id: int
    total_calories: int = 0
    target_calories: int = 2100
    total_protein_g: float = 0.0
    target_protein_min_g: float = 90.0
    target_protein_max_g: float = 120.0
    total_carbs_g: float = 0.0
    total_fat_g: float = 0.0
    total_sugar_g: float = 0.0
    added_sugar_g: float = 0.0
    added_sugar_max_g: float = 25.0
    total_fiber_g: float = 0.0
    meal_count: int = 0
    active_calories_burned: int = 0
    active_minutes: float = 0.0
    activity_count: int = 0
    activity_summary: str | None = None
    sleep_hours: float = 0.0
    sleep_bedtime: str | None = None
    sleep_wake_time: str | None = None
    sleep_summary: str | None = None
    total_water_ml: int = 0
    target_water_ml: int = 2500
    daily_score: float = 0.0
    daily_score_breakdown: dict[str, str] = Field(default_factory=dict)
    ai_feedback: str | None = None
    updated_at: str = Field(default_factory=utc_now)


class AIChatMessage(BaseModel):
    conversation_id: str
    telegram_user_id: int
    user_message: str
    coach_response: str
    context_snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)
