from app.services.activity_service import activity_service


def test_badminton_command_parsing():
    log = activity_service.parse_activity_command("badminton", "2 matches", 12345, 75.0)
    assert log.activity_type == "badminton"
    assert log.matches == 2
    assert log.duration_minutes == 50.0  # 2 * 25 mins
    assert log.estimated_calories > 200
    assert log.calories_min is not None
    assert log.calories_max is not None
    assert log.calories_min < log.calories_max


def test_badminton_sets_and_duration():
    log = activity_service.parse_activity_command("badminton", "3 match 3 set 60m", 12345, 75.0)
    assert log.activity_type == "badminton"
    assert log.matches == 3
    assert log.sets == 3
    assert log.duration_minutes == 60.0


def test_walk_command_parsing():
    log = activity_service.parse_activity_command("walk", "6 km", 12345, 75.0)
    assert log.activity_type == "walking"
    assert log.distance_km == 6.0
    assert log.steps == int(6.0 * 1350)
    assert log.estimated_calories > 150


def test_run_command_parsing():
    log = activity_service.parse_activity_command("run", "5 km 35m", 12345, 75.0)
    assert log.activity_type == "running"
    assert log.distance_km == 5.0
    assert log.duration_minutes == 35.0
    assert log.pace_min_per_km == 7.0
    assert log.estimated_calories > 250
