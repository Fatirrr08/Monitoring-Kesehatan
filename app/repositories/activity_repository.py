
from app.models.schemas import ActivityLog, today_str
from app.repositories.base import BaseRepository, _in_memory_store


class ActivityRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}/activities/{activity_id}."""

    async def save_activity(self, activity: ActivityLog) -> ActivityLog:
        def _sync_save():
            path = f"users/{activity.telegram_user_id}/activities/{activity.activity_id}"
            data = activity.model_dump()
            if self._db:
                self._db.document(path).set(data)
            else:
                _in_memory_store[path] = data
            return activity

        return await self.run_sync(_sync_save)

    async def get_activities_by_date(
        self,
        telegram_user_id: int,
        date_str: str | None = None,
        limit: int = 30,
    ) -> list[ActivityLog]:
        target_date = date_str or today_str()

        def _sync_get():
            logs = []
            if self._db:
                try:
                    col_ref = self._db.collection("users").document(str(telegram_user_id)).collection("activities")
                    query = col_ref.where("activity_date", "==", target_date)
                    for doc in query.stream():
                        logs.append(ActivityLog.model_validate(doc.to_dict()))
                except Exception:
                    logs = []

            if not logs:
                prefix = f"users/{telegram_user_id}/activities/"
                for k, v in _in_memory_store.items():
                    if k.startswith(prefix) and isinstance(v, dict) and v.get("activity_date") == target_date:
                        logs.append(ActivityLog.model_validate(v))

            logs.sort(key=lambda x: x.created_at)
            return logs[:limit]

        return await self.run_sync(_sync_get)


activity_repository = ActivityRepository()
