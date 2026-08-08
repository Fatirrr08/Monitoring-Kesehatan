from typing import Any

from app.models.schemas import (
    UserDocument,
    UserGoals,
    UserProfile,
    UserSettings,
    utc_now,
)
from app.repositories.base import BaseRepository, _in_memory_store


class UserRepository(BaseRepository):
    """Handles persistence for users/{telegram_user_id}."""

    async def create_user(
        self,
        telegram_user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        profile: UserProfile | None = None,
        goals: UserGoals | None = None,
        settings: UserSettings | None = None,
    ) -> UserDocument:
        user_doc = UserDocument(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            profile=profile or UserProfile(),
            goals=goals or UserGoals(),
            settings=settings or UserSettings(),
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        def _sync_create():
            doc_dict = user_doc.model_dump()
            if self._db:
                self._db.collection("users").document(str(telegram_user_id)).set(doc_dict)
            else:
                _in_memory_store[f"users/{telegram_user_id}"] = doc_dict
            return user_doc

        return await self.run_sync(_sync_create)

    async def get_user(self, telegram_user_id: int) -> UserDocument | None:
        def _sync_get():
            if self._db:
                doc = self._db.collection("users").document(str(telegram_user_id)).get()
                if doc.exists:
                    return UserDocument.model_validate(doc.to_dict())
                return None
            else:
                raw = _in_memory_store.get(f"users/{telegram_user_id}")
                if raw:
                    return UserDocument.model_validate(raw)
                return None

        return await self.run_sync(_sync_get)

    async def update_profile(self, telegram_user_id: int, profile_data: dict[str, Any]) -> UserDocument:
        user = await self.get_user(telegram_user_id)
        if not user:
            user = await self.create_user(telegram_user_id)

        p_dict = user.profile.model_dump()
        p_dict.update(profile_data)
        user.profile = UserProfile.model_validate(p_dict)
        user.updated_at = utc_now()

        def _sync_update():
            if self._db:
                self._db.collection("users").document(str(telegram_user_id)).update({
                    "profile": user.profile.model_dump(),
                    "updated_at": user.updated_at,
                })
            else:
                _in_memory_store[f"users/{telegram_user_id}"] = user.model_dump()
            return user

        return await self.run_sync(_sync_update)

    async def update_goals(self, telegram_user_id: int, goals_data: dict[str, Any]) -> UserDocument:
        user = await self.get_user(telegram_user_id)
        if not user:
            user = await self.create_user(telegram_user_id)

        g_dict = user.goals.model_dump()
        g_dict.update(goals_data)
        user.goals = UserGoals.model_validate(g_dict)
        user.updated_at = utc_now()

        def _sync_update():
            if self._db:
                self._db.collection("users").document(str(telegram_user_id)).update({
                    "goals": user.goals.model_dump(),
                    "updated_at": user.updated_at,
                })
            else:
                _in_memory_store[f"users/{telegram_user_id}"] = user.model_dump()
            return user

        return await self.run_sync(_sync_update)


user_repository = UserRepository()
