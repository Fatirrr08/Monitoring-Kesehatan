import pytest
from app.models.schemas import (
    UserProfile,
    UserGoals,
    UserDocument,
    FoodLog,
    ActivityLog,
    WeightLog,
    SleepLog,
    WaterLog,
    DailySummary,
)


def test_user_profile_defaults():
    profile = UserProfile()
    assert profile.age == 20
    assert profile.height_cm == 175.0
    assert profile.current_weight_kg == 75.0
    assert profile.target_weight_kg == 70.0
    assert "chest" in profile.main_muscle_focus
    assert "arms" in profile.main_muscle_focus
    assert "shoulders" in profile.main_muscle_focus
    assert "core" in profile.main_muscle_focus
    assert profile.diet_preference.reduce_added_sugar is True


def test_user_goals_defaults():
    goals = UserGoals()
    assert goals.goal_type == "recomposition"
    assert goals.protein_target_min_g == 90.0
    assert goals.protein_target_max_g == 120.0
    assert goals.added_sugar_max_g == 25.0
    assert goals.daily_calories_target == 2100


def test_food_log_schema():
    log = FoodLog(
        food_log_id="test_food_1",
        telegram_user_id=123456,
        food_name="Nasi Putih + Dada Ayam",
        calories=360,
        protein_g=34.0,
        carbs_g=43.0,
        fat_g=4.0,
        total_sugar_g=0.1,
        added_sugar_g=0.0,
    )
    assert log.calories == 360
    assert log.protein_g == 34.0
    assert log.added_sugar_g == 0.0


def test_activity_log_schema():
    log = ActivityLog(
        activity_id="act_1",
        telegram_user_id=123456,
        activity_type="running",
        distance_km=5.0,
        duration_minutes=35.0,
        estimated_calories=360,
    )
    assert log.activity_type == "running"
    assert log.distance_km == 5.0
