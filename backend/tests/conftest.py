from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_session, init_db
from app.email.deps import get_email_sender
from app.email.sender import RecordingEmailSender
from app.main import create_app


@pytest.fixture
def engine():
    db_path = Path("/tmp/family-kanban-test.db")
    if db_path.exists():
        db_path.unlink()
    eng = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    init_db(bind=eng)
    return eng


@pytest.fixture
def email_sender() -> RecordingEmailSender:
    return RecordingEmailSender()


@pytest.fixture
def client(engine, email_sender: RecordingEmailSender):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_session():
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    application = create_app()
    application.state.email_sender = email_sender
    application.dependency_overrides[get_session] = override_get_session
    application.dependency_overrides[get_email_sender] = lambda: email_sender
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
