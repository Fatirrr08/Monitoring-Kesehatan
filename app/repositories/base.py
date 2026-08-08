import asyncio
import os
from typing import Any

from app.config import settings
from app.utils.logger import logger

_firebase_app = None
_firestore_db = None
_storage_bucket = None
_in_memory_store: dict[str, Any] = {}


def get_firestore_client():
    """Initialize or return Cloud Firestore client."""
    global _firebase_app, _firestore_db, _storage_bucket
    if _firestore_db is not None:
        return _firestore_db

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore, storage

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
                logger.warning("No explicit Firebase credentials found. Running in Local Memory Adapter mode.")
                return None

            bucket_name = settings.FIREBASE_STORAGE_BUCKET or f"{project_id}.appspot.com"
            _firebase_app = firebase_admin.initialize_app(cred, {
                "storageBucket": bucket_name,
            })
            logger.info(f"Cloud Firestore initialized successfully for project: {project_id}")

        _firestore_db = firestore.client()
        try:
            _storage_bucket = storage.bucket()
        except Exception:
            _storage_bucket = None

        return _firestore_db
    except Exception as e:
        logger.warning(f"Failed to initialize Firestore client ({e}). Using Local Memory Adapter.")
        return None


def get_storage_bucket():
    """Return initialized Firebase Storage bucket."""
    global _storage_bucket
    if _storage_bucket is None:
        get_firestore_client()
    return _storage_bucket


class BaseRepository:
    """Base repository with threadpool async execution and dual Firestore/Local adapter."""

    def __init__(self):
        self._db = get_firestore_client()

    @property
    def is_live(self) -> bool:
        return self._db is not None

    async def run_sync(self, func, *args, **kwargs):
        """Execute blocking Firestore calls safely in background threadpool."""
        return await asyncio.to_thread(func, *args, **kwargs)
