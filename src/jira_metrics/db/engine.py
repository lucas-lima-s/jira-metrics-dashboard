from __future__ import annotations

import logging
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from ..config import DatabaseSettings

logger = logging.getLogger(__name__)


class SyncDatabase:
    def __init__(self):
        self._engine = None
        self.session_factory = None

    def init(self, settings: DatabaseSettings) -> None:
        logger.debug("Initializing database engine")
        kwargs = {"echo": settings.echo, "pool_pre_ping": settings.pool_pre_ping}
        if make_url(settings.sqlalchemy_url).get_backend_name() != "sqlite":
            kwargs["pool_size"] = settings.pool_size
            kwargs["max_overflow"] = settings.max_overflow
        self._engine = create_engine(settings.sqlalchemy_url, **kwargs)
        self.session_factory = sessionmaker(
            bind=self._engine, class_=Session, expire_on_commit=False
        )

    @contextmanager
    def get_session_with_transaction(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = self.session_factory()
        try:
            yield session
        finally:
            session.close()

    @property
    def engine(self):
        if not self._engine:
            raise RuntimeError("Sync engine not initialized. Call init() first.")
        return self._engine


sync_db = SyncDatabase()
