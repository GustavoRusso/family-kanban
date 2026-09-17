"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_database_url


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


def create_db_engine(url: str | None = None) -> Engine:
    database_url = url or get_database_url()
    return create_engine(database_url, future=True)


def _make_session_factory(bind: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=bind, autoflush=False, autocommit=False, future=True)


engine = create_db_engine()
SessionLocal = _make_session_factory(engine)


def get_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
