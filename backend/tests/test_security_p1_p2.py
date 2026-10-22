"""P1/P2 security checks: upload content, input validation, rate limiting,
session revocation, error disclosure, security headers and log hygiene."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import textwrap
from datetime import timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]

from tests.test_api_security import MP4_BYTES, _fake_analysis, _signup, _upload  # noqa: E402

import auth  # noqa: E402
import main  # noqa: E402
import models  # noqa: E402
from database import SessionLocal  # noqa: E402

PASSWORD = "guclu1234"


@pytest.fixture()
def client(monkeypatch):
    db = SessionLocal()
    for table in (
        models.AnalysisResult,
        models.Video,
        models.AuthSession,
        models.User,
    ):
        db.query(table).delete()
    db.commit()
    db.close()
    monkeypatch.setattr(main, "analyze_video", _fake_analysis)
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client


def _login(client, email, remember_me=True):
    return client.post(
        "/auth/login",
        json={"email": email, "password": PASSWORD, "remember_me": remember_me},
    )


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


# --- P1: file upload ------------------------------------------------------


@pytest.mark.parametrize(
    "filename,content,status",
    [
        ("virus.mp4", b"MZ\x90\x00" + b"\x00" * 60, 415),  # renamed .exe
        ("script.mov", b"#!/bin/sh\nrm -rf /\n", 415),
        ("fake.avi", MP4_BYTES, 415),  # MP4 data with .avi extension
        ("empty.mp4", b"", 400),
        ("x" * 300 + ".mp4", MP4_BYTES, 400),  # absurd filename
        ("doc.pdf", b"%PDF-1.7", 400),
    ],
)
def test_rejects_non_video_uploads(client, filename, content, status):
    _, alice = _signup(client, "alice@example.com")

    response = _upload(client, alice, filename=filename, content=content)

    assert response.status_code == status
    assert os.listdir(main.UPLOAD_FOLDER) == [] or all(
        not name.startswith(("virus", "script", "fake", "empty"))
        for name in os.listdir(main.UPLOAD_FOLDER)
    )
    db = SessionLocal()
    assert db.query(models.Video).count() == 0
    db.close()


def test_accepts_real_container_signatures(client):
    _, alice = _signup(client, "alice@example.com")
    avi = b"RIFF\x00\x00\x00\x00AVI LIST" + b"\x00" * 16

    assert _upload(client, alice, filename="a.mp4").status_code == 200
    assert _upload(client, alice, filename="b.avi", content=avi).status_code == 200


def test_rejected_upload_leaves_no_file_behind(client):
    _, alice = _signup(client, "alice@example.com")
    before = set(os.listdir(main.UPLOAD_FOLDER))

    _upload(client, alice, filename="virus.mp4", content=b"MZ" + b"\x00" * 40)

    assert set(os.listdir(main.UPLOAD_FOLDER)) == before


# --- P1: input validation -------------------------------------------------


@pytest.mark.parametrize(
    "overrides",
    [
        {"full_name": "A" * 101},
        {"email": "a" * 250 + "@x.co"},
        {"password": "a1" * 65},
        {"full_name": "Ayşe\x00 Yılmaz"},
        {"full_name": "123 456"},
    ],
)
def test_register_rejects_malformed_input(client, overrides):
    body = {"full_name": "Ayşe Yılmaz", "email": "a@example.com", "password": PASSWORD}
    body.update(overrides)

    assert client.post("/auth/register", json=body).status_code == 422


def test_validation_errors_do_not_echo_submitted_values(client):
    secret = "a1" * 70  # too long -> schema validation error
    response = client.post(
        "/auth/register",
        json={"full_name": "Ayşe Yılmaz", "email": "a@example.com", "password": secret},
    )

    assert response.status_code == 422
    assert secret not in response.text
    assert response.json()["fields"] == ["password"]


def test_wrong_types_are_rejected(client):
    response = client.post("/auth/login", json={"email": ["x"], "password": 5})
    assert response.status_code == 422


def test_live_analysis_limits_frame_size_and_exercise(client):
    _, alice = _signup(client, "alice@example.com")

    too_big = client.post(
        "/live-analysis",
        headers=alice,
        data={"exercise_type": "squat", "frame_data": "x" * (main.MAX_FRAME_DATA_LENGTH + 1)},
    )
    unknown = client.post(
        "/live-analysis",
        headers=alice,
        data={"exercise_type": "deadlift'; DROP TABLE users;--", "frame_data": "x" * 30},
    )

    assert too_big.status_code == 422
    assert unknown.status_code in (400, 422)
    db = SessionLocal()
    assert db.query(models.User).count() == 1  # nothing was dropped
    db.close()


# --- P1: rate limiting ----------------------------------------------------


def test_registration_is_rate_limited_per_ip(client):
    for i in range(5):
        _signup(client, f"user{i}@example.com")

    response = client.post(
        "/auth/register",
        json={"full_name": "Altı Kişi", "email": "u6@example.com", "password": PASSWORD},
    )

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0


def test_uploads_are_rate_limited_per_user(client):
    _, alice = _signup(client, "alice@example.com")
    _, bob = _signup(client, "bob@example.com")

    for _ in range(10):
        assert _upload(client, alice).status_code == 200

    assert _upload(client, alice).status_code == 429
    assert _upload(client, bob).status_code == 200  # other users unaffected


def test_global_request_limit(client, monkeypatch):
    monkeypatch.setattr(main._global_limiter, "max_requests", 3)

    statuses = [client.get("/").status_code for _ in range(4)]

    assert statuses == [200, 200, 200, 429]


# --- P1: session security -------------------------------------------------


def test_logout_revokes_only_that_token(client):
    _signup(client, "alice@example.com")
    phone = _login(client, "alice@example.com").json()["access_token"]
    laptop = _login(client, "alice@example.com").json()["access_token"]

    assert client.post("/auth/logout", headers=_bearer(phone)).status_code == 204

    assert client.get("/auth/me", headers=_bearer(phone)).status_code == 401
    assert client.get("/auth/me", headers=_bearer(laptop)).status_code == 200


def test_logout_all_devices(client):
    _signup(client, "alice@example.com")
    phone = _login(client, "alice@example.com").json()["access_token"]
    laptop = _login(client, "alice@example.com").json()["access_token"]

    client.post("/auth/logout?all_devices=true", headers=_bearer(phone))

    assert client.get("/auth/me", headers=_bearer(laptop)).status_code == 401


def test_session_lifetime_follows_remember_me(client):
    _signup(client, "alice@example.com")

    short = _login(client, "alice@example.com", remember_me=False).json()
    long = _login(client, "alice@example.com", remember_me=True).json()

    assert short["expires_in"] == int(timedelta(hours=12).total_seconds())
    assert long["expires_in"] == int(timedelta(days=30).total_seconds())


def test_expired_server_session_is_rejected(client):
    _, alice = _signup(client, "alice@example.com")
    db = SessionLocal()
    for session in db.query(models.AuthSession).all():
        session.expires_at = auth._utcnow() - timedelta(seconds=1)
    db.commit()
    db.close()

    assert client.get("/auth/me", headers=alice).status_code == 401


def test_signed_token_without_server_session_is_rejected(client):
    user_id, _ = _signup(client, "alice@example.com")
    db = SessionLocal()
    token = auth.create_access_token(db, user_id)
    db.query(models.AuthSession).delete()  # e.g. revoked by an admin
    db.commit()
    db.close()

    assert client.get("/auth/me", headers=_bearer(token)).status_code == 401


def test_token_is_not_reusable_after_account_deletion(client):
    _, alice = _signup(client, "alice@example.com")
    client.delete("/auth/me", headers=alice)

    db = SessionLocal()
    assert db.query(models.AuthSession).count() == 0
    db.close()


# --- P2: error handling ---------------------------------------------------


def test_analysis_errors_hide_server_paths(client, monkeypatch):
    _, alice = _signup(client, "alice@example.com")
    secret_path = r"C:\srv\ait\uploaded_videos\internal.mp4"

    def failing_analysis(file_path, exercise_type):
        raise main.AnalysisError(f"Video dosyasi bos: {secret_path}", status_code=422)

    monkeypatch.setattr(main, "analyze_video", failing_analysis)
    response = _upload(client, alice)

    assert response.status_code == 422
    assert "srv" not in response.text and "uploaded_videos" not in response.text
    db = SessionLocal()
    assert "srv" not in db.query(models.AnalysisResult).one().feedback
    db.close()


def test_unhandled_errors_return_generic_message(client, monkeypatch):
    _, alice = _signup(client, "alice@example.com")
    video_id = _upload(client, alice).json()["data"]["video_id"]

    def boom(db, videos):
        raise RuntimeError("sqlite:///C:/srv/ait/test.db is locked")

    monkeypatch.setattr(main, "_delete_videos", boom)
    response = client.delete(f"/videos/{video_id}", headers=alice)

    assert response.status_code == 500
    assert response.json() == {"detail": main.GENERIC_ERROR}
    assert "Traceback" not in response.text and "sqlite" not in response.text


# --- P2: web security -----------------------------------------------------


def test_security_headers_on_success_and_error_responses(client):
    for response in (client.get("/"), client.get("/auth/me")):
        headers = response.headers
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["x-frame-options"] == "DENY"
        assert headers["referrer-policy"] == "no-referrer"
        assert headers["cache-control"] == "no-store"
        assert "default-src 'none'" in headers["content-security-policy"]


def test_production_mode_hardening():
    """Runs in a subprocess because these settings are read at import time."""
    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, sys.argv[1])
        from fastapi.testclient import TestClient
        import main

        client = TestClient(main.app, base_url="http://api.example.com")
        assert client.get("/docs").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        ok = client.get("/", headers={"host": "api.example.com"})
        assert ok.status_code == 200, ok.status_code
        assert "max-age" in ok.headers["strict-transport-security"]
        bad = client.get("/", headers={"host": "evil.example"})
        assert bad.status_code == 400, bad.status_code
        print("ok")
        """
    )
    env = {
        **os.environ,
        "APP_ENV": "production",
        "ALLOWED_HOSTS": "api.example.com",
        "AUTH_SECRET_KEY": "test-only-secret",
    }
    result = subprocess.run(
        [sys.executable, "-c", script, str(BACKEND_DIR)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(BACKEND_DIR),
        timeout=300,
    )

    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.strip().endswith("ok")


def test_development_mode_keeps_docs(client):
    assert client.get("/docs").status_code == 200


# --- P2: log hygiene ------------------------------------------------------


def test_logs_never_contain_passwords_or_tokens(client, caplog):
    caplog.set_level(logging.DEBUG)

    _, alice = _signup(client, "alice@example.com")
    token = alice["Authorization"].split()[1]
    client.post("/auth/login", json={"email": "alice@example.com", "password": "yanlis1234"})
    _login(client, "alice@example.com")
    _upload(client, alice)
    client.get("/auth/me", headers=alice)

    logged = caplog.text
    assert PASSWORD not in logged
    assert "yanlis1234" not in logged
    assert token not in logged
    assert "alice@example.com" not in logged


def test_redaction_filter_masks_secrets():
    record = logging.LogRecord(
        "x",
        logging.INFO,
        __file__,
        1,
        'headers=%s body=%s',
        ("Authorization: Bearer abc.def-123", '{"password": "hunter22"}'),
        None,
    )

    main.RedactSecretsFilter().filter(record)

    message = record.getMessage()
    assert "abc.def-123" not in message and "hunter22" not in message
    assert "[REDACTED]" in message
