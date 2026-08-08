import random

import pytest

from app.models.schemas import FoodLog, today_str
from app.services.firebase_service import firebase_service


@pytest.mark.asyncio
async def test_user_creation_and_retrieval():
    user_id = random.randint(1000000, 9999999)
    user = await firebase_service.create_user(telegram_user_id=user_id, username="testuser")
    assert user.telegram_user_id == user_id
    assert user.profile.age == 20
    assert user.profile.current_weight_kg == 75.0

    fetched = await firebase_service.get_user(user_id)
    assert fetched is not None
    assert fetched.telegram_user_id == user_id


@pytest.mark.asyncio
async def test_update_profile():
    user_id = random.randint(1000000, 9999999)
    await firebase_service.create_user(telegram_user_id=user_id)
    updated = await firebase_service.update_profile(user_id, {"age": 22, "current_weight_kg": 74.0})
    assert updated.profile.age == 22
    assert updated.profile.current_weight_kg == 74.0


@pytest.mark.asyncio
async def test_food_and_daily_summary_aggregation():
    user_id = random.randint(1000000, 9999999)
    await firebase_service.create_user(telegram_user_id=user_id)
    food_log = FoodLog(
        food_log_id=f"test_f_{user_id}",
        telegram_user_id=user_id,
        food_name="Dada Ayam Panggang",
        portion="100g",
        calories=165,
        protein_g=31.0,
        carbs_g=0.0,
        fat_g=3.6,
        total_sugar_g=0.0,
        added_sugar_g=0.0,
        logged_date=today_str(),
    )
    await firebase_service.log_food(food_log)

    logs = await firebase_service.get_food_logs(user_id, today_str())
    assert len(logs) >= 1
    assert logs[0].calories == 165

    summary = await firebase_service.get_daily_summary(user_id, today_str())
    assert summary.total_calories == 165
    assert summary.total_protein_g == 31.0


@pytest.mark.asyncio
async def test_weight_logging():
    user_id = random.randint(1000000, 9999999)
    await firebase_service.create_user(telegram_user_id=user_id)
    w_log = await firebase_service.log_weight(user_id, 74.2)
    assert w_log.weight_kg == 74.2
    assert w_log.starting_weight_kg == 75.0
    assert w_log.difference_from_start_kg == -0.8

    history = await firebase_service.get_weight_history(user_id)
    assert len(history) >= 1
    assert history[0].weight_kg == 74.2


@pytest.mark.asyncio
async def test_water_logging():
    user_id = random.randint(1000000, 9999999)
    await firebase_service.create_user(telegram_user_id=user_id)
    await firebase_service.log_water(user_id, 500)
    await firebase_service.log_water(user_id, 250)

    waters = await firebase_service.get_water_logs(user_id)
    assert sum(w.amount_ml for w in waters) == 750

    summary = await firebase_service.get_daily_summary(user_id)
    assert summary.total_water_ml == 750


@pytest.mark.asyncio
async def test_storage_upload_mock_fallback():
    user_id = random.randint(1000000, 9999999)
    res = await firebase_service.upload_food_image(user_id, b"fake_image_bytes", "jpg")
    assert "storage_path" in res
    assert f"food-images/{user_id}" in res["storage_path"]
