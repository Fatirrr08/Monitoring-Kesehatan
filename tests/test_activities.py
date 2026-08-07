import pytest
from app.services.activity_service import activity_service


def test_walking_calculation():
    log = activity_service.parse_activity_command("walk", "6 km", 123456, 75.0)
    assert log.distance_km == 6.0
    assert log.estimated_calories > 200
    assert log.steps > 7000


def test_running_calculation():
    log = activity_service.parse_activity_command("run", "5 km 42m", 123456, 75.0)
    assert log.distance_km == 5.0
    assert log.duration_minutes == 42.0
    assert log.pace_min_per_km == 8.4
    assert log.estimated_calories > 300


def test_skipping_calculation():
    log = activity_service.parse_activity_command("skipping", "800", 123456, 75.0)
    assert log.repetitions == 800
    assert log.estimated_calories > 50


def test_workout_calculation():
    log = activity_service.parse_activity_command("workout", "35m", 123456, 75.0)
    assert log.duration_minutes == 35.0
    assert log.estimated_calories > 150
