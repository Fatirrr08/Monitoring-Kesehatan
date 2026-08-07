from datetime import datetime, timezone
from typing import List, Optional, Literal, Dict, Any
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
    age: int = Field(default=20, ge=10, le=100, description="Age in years")
    gender: Literal["male", "female", "other"] = Field(default="male")
    height_cm: float = Field(default=175.0, ge=50.0, le=250.0, description="Height in cm")
    current_weight_kg: float = Field(default=75.0, ge=20.0, le=300.0, description="Current weight in kg")
    target_weight_kg: float = Field(default=70.0, ge=20.0, le=300.0, description="Target weight in kg")
    activity_level: str = Field(default="moderate", description="Activity level: light, moderate, high")
    main_muscle_focus: List[str] = Field(
        default_factory=lambda: ["chest", "arms", "shoulders", "core"],
        description="Muscle groups targeted for recomposition"
    )
    preferred_exercises: List[str] = Field(
        default_factory=lambda: ["walking", "running", "skipping", "home workout"],
        description="Preferred exercise types"
    )
    diet_preference: DietPreference = Field(default_factory=DietPreference)


class UserGoals(BaseModel):
    goal_type: Literal["recomposition", "fat_loss", "muscle_gain", "maintenance"] = Field(
        default="recomposition",
        description="Primary fitness goal: fat loss + muscle gain"
    )
    daily_calories_target: int = Field(default=2100, description="Daily caloric budget in kcal")
    protein_target_min_g: float = Field(default=90.0, description="Initial min protein in grams")
    protein_target_max_g: float = Field(default=120.0, description="Initial max protein in grams")
    carbs_target_g: float = Field(default=240.0, description="Carbohydrates target in grams")
    fat_target_g: float = Field(default=60.0, description="Fat target in grams")
    added_sugar_max_g: float = Field(default=25.0, description="Maximum added sugar in grams")
    fiber_target_g: float = Field(default=25.0, description="Daily fiber target in grams")
    water_target_ml: int = Field(default=2500, description="Daily water target in ml")
    sleep_target_hours: float = Field(default=8.0, description="Daily sleep target in hours")
    weekly_workout_days: int = Field(default=4, description="Target workout sessions per week")


class UserSettings(BaseModel):
    timezone: str = Field(default="Asia/Jakarta")
    language: str = Field(default="id")
    reminders_enabled: bool = Field(default=True)
    daily_score_notifications: bool = Field(default=True)


class UserDocument(BaseModel):
    telegram_user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    profile: UserProfile = Field(default_factory=UserProfile)
    goals: UserGoals = Field(default_factory=UserGoals)
    settings: UserSettings = Field(default_factory=UserSettings)
    created_at: str = Field(default_factory=utc_now)
    updated_at: str = Field(default_factory=utc_now)


class FoodItemSubEntry(BaseModel):
    name: str
    estimated_grams: float = 100.0
    calories: int = 0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    sugar_g: float = 0.0
    is_added_sugar: bool = False


class FoodLog(BaseModel):
    food_log_id: str
    telegram_user_id: int
    food_name: str
    meal_type: Literal["breakfast", "lunch", "dinner", "snack"] = "lunch"
    portion: str = "1 porsi"
    calories: int = 0
    protein_g: float = 0.0
    carbs_g: float = 0.0
    fat_g: float = 0.0
    total_sugar_g: float = 0.0
    added_sugar_g: float = 0.0
    fiber_g: float = 0.0
    sodium_mg: float = 0.0
    confidence: Literal["high", "medium", "low", "manual"] = "manual"
    source: Literal["manual_text", "preset", "photo_ai", "nutrition_label_ocr"] = "manual_text"
    image_reference: Optional[str] = None
    image_url: Optional[str] = None
    notes: Optional[str] = None
    items: List[FoodItemSubEntry] = Field(default_factory=list)
    logged_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class ActivityLog(BaseModel):
    activity_id: str
    telegram_user_id: int
    activity_type: Literal["walking", "running", "skipping", "home_workout", "cycling", "other"] = "walking"
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
    repetitions: Optional[int] = None
    steps: Optional[int] = None
    pace_min_per_km: Optional[float] = None
    estimated_calories: int = 0
    source: Literal["command", "screenshot_ocr", "manual"] = "command"
    notes: Optional[str] = None
    activity_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class WeightLog(BaseModel):
    weight_id: str
    telegram_user_id: int
    weight_kg: float
    starting_weight_kg: float = 75.0
    target_weight_kg: float = 70.0
    difference_from_start_kg: float = 0.0
    difference_from_previous_kg: Optional[float] = None
    logged_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class SleepLog(BaseModel):
    sleep_id: str
    telegram_user_id: int
    bedtime: str = "23:00"  # HH:MM
    wake_time: str = "07:00"  # HH:MM
    duration_hours: float = 8.0
    quality_rating: Optional[int] = Field(default=None, ge=1, le=5)
    timing_assessment: str = "consistent"
    duration_assessment: str = "optimal"
    notes: Optional[str] = None
    sleep_date: str = Field(default_factory=today_str)
    created_at: str = Field(default_factory=utc_now)


class WaterLog(BaseModel):
    water_log_id: str
    telegram_user_id: int
    amount_ml: int = 250
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
    sleep_hours: float = 0.0
    sleep_bedtime: Optional[str] = None
    sleep_wake_time: Optional[str] = None
    total_water_ml: int = 0
    target_water_ml: int = 2500
    daily_score: float = 0.0
    daily_score_breakdown: Dict[str, str] = Field(default_factory=dict)
    ai_feedback: Optional[str] = None
    updated_at: str = Field(default_factory=utc_now)


class AIChatMessage(BaseModel):
    conversation_id: str
    telegram_user_id: int
    user_message: str
    coach_response: str
    context_snapshot: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)
