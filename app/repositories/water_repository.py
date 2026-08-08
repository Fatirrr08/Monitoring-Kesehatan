
from app.models.schemas import WaterLog, today_str
from app.repositories.base import BaseRepository, _in_memory_store


class WaterRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}/water_logs/{water_id}."""

    async def save_water(self, water_log: WaterLog) -> WaterLog:
        def _sync_save():
            path = f"users/{water_log.telegram_user_id}/water_logs/{water_log.water_log_id}"
            data = water_log.model_dump()
            if self._db:
                self._db.document(path).set(data)
            else:
                _in_memory_store[path] = data
            return water_log

        return await self.run_sync(_sync_save)

    async def get_water_logs_by_date(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
    ) -> list[WaterLog]:
        target_date = date_str or today_str()

        def _sync_get():
            logs = []
            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("water_logs")
                    query = col_ref.where("logged_date", "==", target_date)
                    for doc in query.stream():
                        logs.append(WaterLog.model_validate(doc.to_dict()))
                except Exception:
                    logs = []

            if not logs:
                prefix = f"users/{telegram_user_id}/water_logs/"
                for k, v in _in_memory_store.items():
                    if k.startswith(prefix) and isinstance(v, dict) and v.get("logged_date") == target_date:
                        logs.append(WaterLog.model_validate(v))

            logs.sort(key=lambda x: x.created_at)
            return logs

        return await self.run_sync(_sync_get)


water_repository = WaterRepository()
