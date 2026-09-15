from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.db import get_session
from app.email.deps import get_email_sender
from app.email.sender import ResendEmailSender
from app.main import create_app
from app.store.sqlalchemy_store import SqlAlchemyStore
from tests.helpers import auth_header, request_code, sign_in


def test_request_code_does_not_echo_code(client: TestClient) -> None:
    code = request_code(client, "maya@example.com")
    assert isinstance(code, str)
    assert len(code) == 6


def test_request_code_rejects_invalid_email(client: TestClient) -> None:
    response = client.post("/api/v1/auth/code", json={"email": "not-an-email"})
    assert response.status_code == 400
    assert "message" in response.json()


def test_request_code_fails_when_email_not_configured(engine, monkeypatch) -> None:
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("EMAIL_FROM", raising=False)
    monkeypatch.setenv("EMAIL_DELIVERY", "resend")

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
    application.dependency_overrides[get_email_sender] = lambda: ResendEmailSender()

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/auth/code",
            json={"email": "maya@example.com"},
        )
        assert response.status_code == 400
        assert "Email is not configured" in response.json()["message"]

        # Failed send must not leave a recoverable code in the DB.
        with Session() as session:
            store = SqlAlchemyStore(session)
            assert store.get_code("maya@example.com") is None

    application.dependency_overrides.clear()


def test_console_delivery_stores_code_and_verify_works(engine, monkeypatch, caplog) -> None:
    monkeypatch.setenv("EMAIL_DELIVERY", "console")

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
    # Use real get_email_sender so EMAIL_DELIVERY=console is honored.
    with TestClient(application) as client:
        with caplog.at_level("WARNING", logger="app.email.sender"):
            response = client.post(
                "/api/v1/auth/code",
                json={"email": "maya@example.com"},
            )
        assert response.status_code == 200
        assert response.json() == {}
        assert "devCode" not in response.json()

        with Session() as session:
            store = SqlAlchemyStore(session)
            stored = store.get_code("maya@example.com")
            assert stored is not None
            code, _expires = stored

        assert code in caplog.text
        assert "maya@example.com" in caplog.text

        verify = client.post(
            "/api/v1/auth/verify",
            json={"email": "maya@example.com", "code": code},
        )
        assert verify.status_code == 200
        assert verify.json()["user"]["email"] == "maya@example.com"

    application.dependency_overrides.clear()


def test_verify_auto_creates_account_and_normalizes_email(client: TestClient) -> None:
    body = sign_in(client, "Maya@Example.com ")
    assert body["user"]["email"] == "maya@example.com"
    assert body["activeFamilyId"] is None
    assert body["user"]["id"]
    assert body["user"]["name"]
    assert body["accessToken"]


def test_verify_rejects_wrong_code(client: TestClient) -> None:
    request_code(client, "leo@example.com")
    response = client.post(
        "/api/v1/auth/verify",
        json={"email": "leo@example.com", "code": "000000"},
    )
    assert response.status_code == 400
    assert "doesn't match" in response.json()["message"]


def test_verify_rejects_expired_code(client: TestClient, engine) -> None:
    code = request_code(client, "maya@example.com")
    issued_at = datetime.now(timezone.utc)

    with patch("app.auth.service._utcnow", return_value=issued_at + timedelta(minutes=6)):
        response = client.post(
            "/api/v1/auth/verify",
            json={"email": "maya@example.com", "code": code},
        )
    assert response.status_code == 400
    assert "expired" in response.json()["message"].lower()

    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with Session() as session:
        store = SqlAlchemyStore(session)
        assert store.get_code("maya@example.com") is None


def test_same_email_returns_same_user_id(client: TestClient) -> None:
    first = sign_in(client, "maya@example.com")
    sign_out = client.post(
        "/api/v1/auth/sign-out",
        headers=auth_header(first["accessToken"]),
    )
    assert sign_out.status_code == 204

    second = sign_in(client, "maya@example.com")
    assert second["user"]["id"] == first["user"]["id"]
    assert second["accessToken"] != first["accessToken"]


def test_session_without_token_returns_null(client: TestClient) -> None:
    response = client.get("/api/v1/auth/session")
    assert response.status_code == 200
    assert response.json() is None


def test_session_with_valid_token_returns_session(client: TestClient) -> None:
    auth = sign_in(client, "maya@example.com")
    response = client.get(
        "/api/v1/auth/session",
        headers=auth_header(auth["accessToken"]),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["id"] == auth["user"]["id"]
    assert body["user"]["email"] == "maya@example.com"
    assert body["activeFamilyId"] is None
    assert "accessToken" not in body


def test_session_with_invalid_token_returns_null(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/session",
        headers=auth_header("not-a-real-token"),
    )
    assert response.status_code == 200
    assert response.json() is None


def test_sign_out_requires_auth(client: TestClient) -> None:
    response = client.post("/api/v1/auth/sign-out")
    assert response.status_code == 401
    assert "message" in response.json()


def test_sign_out_clears_session(client: TestClient) -> None:
    auth = sign_in(client, "maya@example.com")
    headers = auth_header(auth["accessToken"])

    response = client.post("/api/v1/auth/sign-out", headers=headers)
    assert response.status_code == 204

    session = client.get("/api/v1/auth/session", headers=headers)
    assert session.status_code == 200
    assert session.json() is None
