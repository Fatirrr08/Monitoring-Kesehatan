from app.services.sleep_service import sleep_service


def test_sleep_parsing_overnight():
    bed, wake, dur = sleep_service.parse_sleep_input("23:30 07:30")
    assert bed == "23:30"
    assert wake == "07:30"
    assert dur == 8.0


def test_sleep_parsing_shift():
    bed, wake, dur = sleep_service.parse_sleep_input("07:00 15:00")
    assert bed == "07:00"
    assert wake == "15:00"
    assert dur == 8.0


def test_sleep_evaluation_duration_vs_timing():
    log = sleep_service.evaluate_sleep(123456, "07:00 15:00")
    assert log.duration_hours == 8.0
    assert "optimal" in log.duration_assessment
    assert "shift" in log.timing_assessment
