
from app.models.schemas import DailySummary, today_str
from app.repositories.base import BaseRepository, _in_memory_store


class SummaryRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}/daily_summaries/{YYYY-MM-DD}."""

    async def save_daily_summary(self, summary: DailySummary) -> DailySummary:
        def _sync_save():
            path = f"users/{summary.telegram_user_id}/daily_summaries/{summary.summary_date}"
            data = summary.model_dump()
            if self._db:
                self._db.document(path).set(data)
            else:
                _in_memory_store[path] = data
            return summary

        return await self.run_sync(_sync_save)

    async def get_daily_summary(self, telegram_user_id: int, date_str: str | None = None) -> DailySummary | None:
        target_date = date_str or today_str()

        def _sync_get():
            path = f"users/{telegram_user_id}/daily_summaries/{target_date}"
            if self._db:
                doc = self._db.document(path).get()
                if doc.exists:
                    return DailySummary.model_validate(doc.to_dict())
            else:
                raw = _in_memory_store.get(path)
                if raw:
                    return DailySummary.model_validate(raw)
            return None

        return await self.run_sync(_sync_get)


summary_repository = SummaryRepository()
