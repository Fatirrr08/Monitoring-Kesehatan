
from app.models.schemas import SleepLog, today_str
from app.repositories.base import BaseRepository, _in_memory_store


class SleepRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}/sleep_logs/{sleep_id}."""

    async def save_sleep(self, sleep_log: SleepLog) -> SleepLog:
        def _sync_save():
            path = f"users/{sleep_log.telegram_user_id}/sleep_logs/{sleep_log.sleep_id}"
            data = sleep_log.model_dump()
            if self._db:
                self._db.document(path).set(data)
            else:
                _in_memory_store[path] = data
            return sleep_log

        return await self.run_sync(_sync_save)

    async def get_sleep_logs_by_date(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
        limit: int = 7,
    ) -> list[SleepLog]:
        target_date = date_str or today_str()

        def _sync_get():
            logs = []
            if self._db:
                col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("sleep_logs")
                query = col_ref.where("sleep_date", "==", target_date).limit(limit)
                for doc in query.stream():
                    logs.append(SleepLog.model_validate(doc.to_dict()))
            else:
                prefix = f"users/{telegram_user_id}/sleep_logs/"
                for k, v in _in_memory_store.items():
                    if k.startswith(prefix) and isinstance(v, dict) and v.get("sleep_date") == target_date:
                        logs.append(SleepLog.model_validate(v))
                logs.sort(key=lambda x: x.created_at, reverse=True)
            return logs

        return await self.run_sync(_sync_get)


sleep_repository = SleepRepository()
