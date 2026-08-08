import pytest
from pydantic import ValidationError

from app.models.schemas import ActivityLog, SleepLog, UserProfile, WaterLog


def test_user_profile_validation_success():
    profile = UserProfile(
        age=22,
        height_cm=175.0,
        current_weight_kg=74.5,
        target_weight_kg=70.0,
    )
    assert profile.age == 22
    assert profile.height_cm == 175.0
    assert profile.current_weight_kg == 74.5


def test_user_profile_validation_failure_weight():
    # Weight below 20kg must fail
    with pytest.raises(ValidationError):
        UserProfile(current_weight_kg=15.0)

    # Weight above 300kg must fail
    with pytest.raises(ValidationError):
        UserProfile(current_weight_kg=350.0)


def test_user_profile_validation_failure_height():
    with pytest.raises(ValidationError):
        UserProfile(height_cm=80.0)


def test_water_validation_limits():
    # 500ml is valid
    w = WaterLog(water_log_id="w1", telegram_user_id=123, amount_ml=500)
    assert w.amount_ml == 500

    # Over 10,000ml in single entry must fail
    with pytest.raises(ValidationError):
        WaterLog(water_log_id="w2", telegram_user_id=123, amount_ml=15000)


def test_sleep_validation_limits():
    # 7.5h is valid
    s = SleepLog(sleep_id="s1", telegram_user_id=123, duration_hours=7.5)
    assert s.duration_hours == 7.5

    # Over 24h must fail
    with pytest.raises(ValidationError):
        SleepLog(sleep_id="s2", telegram_user_id=123, duration_hours=28.0)


def test_activity_validation_limits():
    act = ActivityLog(
        activity_id="a1",
        telegram_user_id=123,
        activity_type="badminton",
        matches=2,
        sets=2,
        duration_minutes=45.0,
        estimated_calories=300,
    )
    assert act.matches == 2
    assert act.sets == 2
