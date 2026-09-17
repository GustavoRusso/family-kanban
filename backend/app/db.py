"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_database_url


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


def create_db_engine(url: str | None = None) -> Engine:
    database_url = url or get_database_url()
    return create_engine(database_url, future=True, pool_pre_ping=True)


def _make_session_factory(bind: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=bind, autoflush=False, autocommit=False, future=True)


def run_migrations(bind: Engine) -> None:
    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    alembic_dir = Path(__file__).resolve().parents[1] / "alembic"
    config = Config(str(alembic_ini))
    config.set_main_option("script_location", str(alembic_dir))
    config.set_main_option("sqlalchemy.url", str(bind.url))
    command.upgrade(config, "head")


def init_db(bind: Engine | None = None) -> None:
    target_engine = bind or engine
    run_migrations(target_engine)


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
