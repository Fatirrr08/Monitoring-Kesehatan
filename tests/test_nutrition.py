import pytest
from app.services.food_database import search_food, get_food_by_key, INDONESIAN_FOOD_DATABASE
from app.services.nutrition_service import nutrition_service
from app.models.schemas import DailySummary


def test_indonesian_food_database_contains_staples():
    expected_keys = [
        "nasi_putih", "nasi_goreng", "nasi_bakar", "bubur_ayam",
        "ayam_crispy", "ayam_kemangi", "dada_ayam", "tongkol",
        "ikan_teri", "telur", "telur_puyuh", "tahu", "tempe",
        "opor", "ceker", "bakso", "mie_ayam", "gorengan",
        "sayur_sop", "timun", "tomat", "selada", "jambu_merah",
        "susu", "almond_milk", "americano", "teh", "jamu_kunyit_asam"
    ]
    for key in expected_keys:
        assert key in INDONESIAN_FOOD_DATABASE, f"Missing {key} in food database"


def test_jambu_merah_natural_sugar_not_added_sugar():
    jambu = get_food_by_key("jambu_merah")
    assert jambu is not None
    assert jambu.total_sugar_g > 0.0
    assert jambu.added_sugar_g == 0.0  # Whole fruit natural sugar is NOT added sugar


def test_teh_manis_has_added_sugar():
    teh = get_food_by_key("teh")
    assert teh is not None
    assert teh.added_sugar_g > 0.0


def test_search_food():
    results = search_food("ayam")
    assert len(results) >= 4
    names = [r.name for r in results]
    assert any("Dada Ayam" in n for n in names)


def test_protein_bar_rendering():
    bar = nutrition_service.render_protein_bar(60.0, 120.0, length=10)
    assert bar == "█████░░░░░"
