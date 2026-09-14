"""SQLAlchemy engine and session factory — dialect comes from DATABASE_URL."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_database_url


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


def _engine_kwargs(url: str) -> dict:
    """Dialect-specific engine options without hard-coding a single database."""
    kwargs: dict = {"future": True}
    if url.startswith("sqlite"):
        # FastAPI can share connections across threads in the same process.
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


def create_db_engine(url: str | None = None) -> Engine:
    database_url = url or get_database_url()
    engine = create_engine(database_url, **_engine_kwargs(database_url))
    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_fk(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def _make_session_factory(bind: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=bind, autoflush=False, autocommit=False, future=True)


engine = create_db_engine()
SessionLocal = _make_session_factory(engine)


def _ensure_login_code_expires_at(bind: Engine) -> None:
    """Add login_codes.expires_at when missing; clear codes issued without TTL."""
    insp = inspect(bind)
    if "login_codes" not in insp.get_table_names():
        return
    columns = {col["name"] for col in insp.get_columns("login_codes")}
    if "expires_at" in columns:
        return

    dialect = bind.dialect.name
    if dialect == "sqlite":
        ddl = "ALTER TABLE login_codes ADD COLUMN expires_at DATETIME"
    else:
        ddl = "ALTER TABLE login_codes ADD COLUMN expires_at TIMESTAMP WITH TIME ZONE"

    with bind.begin() as conn:
        conn.execute(text(ddl))
        conn.execute(text("DELETE FROM login_codes"))


def init_db(bind: Engine | None = None) -> None:
    """Create tables if they do not exist (fine until migrations are added)."""
    # Import models so metadata is registered.
    import app.orm  # noqa: F401

    target = bind or engine
    Base.metadata.create_all(bind=target)
    _ensure_login_code_expires_at(target)


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
