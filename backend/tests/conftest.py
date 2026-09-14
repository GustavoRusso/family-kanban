from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.auth.deps import get_store
from app.main import create_app
from app.store.memory import InMemoryStore


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def client(store: InMemoryStore):
    application = create_app()
    application.dependency_overrides[get_store] = lambda: store
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
