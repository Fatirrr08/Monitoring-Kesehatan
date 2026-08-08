from app.models.schemas import WeightLog
from app.repositories.base import BaseRepository, _in_memory_store


class WeightRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}/weights/{weight_id}."""

    async def save_weight(self, weight_log: WeightLog) -> WeightLog:
        def _sync_save():
            path = f"users/{weight_log.telegram_user_id}/weights/{weight_log.weight_id}"
            data = weight_log.model_dump()
            if self._db:
                self._db.document(path).set(data)
            else:
                _in_memory_store[path] = data
            return weight_log

        return await self.run_sync(_sync_save)

    async def get_weight_history(self, telegram_user_id: int, limit: int = 30) -> list[WeightLog]:
        def _sync_get():
            logs = []
            if self._db:
                col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("weights")
                query = col_ref.order_by("created_at", direction="DESCENDING").limit(limit)
                for doc in query.stream():
                    logs.append(WeightLog.model_validate(doc.to_dict()))
            else:
                prefix = f"users/{telegram_user_id}/weights/"
                for k, v in _in_memory_store.items():
                    if k.startswith(prefix) and isinstance(v, dict):
                        logs.append(WeightLog.model_validate(v))
                logs.sort(key=lambda x: x.created_at, reverse=True)
            return logs[:limit]

        return await self.run_sync(_sync_get)


weight_repository = WeightRepository()
