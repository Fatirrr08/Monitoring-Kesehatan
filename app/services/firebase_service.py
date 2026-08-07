"""Firebase Service Layer for FitTrack AI.

Supports Firebase Realtime Database and Cloud Firestore seamlessly.
All database and storage operations MUST go through this service layer.
"""

import asyncio
import io
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.config import settings
from app.models.schemas import (
    UserDocument,
    UserProfile,
    UserGoals,
    UserSettings,
    FoodLog,
    ActivityLog,
    WeightLog,
    SleepLog,
    WaterLog,
    DailySummary,
    AIChatMessage,
    utc_now,
    today_str,
)
from app.utils.logger import logger

_firebase_app = None
_rtdb = None
_firestore_db = None
_storage_bucket = None
_in_memory_db: Dict[str, Any] = {}


def _init_firebase():
    global _firebase_app, _rtdb, _firestore_db, _storage_bucket
    if _firebase_app is not None:
        return _rtdb, _firestore_db, _storage_bucket

    try:
        import firebase_admin
        from firebase_admin import credentials, db, firestore, storage

        if not firebase_admin._apps:
            cred_path = settings.FIREBASE_CREDENTIALS_PATH or "serviceAccountKey.json"
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                project_id = cred.project_id
            elif settings.FIREBASE_PROJECT_ID and settings.FIREBASE_CLIENT_EMAIL and settings.FIREBASE_PRIVATE_KEY:
                private_key = settings.FIREBASE_PRIVATE_KEY.replace("\\n", "\n")
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": settings.FIREBASE_PROJECT_ID,
                    "client_email": settings.FIREBASE_CLIENT_EMAIL,
                    "private_key": private_key,
                    "token_uri": "https://oauth2.googleapis.com/token",
                })
                project_id = settings.FIREBASE_PROJECT_ID
            else:
                logger.warning("No Firebase credentials file found yet. Running in Local Memory Adapter mode.")
                return None, None, None

            db_url = settings.FIREBASE_DATABASE_URL or f"https://{project_id}-default-rtdb.firebaseio.com"
            bucket_name = settings.FIREBASE_STORAGE_BUCKET or f"{project_id}.appspot.com"

            _firebase_app = firebase_admin.initialize_app(cred, {
                "databaseURL": db_url,
                "storageBucket": bucket_name,
            })
            logger.info(f"Firebase Admin SDK initialized successfully with Realtime Database ({db_url}) & Storage.")

        try:
            _rtdb = db
        except Exception:
            _rtdb = None

        try:
            _firestore_db = firestore.client()
        except Exception:
            _firestore_db = None

        try:
            if settings.FIREBASE_STORAGE_BUCKET:
                _storage_bucket = storage.bucket(settings.FIREBASE_STORAGE_BUCKET)
            else:
                _storage_bucket = storage.bucket()
        except Exception:
            _storage_bucket = None

        return _rtdb, _firestore_db, _storage_bucket
    except Exception as e:
        logger.warning(f"Failed to initialize Firebase Admin SDK ({e}). Falling back to Local Memory Adapter.")
        return None, None, None


class FirebaseService:
    """Service layer managing all Firebase Realtime Database & Storage operations."""

    def __init__(self):
        self._rtdb, self._db, self._bucket = _init_firebase()

    @property
    def is_connected_to_firebase(self) -> bool:
        return self._rtdb is not None or self._db is not None

    # =========================================================================
    # USER & PROFILE MANAGEMENT
    # =========================================================================

    async def create_user(
        self,
        telegram_user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        profile: Optional[UserProfile] = None,
        goals: Optional[UserGoals] = None,
        user_settings: Optional[UserSettings] = None,
    ) -> UserDocument:
        """Create a new user document in Firebase Realtime Database & Firestore."""
        user_doc = UserDocument(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            profile=profile or UserProfile(),
            goals=goals or UserGoals(),
            settings=user_settings or UserSettings(),
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        def _sync_create():
            doc_dict = user_doc.model_dump()
            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{telegram_user_id}").set(doc_dict)
                except Exception as e:
                    logger.warning(f"Realtime DB set user error: {e}")
            if self._db:
                try:
                    self._db.collection("users").document(str(telegram_user_id)).set(doc_dict)
                except Exception as e:
                    logger.warning(f"Firestore set user error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{telegram_user_id}"] = doc_dict
            return user_doc

        return await asyncio.to_thread(_sync_create)

    async def get_user(self, telegram_user_id: int) -> Optional[UserDocument]:
        """Fetch user profile and goals from Firebase."""
        def _sync_get():
            # 1. Try Realtime Database
            if self._rtdb:
                try:
                    data = self._rtdb.reference(f"users/{telegram_user_id}").get()
                    if data and isinstance(data, dict):
                        return UserDocument.model_validate(data)
                except Exception as e:
                    logger.warning(f"Realtime DB get user error: {e}")

            # 2. Try Firestore
            if self._db:
                try:
                    doc = self._db.collection("users").document(str(telegram_user_id)).get()
                    if doc.exists:
                        return UserDocument.model_validate(doc.to_dict())
                except Exception as e:
                    logger.warning(f"Firestore get user error: {e}")

            # 3. Fallback memory adapter
            raw = _in_memory_db.get(f"users/{telegram_user_id}")
            if raw:
                return UserDocument.model_validate(raw)
            return None

        return await asyncio.to_thread(_sync_get)

    async def update_profile(
        self,
        telegram_user_id: int,
        profile_data: Dict[str, Any],
    ) -> Optional[UserDocument]:
        """Update fields inside user profile."""
        user = await self.get_user(telegram_user_id)
        if not user:
            user = await self.create_user(telegram_user_id)

        current_profile_dict = user.profile.model_dump()
        current_profile_dict.update(profile_data)
        updated_profile = UserProfile.model_validate(current_profile_dict)
        user.profile = updated_profile
        user.updated_at = utc_now()

        def _sync_update():
            p_dict = user.profile.model_dump()
            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{telegram_user_id}/profile").update(p_dict)
                    self._rtdb.reference(f"users/{telegram_user_id}/updated_at").set(user.updated_at)
                except Exception as e:
                    logger.warning(f"RTDB update profile error: {e}")
            if self._db:
                try:
                    self._db.collection("users").document(str(telegram_user_id)).update({
                        "profile": p_dict,
                        "updated_at": user.updated_at,
                    })
                except Exception as e:
                    logger.warning(f"Firestore update profile error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{telegram_user_id}"] = user.model_dump()
            return user

        return await asyncio.to_thread(_sync_update)

    async def update_goals(
        self,
        telegram_user_id: int,
        goals_data: Dict[str, Any],
    ) -> Optional[UserDocument]:
        """Update user goals."""
        user = await self.get_user(telegram_user_id)
        if not user:
            user = await self.create_user(telegram_user_id)

        current_goals_dict = user.goals.model_dump()
        current_goals_dict.update(goals_data)
        updated_goals = UserGoals.model_validate(current_goals_dict)
        user.goals = updated_goals
        user.updated_at = utc_now()

        def _sync_update_goals():
            g_dict = user.goals.model_dump()
            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{telegram_user_id}/goals").update(g_dict)
                    self._rtdb.reference(f"users/{telegram_user_id}/updated_at").set(user.updated_at)
                except Exception as e:
                    logger.warning(f"RTDB update goals error: {e}")
            if self._db:
                try:
                    self._db.collection("users").document(str(telegram_user_id)).update({
                        "goals": g_dict,
                        "updated_at": user.updated_at,
                    })
                except Exception as e:
                    logger.warning(f"Firestore update goals error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{telegram_user_id}"] = user.model_dump()
            return user

        return await asyncio.to_thread(_sync_update_goals)

    # =========================================================================
    # FOOD LOGS
    # =========================================================================

    async def log_food(self, food_log: FoodLog) -> FoodLog:
        """Store food entry in Firebase Realtime Database & Firestore."""
        def _sync_log_food():
            data = food_log.model_dump()
            uid = food_log.telegram_user_id
            fid = food_log.food_log_id

            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{uid}/food_logs/{fid}").set(data)
                except Exception as e:
                    logger.warning(f"RTDB log food error: {e}")
            if self._db:
                try:
                    self._db.document(f"users/{uid}/food_logs/{fid}").set(data)
                except Exception as e:
                    logger.warning(f"Firestore log food error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{uid}/food_logs/{fid}"] = data
            return food_log

        saved = await asyncio.to_thread(_sync_log_food)
        await self._recalculate_daily_summary(food_log.telegram_user_id, food_log.logged_date)
        return saved

    async def get_food_logs(
        self,
        telegram_user_id: int,
        date_str: Optional[str] = None,
        limit: int = 50,
    ) -> List[FoodLog]:
        """Retrieve food logs for a given date or all recent logs."""
        target_date = date_str or today_str()

        def _sync_get_food():
            logs = []
            if self._rtdb:
                try:
                    raw_dict = self._rtdb.reference(f"users/{telegram_user_id}/food_logs").get()
                    if raw_dict and isinstance(raw_dict, dict):
                        for item in raw_dict.values():
                            if isinstance(item, dict) and item.get("logged_date") == target_date:
                                logs.append(FoodLog.model_validate(item))
                        logs.sort(key=lambda x: x.created_at)
                        return logs[:limit]
                except Exception as e:
                    logger.warning(f"RTDB get food logs error: {e}")

            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("food_logs")
                    query = col_ref.where("logged_date", "==", target_date).order_by("created_at").limit(limit)
                    for doc in query.stream():
                        logs.append(FoodLog.model_validate(doc.to_dict()))
                    return logs
                except Exception as e:
                    logger.warning(f"Firestore get food logs error: {e}")

            prefix = f"users/{telegram_user_id}/food_logs/"
            for k, v in _in_memory_db.items():
                if k.startswith(prefix) and isinstance(v, dict) and v.get("logged_date") == target_date:
                    logs.append(FoodLog.model_validate(v))
            logs.sort(key=lambda x: x.created_at)
            return logs[:limit]

        return await asyncio.to_thread(_sync_get_food)

    # =========================================================================
    # ACTIVITIES
    # =========================================================================

    async def log_activity(self, activity_log: ActivityLog) -> ActivityLog:
        """Store activity entry in Firebase."""
        def _sync_log():
            data = activity_log.model_dump()
            uid = activity_log.telegram_user_id
            aid = activity_log.activity_id

            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{uid}/activities/{aid}").set(data)
                except Exception as e:
                    logger.warning(f"RTDB log act error: {e}")
            if self._db:
                try:
                    self._db.document(f"users/{uid}/activities/{aid}").set(data)
                except Exception as e:
                    logger.warning(f"Firestore log act error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{uid}/activities/{aid}"] = data
            return activity_log

        saved = await asyncio.to_thread(_sync_log)
        await self._recalculate_daily_summary(activity_log.telegram_user_id, activity_log.activity_date)
        return saved

    async def get_activity_logs(
        self,
        telegram_user_id: int,
        date_str: Optional[str] = None,
        limit: int = 30,
    ) -> List[ActivityLog]:
        """Fetch activity logs for a specific date."""
        target_date = date_str or today_str()

        def _sync_get_act():
            logs = []
            if self._rtdb:
                try:
                    raw_dict = self._rtdb.reference(f"users/{telegram_user_id}/activities").get()
                    if raw_dict and isinstance(raw_dict, dict):
                        for item in raw_dict.values():
                            if isinstance(item, dict) and item.get("activity_date") == target_date:
                                logs.append(ActivityLog.model_validate(item))
                        logs.sort(key=lambda x: x.created_at)
                        return logs[:limit]
                except Exception as e:
                    logger.warning(f"RTDB get act error: {e}")

            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("activities")
                    query = col_ref.where("activity_date", "==", target_date).limit(limit)
                    for doc in query.stream():
                        logs.append(ActivityLog.model_validate(doc.to_dict()))
                    return logs
                except Exception as e:
                    logger.warning(f"Firestore get act error: {e}")

            prefix = f"users/{telegram_user_id}/activities/"
            for k, v in _in_memory_db.items():
                if k.startswith(prefix) and isinstance(v, dict) and v.get("activity_date") == target_date:
                    logs.append(ActivityLog.model_validate(v))
            logs.sort(key=lambda x: x.created_at)
            return logs[:limit]

        return await asyncio.to_thread(_sync_get_act)

    # =========================================================================
    # WEIGHT TRACKING
    # =========================================================================

    async def log_weight(
        self,
        telegram_user_id: int,
        weight_kg: float,
        date_str: Optional[str] = None,
    ) -> WeightLog:
        """Log a new weight entry."""
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

        def _sync_log_w():
            data = weight_log.model_dump()
            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{telegram_user_id}/weights/{weight_id}").set(data)
                except Exception as e:
                    logger.warning(f"RTDB log weight error: {e}")
            if self._db:
                try:
                    self._db.document(f"users/{telegram_user_id}/weights/{weight_id}").set(data)
                except Exception as e:
                    logger.warning(f"Firestore log weight error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{telegram_user_id}/weights/{weight_id}"] = data
            return weight_log

        saved = await asyncio.to_thread(_sync_log_w)
        await self.update_profile(telegram_user_id, {"current_weight_kg": weight_kg})
        return saved

    async def get_weight_history(
        self,
        telegram_user_id: int,
        limit: int = 30,
    ) -> List[WeightLog]:
        """Fetch historical weight logs."""
        def _sync_get_w():
            logs = []
            if self._rtdb:
                try:
                    raw_dict = self._rtdb.reference(f"users/{telegram_user_id}/weights").get()
                    if raw_dict and isinstance(raw_dict, dict):
                        for item in raw_dict.values():
                            if isinstance(item, dict):
                                logs.append(WeightLog.model_validate(item))
                        logs.sort(key=lambda x: x.created_at, reverse=True)
                        return logs[:limit]
                except Exception as e:
                    logger.warning(f"RTDB get weight error: {e}")

            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("weights")
                    query = col_ref.order_by("created_at", direction="DESCENDING").limit(limit)
                    for doc in query.stream():
                        logs.append(WeightLog.model_validate(doc.to_dict()))
                    return logs
                except Exception as e:
                    logger.warning(f"Firestore get weight error: {e}")

            prefix = f"users/{telegram_user_id}/weights/"
            for k, v in _in_memory_db.items():
                if k.startswith(prefix) and isinstance(v, dict):
                    logs.append(WeightLog.model_validate(v))
            logs.sort(key=lambda x: x.created_at, reverse=True)
            return logs[:limit]

        return await asyncio.to_thread(_sync_get_w)

    # =========================================================================
    # SLEEP TRACKING
    # =========================================================================

    async def log_sleep(self, sleep_log: SleepLog) -> SleepLog:
        """Store sleep log entry."""
        def _sync_log_sleep():
            data = sleep_log.model_dump()
            uid = sleep_log.telegram_user_id
            sid = sleep_log.sleep_id

            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{uid}/sleep_logs/{sid}").set(data)
                except Exception as e:
                    logger.warning(f"RTDB log sleep error: {e}")
            if self._db:
                try:
                    self._db.document(f"users/{uid}/sleep_logs/{sid}").set(data)
                except Exception as e:
                    logger.warning(f"Firestore log sleep error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{uid}/sleep_logs/{sid}"] = data
            return sleep_log

        saved = await asyncio.to_thread(_sync_log_sleep)
        await self._recalculate_daily_summary(sleep_log.telegram_user_id, sleep_log.sleep_date)
        return saved

    async def get_sleep_logs(
        self,
        telegram_user_id: int,
        date_str: Optional[str] = None,
        limit: int = 7,
    ) -> List[SleepLog]:
        """Get sleep logs."""
        target_date = date_str or today_str()

        def _sync_get_sleep():
            logs = []
            if self._rtdb:
                try:
                    raw_dict = self._rtdb.reference(f"users/{telegram_user_id}/sleep_logs").get()
                    if raw_dict and isinstance(raw_dict, dict):
                        for item in raw_dict.values():
                            if isinstance(item, dict) and item.get("sleep_date") == target_date:
                                logs.append(SleepLog.model_validate(item))
                        logs.sort(key=lambda x: x.created_at, reverse=True)
                        return logs[:limit]
                except Exception as e:
                    logger.warning(f"RTDB get sleep error: {e}")

            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("sleep_logs")
                    query = col_ref.where("sleep_date", "==", target_date).limit(limit)
                    for doc in query.stream():
                        logs.append(SleepLog.model_validate(doc.to_dict()))
                    return logs
                except Exception as e:
                    logger.warning(f"Firestore get sleep error: {e}")

            prefix = f"users/{telegram_user_id}/sleep_logs/"
            for k, v in _in_memory_db.items():
                if k.startswith(prefix) and isinstance(v, dict) and v.get("sleep_date") == target_date:
                    logs.append(SleepLog.model_validate(v))
            logs.sort(key=lambda x: x.created_at, reverse=True)
            return logs[:limit]

        return await asyncio.to_thread(_sync_get_sleep)

    # =========================================================================
    # WATER TRACKING
    # =========================================================================

    async def log_water(
        self,
        telegram_user_id: int,
        amount_ml: int,
        date_str: Optional[str] = None,
    ) -> WaterLog:
        """Log incremental water consumption."""
        water_id = f"water_{date_str or today_str()}_{uuid.uuid4().hex[:6]}"
        water_log = WaterLog(
            water_log_id=water_id,
            telegram_user_id=telegram_user_id,
            amount_ml=amount_ml,
            logged_date=date_str or today_str(),
            created_at=utc_now(),
        )

        def _sync_log_water():
            data = water_log.model_dump()
            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{telegram_user_id}/water_logs/{water_id}").set(data)
                except Exception as e:
                    logger.warning(f"RTDB log water error: {e}")
            if self._db:
                try:
                    self._db.document(f"users/{telegram_user_id}/water_logs/{water_id}").set(data)
                except Exception as e:
                    logger.warning(f"Firestore log water error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{telegram_user_id}/water_logs/{water_id}"] = data
            return water_log

        saved = await asyncio.to_thread(_sync_log_water)
        await self._recalculate_daily_summary(telegram_user_id, water_log.logged_date)
        return saved

    async def get_water_logs(
        self,
        telegram_user_id: int,
        date_str: Optional[str] = None,
    ) -> List[WaterLog]:
        """Fetch all water logs logged on a particular date."""
        target_date = date_str or today_str()

        def _sync_get_water():
            logs = []
            if self._rtdb:
                try:
                    raw_dict = self._rtdb.reference(f"users/{telegram_user_id}/water_logs").get()
                    if raw_dict and isinstance(raw_dict, dict):
                        for item in raw_dict.values():
                            if isinstance(item, dict) and item.get("logged_date") == target_date:
                                logs.append(WaterLog.model_validate(item))
                        return logs
                except Exception as e:
                    logger.warning(f"RTDB get water error: {e}")

            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("water_logs")
                    query = col_ref.where("logged_date", "==", target_date)
                    for doc in query.stream():
                        logs.append(WaterLog.model_validate(doc.to_dict()))
                    return logs
                except Exception as e:
                    logger.warning(f"Firestore get water error: {e}")

            prefix = f"users/{telegram_user_id}/water_logs/"
            for k, v in _in_memory_db.items():
                if k.startswith(prefix) and isinstance(v, dict) and v.get("logged_date") == target_date:
                    logs.append(WaterLog.model_validate(v))
            return logs

        return await asyncio.to_thread(_sync_get_water)

    # =========================================================================
    # DAILY SUMMARIES & SCORE
    # =========================================================================

    async def create_daily_summary(self, summary: DailySummary) -> DailySummary:
        """Save aggregated daily summary."""
        def _sync_create_sum():
            data = summary.model_dump()
            uid = summary.telegram_user_id
            dt = summary.summary_date

            if self._rtdb:
                try:
                    self._rtdb.reference(f"users/{uid}/daily_summaries/{dt}").set(data)
                except Exception as e:
                    logger.warning(f"RTDB set daily sum error: {e}")
            if self._db:
                try:
                    self._db.document(f"users/{uid}/daily_summaries/{dt}").set(data)
                except Exception as e:
                    logger.warning(f"Firestore set daily sum error: {e}")
            if not self._rtdb and not self._db:
                _in_memory_db[f"users/{uid}/daily_summaries/{dt}"] = data
            return summary

        return await asyncio.to_thread(_sync_create_sum)

    async def get_daily_summary(
        self,
        telegram_user_id: int,
        date_str: Optional[str] = None,
    ) -> DailySummary:
        """Fetch or automatically recalculate daily summary."""
        target_date = date_str or today_str()

        def _sync_get_sum():
            if self._rtdb:
                try:
                    raw = self._rtdb.reference(f"users/{telegram_user_id}/daily_summaries/{target_date}").get()
                    if raw and isinstance(raw, dict):
                        return DailySummary.model_validate(raw)
                except Exception as e:
                    logger.warning(f"RTDB get daily sum error: {e}")

            if self._db:
                try:
                    doc = self._db.document(f"users/{telegram_user_id}/daily_summaries/{target_date}").get()
                    if doc.exists:
                        return DailySummary.model_validate(doc.to_dict())
                except Exception as e:
                    logger.warning(f"Firestore get daily sum error: {e}")

            raw = _in_memory_db.get(f"users/{telegram_user_id}/daily_summaries/{target_date}")
            if raw:
                return DailySummary.model_validate(raw)
            return None

        summary = await asyncio.to_thread(_sync_get_sum)
        if summary is None:
            summary = await self._recalculate_daily_summary(telegram_user_id, target_date)
        return summary

    async def _recalculate_daily_summary(
        self,
        telegram_user_id: int,
        target_date: str,
    ) -> DailySummary:
        """Recalculate nutrition, activity, sleep, and water totals for a date."""
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
        added_sugar = round(sum(f.added_sugar_g for f in foods), 1)
        total_fiber = round(sum(f.fiber_g for f in foods), 1)

        # Aggregate Activity
        burned_cals = sum(a.estimated_calories for a in activities)
        active_mins = sum(a.duration_minutes or 0.0 for a in activities)

        # Aggregate Sleep
        latest_sleep = sleeps[0] if sleeps else None
        sleep_dur = latest_sleep.duration_hours if latest_sleep else 0.0

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

        if sleep_dur >= 7.0 and sleep_dur <= 9.0:
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
            sleep_hours=sleep_dur,
            sleep_bedtime=latest_sleep.bedtime if latest_sleep else None,
            sleep_wake_time=latest_sleep.wake_time if latest_sleep else None,
            total_water_ml=total_water,
            target_water_ml=user.goals.water_target_ml,
            daily_score=round(min(score_val, 10.0), 1),
            daily_score_breakdown=score_breakdown,
            ai_feedback="Pola makan dan aktivitas hari ini terpantau baik.",
            updated_at=utc_now(),
        )

        return await self.create_daily_summary(summary)

    # =========================================================================
    # FIREBASE STORAGE & FOOD IMAGES
    # =========================================================================

    async def upload_food_image(
        self,
        telegram_user_id: int,
        image_bytes: bytes,
        file_extension: str = "jpg",
    ) -> Dict[str, str]:
        """Upload food image to Firebase Storage: food-images/{user_id}/YYYY/MM/{image_id}.jpg."""
        now = datetime.now(timezone.utc)
        year_str = now.strftime("%Y")
        month_str = now.strftime("%m")
        image_id = f"img_{uuid.uuid4().hex}"
        storage_path = f"food-images/{telegram_user_id}/{year_str}/{month_str}/{image_id}.{file_extension}"

        def _sync_upload():
            if self._bucket:
                try:
                    blob = self._bucket.blob(storage_path)
                    blob.upload_from_string(image_bytes, content_type=f"image/{file_extension}")
                    try:
                        blob.make_public()
                        public_url = blob.public_url
                    except Exception:
                        public_url = f"https://storage.googleapis.com/{self._bucket.name}/{storage_path}"
                    return {
                        "storage_path": storage_path,
                        "image_url": public_url,
                        "image_id": image_id,
                    }
                except Exception as e:
                    logger.warning(f"Storage upload error ({e}). Using mock path.")

            mock_url = f"https://mock-storage.firebase.local/{storage_path}"
            _in_memory_db[f"storage:{storage_path}"] = image_bytes
            return {
                "storage_path": storage_path,
                "image_url": mock_url,
                "image_id": image_id,
            }

        return await asyncio.to_thread(_sync_upload)

    async def save_food_analysis(
        self,
        telegram_user_id: int,
        analysis_data: Dict[str, Any],
    ) -> FoodLog:
        """Persist analyzed food record."""
        food_log_id = f"food_{today_str()}_{uuid.uuid4().hex[:6]}"
        food_log = FoodLog(
            food_log_id=food_log_id,
            telegram_user_id=telegram_user_id,
            food_name=analysis_data.get("food_name", "Makanan Campur"),
            meal_type=analysis_data.get("meal_type", "lunch"),
            portion=analysis_data.get("portion", "1 porsi"),
            calories=analysis_data.get("calories", 0),
            protein_g=analysis_data.get("protein_g", 0.0),
            carbs_g=analysis_data.get("carbs_g", 0.0),
            fat_g=analysis_data.get("fat_g", 0.0),
            total_sugar_g=analysis_data.get("total_sugar_g", 0.0),
            added_sugar_g=analysis_data.get("added_sugar_g", 0.0),
            fiber_g=analysis_data.get("fiber_g", 0.0),
            sodium_mg=analysis_data.get("sodium_mg", 0.0),
            confidence=analysis_data.get("confidence", "medium"),
            source=analysis_data.get("source", "photo_ai"),
            image_reference=analysis_data.get("storage_path"),
            image_url=analysis_data.get("image_url"),
            notes=analysis_data.get("notes"),
            items=analysis_data.get("items", []),
            logged_date=today_str(),
            created_at=utc_now(),
        )
        return await self.log_food(food_log)


firebase_service = FirebaseService()
