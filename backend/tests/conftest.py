from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_session, init_db
from app.main import create_app


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    init_db(bind=eng)
    return eng


@pytest.fixture
def client(engine):
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
    application.dependency_overrides[get_session] = override_get_session
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
