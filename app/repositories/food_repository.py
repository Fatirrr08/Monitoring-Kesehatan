
from app.models.schemas import FoodLog, today_str
from app.repositories.base import BaseRepository, _in_memory_store


class FoodRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}/food_logs/{food_log_id}."""

    async def save_food_log(self, food_log: FoodLog) -> FoodLog:
        def _sync_save():
            path = f"users/{food_log.telegram_user_id}/food_logs/{food_log.food_log_id}"
            data = food_log.model_dump()
            if self._db:
                self._db.document(path).set(data)
            else:
                _in_memory_store[path] = data
            return food_log

        return await self.run_sync(_sync_save)

    async def get_food_logs_by_date(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
        limit: int = 50,
    ) -> list[FoodLog]:
        target_date = date_str or today_str()

        def _sync_get():
            logs = []
            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("food_logs")
                    query = col_ref.where("logged_date", "==", target_date)
                    for doc in query.stream():
                        logs.append(FoodLog.model_validate(doc.to_dict()))
                except Exception:
                    logs = []

            if not logs:
                prefix = f"users/{telegram_user_id}/food_logs/"
                for k, v in _in_memory_store.items():
                    if k.startswith(prefix) and isinstance(v, dict) and v.get("logged_date") == target_date:
                        logs.append(FoodLog.model_validate(v))

            logs.sort(key=lambda x: x.created_at)
            return logs[:limit]

        return await self.run_sync(_sync_get)


food_repository = FoodRepository()
