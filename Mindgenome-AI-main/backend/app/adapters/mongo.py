from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.logging import logger


class MongoActivityStore:
    def __init__(self) -> None:
        self._client = None
        self._database = None

    def is_configured(self) -> bool:
        return bool(settings.MONGODB_URI)

    async def connect(self) -> bool:
        if not self.is_configured():
            return False
        if self._client is not None:
            return True
        try:
            from motor.motor_asyncio import AsyncIOMotorClient

            self._client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
            )
            await self._client.admin.command("ping")
            self._database = self._client[settings.MONGODB_DATABASE]
            await self._ensure_indexes()
            logger.info("mongodb_atlas_connected", database=settings.MONGODB_DATABASE)
            return True
        except Exception as exc:
            logger.warning("mongodb_atlas_unavailable", error=str(exc))
            self._client = None
            self._database = None
            return False

    async def _ensure_indexes(self) -> None:
        if self._database is None:
            return
        await self._database.learning_history.create_index([("user_id", 1), ("created_at", -1)])
        await self._database.learning_history.create_index([("user_id", 1), ("concept_id", 1), ("created_at", -1)])
        await self._database.learner_progress.create_index([("user_id", 1), ("concept_id", 1)], unique=True)
        await self._database.quiz_attempts.create_index([("user_id", 1), ("concept_id", 1), ("completed_at", -1)])
        await self._database.tutor_sessions.create_index([("user_id", 1), ("created_at", -1)])

    async def insert_history(self, document: dict[str, Any]) -> bool:
        if not await self.connect():
            return False
        try:
            now = datetime.now(timezone.utc)
            document.setdefault("created_at", now)
            document.setdefault("updated_at", now)
            await self._database.learning_history.insert_one(document)
            return True
        except Exception as exc:
            logger.warning("mongodb_history_insert_failed", error=str(exc))
            return False

    async def upsert_progress(self, user_id: str, concept_id: str, update: dict[str, Any]) -> bool:
        if not await self.connect():
            return False
        try:
            now = datetime.now(timezone.utc)
            await self._database.learner_progress.update_one(
                {"user_id": user_id, "concept_id": concept_id},
                {
                    "$set": {**update, "updated_at": now},
                    "$setOnInsert": {"created_at": now, "evidence_count": 0},
                    "$inc": {"evidence_count": 1},
                },
                upsert=True,
            )
            return True
        except Exception as exc:
            logger.warning("mongodb_progress_upsert_failed", error=str(exc))
            return False

    async def insert_quiz_attempt(self, document: dict[str, Any]) -> bool:
        if not await self.connect():
            return False
        try:
            await self._database.quiz_attempts.insert_one(document)
            return True
        except Exception as exc:
            logger.warning("mongodb_quiz_insert_failed", error=str(exc))
            return False

    async def insert_tutor_session(self, document: dict[str, Any]) -> bool:
        if not await self.connect():
            return False
        try:
            document.setdefault("created_at", datetime.now(timezone.utc))
            await self._database.tutor_sessions.insert_one(document)
            return True
        except Exception as exc:
            logger.warning("mongodb_tutor_insert_failed", error=str(exc))
            return False

    async def ping(self) -> bool:
        return await self.connect()

    async def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None


mongo_activity_store = MongoActivityStore()
