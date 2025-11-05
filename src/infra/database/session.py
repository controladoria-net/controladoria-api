from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.infra.database.config import get_database_url

_engine = create_engine(get_database_url(), pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    bind=_engine, autocommit=False, autoflush=False, future=True
)


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Provide a transactional scope for database operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a session."""
    with session_scope() as session:
        yield session
