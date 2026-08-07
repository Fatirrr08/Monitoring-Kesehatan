import pytest
from app.utils.formatting import make_progress_bar


def test_water_progress_bar():
    # 1500 of 2500 is 60%
    bar = make_progress_bar(1500, 2500, length=10)
    assert bar == "██████░░░░"


def test_full_water_progress_bar():
    bar = make_progress_bar(2500, 2500, length=10)
    assert bar == "██████████"
