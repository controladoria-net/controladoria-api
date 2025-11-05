from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.infra.database.models import SchedulerLockModel


class SchedulerLockRepository:
    """Repository handling distributed scheduler locks backed by the database."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def acquire(self, lock_name: str, ttl_seconds: int) -> bool:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl_seconds)
        lock = SchedulerLockModel(
            lock_name=lock_name, acquired_at=now, expires_at=expires_at
        )
        self._session.add(lock)
        try:
            self._session.flush()
            return True
        except IntegrityError:
            self._session.rollback()
            existing = self._session.execute(
                select(SchedulerLockModel).where(
                    SchedulerLockModel.lock_name == lock_name
                )
            ).scalar_one_or_none()
            if existing and existing.expires_at < now:
                existing.acquired_at = now
                existing.expires_at = expires_at
                self._session.add(existing)
                self._session.flush()
                return True
            return False

    def release(self, lock_name: str) -> None:
        self._session.execute(
            delete(SchedulerLockModel).where(SchedulerLockModel.lock_name == lock_name)
        )
        self._session.flush()
