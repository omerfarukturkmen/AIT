"""Tests for e-mail/password auth endpoints (in-memory SQLite)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import auth  # noqa: E402
import models  # noqa: E402
from database import Base  # noqa: E402


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth.router)
    app.dependency_overrides[auth.get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.session_factory = TestingSession
        yield test_client


def _register(client, **overrides):
    body = {
        "full_name": "Ayşe Yılmaz",
        "email": "Ayse@Example.com",
        "password": "guclu1234",
    }
    body.update(overrides)
    return client.post("/auth/register", json=body)


def test_register_hashes_password_and_returns_session(client):
    response = _register(client)

    assert response.status_code == 201
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "ayse@example.com"
    assert data["user"]["full_name"] == "Ayşe Yılmaz"

    db = client.session_factory()
    user = db.query(models.User).one()
    assert user.password_hash.startswith("pbkdf2_sha256$")
    assert "guclu1234" not in user.password_hash
    db.close()


def test_register_rejects_duplicate_email(client):
    _register(client)
    response = _register(client, email="ayse@example.com ")
    assert response.status_code == 409


@pytest.mark.parametrize(
    "overrides",
    [
        {"email": "gecersiz-eposta"},
        {"password": "kisa1"},
        {"password": "sadeceharf"},
        {"full_name": " "},
    ],
)
def test_register_validates_input(client, overrides):
    assert _register(client, **overrides).status_code == 422


def test_login_with_correct_and_wrong_password(client):
    _register(client)

    ok = client.post(
        "/auth/login", json={"email": "AYSE@example.com", "password": "guclu1234"}
    )
    assert ok.status_code == 200
    assert ok.json()["access_token"]

    wrong = client.post(
        "/auth/login", json={"email": "ayse@example.com", "password": "yanlis1234"}
    )
    unknown = client.post(
        "/auth/login", json={"email": "yok@example.com", "password": "guclu1234"}
    )
    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_me_requires_valid_token(client):
    token = _register(client).json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ayse@example.com"

    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    assert (
        client.get(
            "/auth/me", headers={"Authorization": f"Bearer {tampered}"}
        ).status_code
        == 401
    )
    assert client.get("/auth/me").status_code == 401
