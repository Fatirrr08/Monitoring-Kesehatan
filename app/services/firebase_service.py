"""Firebase Service Layer for FitTrack AI.

Orchestrates business workflows and delegates persistence to repositories.
All Firestore and Storage operations MUST go through this layer.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from app.models.schemas import (
    ActivityLog,
    DailySummary,
    FoodLog,
    SleepLog,
    UserDocument,
    UserGoals,
    UserProfile,
    UserSettings,
    WaterLog,
    WeightLog,
    today_str,
    utc_now,
)
from app.repositories.activity_repository import activity_repository
from app.repositories.base import _in_memory_store, get_storage_bucket
from app.repositories.food_repository import food_repository
from app.repositories.sleep_repository import sleep_repository
from app.repositories.summary_repository import summary_repository
from app.repositories.user_repository import user_repository
from app.repositories.water_repository import water_repository
from app.repositories.weight_repository import weight_repository
from app.utils.logger import logger


class FirebaseService:
    """High-level application service orchestrating Firestore and Storage."""

    def __init__(self):
        self._user_repo = user_repository
        self._food_repo = food_repository
        self._activity_repo = activity_repository
        self._weight_repo = weight_repository
        self._sleep_repo = sleep_repository
        self._water_repo = water_repository
        self._summary_repo = summary_repository

    @property
    def is_connected_to_firebase(self) -> bool:
        return self._user_repo.is_live

    # =========================================================================
    # USER & PROFILE OPERATIONS
    # =========================================================================

    async def create_user(
        self,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        profile: UserProfile | None = None,
        goals: UserGoals | None = None,
        user_settings: UserSettings | None = None,
    ) -> UserDocument:
        return await self._user_repo.create_user(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            profile=profile,
            goals=goals,
            settings=user_settings,
        )

    async def get_user(self, telegram_user_id: int) -> UserDocument | None:
        return await self._user_repo.get_user(telegram_user_id)

    async def update_profile(
        self,
        telegram_user_id: int,
        profile_data: dict[str, Any],
    ) -> UserDocument:
        return await self._user_repo.update_profile(telegram_user_id, profile_data)

    async def update_goals(
        self,
        telegram_user_id: int,
        goals_data: dict[str, Any],
    ) -> UserDocument:
        return await self._user_repo.update_goals(telegram_user_id, goals_data)

    # =========================================================================
    # FOOD LOGS
    # =========================================================================

    async def log_food(self, food_log: FoodLog) -> FoodLog:
        saved = await self._food_repo.save_food_log(food_log)
        await self._recalculate_daily_summary(food_log.telegram_user_id, food_log.logged_date)
        return saved

    async def get_food_logs(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
        limit: int = 50,
    ) -> list[FoodLog]:
        return await self._food_repo.get_food_logs_by_date(telegram_user_id, date_str, limit)

    # =========================================================================
    # ACTIVITIES
    # =========================================================================

    async def log_activity(self, activity_log: ActivityLog) -> ActivityLog:
        saved = await self._activity_repo.save_activity(activity_log)
        await self._recalculate_daily_summary(activity_log.telegram_user_id, activity_log.activity_date)
        return saved

    async def get_activity_logs(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
        limit: int = 30,
    ) -> list[ActivityLog]:
        return await self._activity_repo.get_activities_by_date(telegram_user_id, date_str, limit)

    # =========================================================================
    # WEIGHT TRACKING
    # =========================================================================

    async def log_weight(
        self,
        telegram_user_id: int,
        weight_kg: float,
        date_str: str | None = None,
    ) -> WeightLog:
        user = await self.get_user(telegram_user_id)
        start_weight = user.profile.current_weight_kg if user else 75.0
        target_weight = user.profile.target_weight_kg if user else 70.0

        history = await self.get_weight_history(telegram_user_id, limit=1)
        prev_diff = None
        if history:
            prev_diff = round(weight_kg - history[0].weight_kg, 2)

        weight_id = f"w_{date_str or today_str()}_{uuid.uuid4().hex[:6]}"
        diff_from_start = round(weight_kg - start_weight, 2)

        weight_log = WeightLog(
            weight_id=weight_id,
            telegram_user_id=telegram_user_id,
            weight_kg=weight_kg,
            starting_weight_kg=start_weight,
            target_weight_kg=target_weight,
            difference_from_start_kg=diff_from_start,
            difference_from_previous_kg=prev_diff,
            logged_date=date_str or today_str(),
            created_at=utc_now(),
        )

        saved = await self._weight_repo.save_weight(weight_log)
        await self.update_profile(telegram_user_id, {"current_weight_kg": weight_kg})
        return saved

    async def get_weight_history(
        self,
        telegram_user_id: int,
        limit: int = 30,
    ) -> list[WeightLog]:
        return await self._weight_repo.get_weight_history(telegram_user_id, limit)

    # =========================================================================
    # SLEEP TRACKING
    # =========================================================================

    async def log_sleep(self, sleep_log: SleepLog) -> SleepLog:
        saved = await self._sleep_repo.save_sleep(sleep_log)
        await self._recalculate_daily_summary(sleep_log.telegram_user_id, sleep_log.sleep_date)
        return saved

    async def get_sleep_logs(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
        limit: int = 7,
    ) -> list[SleepLog]:
        return await self._sleep_repo.get_sleep_logs_by_date(telegram_user_id, date_str, limit)

    # =========================================================================
    # WATER TRACKING
    # =========================================================================

    async def log_water(
        self,
        telegram_user_id: int,
        amount_ml: int,
        date_str: str | None = None,
    ) -> WaterLog:
        water_id = f"water_{date_str or today_str()}_{uuid.uuid4().hex[:6]}"
        water_log = WaterLog(
            water_log_id=water_id,
            telegram_user_id=telegram_user_id,
            amount_ml=amount_ml,
            logged_date=date_str or today_str(),
            created_at=utc_now(),
        )

        saved = await self._water_repo.save_water(water_log)
        await self._recalculate_daily_summary(telegram_user_id, water_log.logged_date)
        return saved

    async def get_water_logs(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
    ) -> list[WaterLog]:
        return await self._water_repo.get_water_logs_by_date(telegram_user_id, date_str)

    # =========================================================================
    # DAILY SUMMARY
    # =========================================================================

    async def get_daily_summary(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
    ) -> DailySummary:
        target_date = date_str or today_str()
        summary = await self._summary_repo.get_daily_summary(telegram_user_id, target_date)
        if summary is None:
            summary = await self._recalculate_daily_summary(telegram_user_id, target_date)
        return summary

    async def _recalculate_daily_summary(
        self,
        telegram_user_id: int,
        target_date: str,
    ) -> DailySummary:
        user = await self.get_user(telegram_user_id)
        if not user:
            user = await self.create_user(telegram_user_id)

        foods = await self.get_food_logs(telegram_user_id, target_date)
        activities = await self.get_activity_logs(telegram_user_id, target_date)
        sleeps = await self.get_sleep_logs(telegram_user_id, target_date)
        waters = await self.get_water_logs(telegram_user_id, target_date)

        # Aggregate Nutrition
        total_cals = sum(f.calories for f in foods)
        total_prot = round(sum(f.protein_g for f in foods), 1)
        total_carbs = round(sum(f.carbs_g for f in foods), 1)
        total_fat = round(sum(f.fat_g for f in foods), 1)
        total_sugar = round(sum(f.total_sugar_g for f in foods), 1)
        added_sugar = round(sum(f.added_sugar_g or 0.0 for f in foods), 1)
        total_fiber = round(sum(f.fiber_g for f in foods), 1)

        # Aggregate Activity
        burned_cals = sum(a.estimated_calories for a in activities)
        active_mins = sum(a.duration_minutes or 0.0 for a in activities)
        act_summary = ", ".join(f"{a.activity_type.title()}" for a in activities) if activities else None

        # Aggregate Sleep
        latest_sleep = sleeps[0] if sleeps else None
        sleep_dur = latest_sleep.duration_hours if latest_sleep else 0.0
        sleep_sum = f"{sleep_dur}h ({latest_sleep.bedtime}-{latest_sleep.wake_time})" if latest_sleep else None

        # Aggregate Water
        total_water = sum(w.amount_ml for w in waters)

        # Calculate Score breakdown
        score_breakdown = {}
        score_val = 0.0

        cal_diff = abs(total_cals - user.goals.daily_calories_target)
        if total_cals == 0:
            score_breakdown["nutrition"] = "⚪"
        elif cal_diff <= 250:
            score_breakdown["nutrition"] = "🟢"
            score_val += 2.0
        elif cal_diff <= 500:
            score_breakdown["nutrition"] = "🟡"
            score_val += 1.2
        else:
            score_breakdown["nutrition"] = "🟠"
            score_val += 0.8

        if total_prot >= user.goals.protein_target_min_g:
            score_breakdown["protein"] = "🟢"
            score_val += 2.5
        elif total_prot >= (user.goals.protein_target_min_g * 0.7):
            score_breakdown["protein"] = "🟡"
            score_val += 1.5
        else:
            score_breakdown["protein"] = "⚪" if total_prot == 0 else "🟠"
            score_val += 0.5

        if added_sugar <= user.goals.added_sugar_max_g:
            score_breakdown["sugar"] = "🟢"
            score_val += 2.0
        else:
            score_breakdown["sugar"] = "🟡"
            score_val += 1.0

        if active_mins >= 30 or burned_cals >= 250:
            score_breakdown["activity"] = "🟢"
            score_val += 1.5
        elif active_mins > 0:
            score_breakdown["activity"] = "🟡"
            score_val += 1.0
        else:
            score_breakdown["activity"] = "⚪"

        if 7.0 <= sleep_dur <= 9.0:
            score_breakdown["sleep"] = "🟢"
            score_val += 1.0
        elif sleep_dur > 0:
            score_breakdown["sleep"] = "🟡"
            score_val += 0.6
        else:
            score_breakdown["sleep"] = "⚪"

        if total_water >= user.goals.water_target_ml:
            score_breakdown["hydration"] = "🟢"
            score_val += 1.0
        elif total_water >= (user.goals.water_target_ml * 0.6):
            score_breakdown["hydration"] = "🟡"
            score_val += 0.6
        else:
            score_breakdown["hydration"] = "⚪"

        summary = DailySummary(
            summary_date=target_date,
            telegram_user_id=telegram_user_id,
            total_calories=total_cals,
            target_calories=user.goals.daily_calories_target,
            total_protein_g=total_prot,
            target_protein_min_g=user.goals.protein_target_min_g,
            target_protein_max_g=user.goals.protein_target_max_g,
            total_carbs_g=total_carbs,
            total_fat_g=total_fat,
            total_sugar_g=total_sugar,
            added_sugar_g=added_sugar,
            added_sugar_max_g=user.goals.added_sugar_max_g,
            total_fiber_g=total_fiber,
            meal_count=len(foods),
            active_calories_burned=burned_cals,
            active_minutes=active_mins,
            activity_count=len(activities),
            activity_summary=act_summary,
            sleep_hours=sleep_dur,
            sleep_bedtime=latest_sleep.bedtime if latest_sleep else None,
            sleep_wake_time=latest_sleep.wake_time if latest_sleep else None,
            sleep_summary=sleep_sum,
            total_water_ml=total_water,
            target_water_ml=user.goals.water_target_ml,
            daily_score=round(min(score_val, 10.0), 1),
            daily_score_breakdown=score_breakdown,
            ai_feedback="Pola makan dan aktivitas hari ini terpantau baik.",
            updated_at=utc_now(),
        )

        return await self._summary_repo.save_daily_summary(summary)

    # =========================================================================
    # FIREBASE STORAGE OPERATIONS
    # =========================================================================

    async def upload_food_image(
        self,
        telegram_user_id: int,
        image_bytes: bytes,
        file_extension: str = "jpg",
    ) -> dict[str, str]:
        """Upload validated food image to Storage: food-images/{user_id}/YYYY/MM/{image_id}.jpg."""
        now = datetime.now(timezone.utc)
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")
        image_id = f"img_{uuid.uuid4().hex}"
        storage_path = f"food-images/{telegram_user_id}/{year_str}/{month_str}/{image_id}.{file_extension}"

        def _sync_upload():
            bucket = get_storage_bucket()
            if bucket:
                try:
                    blob = bucket.blob(storage_path)
                    blob.upload_from_string(image_bytes, content_type=f"image/{file_extension}")
                    try:
                        blob.make_public()
                        public_url = blob.public_url
                    except Exception:
                        public_url = f"https://storage.googleapis.com/{bucket.name}/{storage_path}"
                    return {
                        "storage_path": storage_path,
                        "image_url": public_url,
                        "image_id": image_id,
                    }
                except Exception as e:
                    logger.warning(f"Storage upload error ({e}). Using mock path.")

            mock_url = f"https://mock-storage.firebase.local/{storage_path}"
            _in_memory_store[f"storage:{storage_path}"] = image_bytes
            return {
                "storage_path": storage_path,
                "image_url": mock_url,
                "image_id": image_id,
            }

        return await asyncio.to_thread(_sync_upload)

    async def save_food_analysis(
        self,
        telegram_user_id: int,
        analysis_data: dict[str, Any],
    ) -> FoodLog:
        food_log_id = f"food_{today_str()}_{uuid.uuid4().hex[:6]}"
        food_log = FoodLog(
            food_log_id=food_log_id,
            telegram_user_id=telegram_user_id,
            food_name=analysis_data.get("food_name", "Makanan Campur"),
            meal_type=analysis_data.get("meal_type", "lunch"),
            portion=analysis_data.get("portion", "1 porsi"),
            calories=analysis_data.get("calories", 0),
            calories_min=analysis_data.get("calories_min"),
            calories_max=analysis_data.get("calories_max"),
            protein_g=analysis_data.get("protein_g", 0.0),
            carbs_g=analysis_data.get("carbs_g", 0.0),
            fat_g=analysis_data.get("fat_g", 0.0),
            total_sugar_g=analysis_data.get("total_sugar_g", 0.0),
            added_sugar_g=analysis_data.get("added_sugar_g"),
            fiber_g=analysis_data.get("fiber_g", 0.0),
            sodium_mg=analysis_data.get("sodium_mg", 0.0),
            confidence=analysis_data.get("confidence", 0.7),
            source=analysis_data.get("source", "photo_ai"),
            image_reference=analysis_data.get("storage_path"),
            image_url=analysis_data.get("image_url"),
            notes=analysis_data.get("notes"),
            assumptions=analysis_data.get("assumptions", []),
            logged_date=today_str(),
            created_at=utc_now(),
        )
        return await self.log_food(food_log)


firebase_service = FirebaseService()
