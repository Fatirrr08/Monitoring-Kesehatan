import pytest

from app.ai.vision import vision_service
from app.models.schemas import FoodAnalysis


@pytest.mark.asyncio
async def test_fallback_food_analysis_structured():
    dummy_bytes = b"\xff\xd8\xff\xe0dummyjpegimagebytes"
    analysis = await vision_service.analyze_food_image(dummy_bytes)

    assert isinstance(analysis, FoodAnalysis)
    assert analysis.calories_min is not None
    assert analysis.calories_max is not None
    assert analysis.calories_min <= analysis.calories_max
    assert analysis.protein_g >= 20.0
    assert 0.0 <= analysis.overall_confidence <= 1.0
    assert len(analysis.assumptions) > 0


def test_format_food_analysis_card():
    analysis = FoodAnalysis(
        food_name="Nasi Padang Ayam Pop",
        portion="1 porsi",
        calories=550,
        calories_min=500,
        calories_max=600,
        protein_g=30.0,
        carbs_g=60.0,
        fat_g=20.0,
        total_sugar_g=2.0,
        added_sugar_g=0.0,
        overall_confidence=0.85,
        assumptions=["Ayam pop tanpa kuah gulai berlebih"],
    )

    card = vision_service.format_food_analysis_card(analysis)
    assert "Nasi Padang Ayam Pop" in card
    assert "500–600 kcal" in card
    assert "🟢 High" in card
    assert "Ayam pop tanpa kuah gulai berlebih" in card
