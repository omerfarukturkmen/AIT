"""Migrations, background analysis, video retention, password reset,
e-mail verification and Google/Apple sign-in."""

from __future__ import annotations

import email
import os
import re
import sqlite3
import subprocess
import sys
import textwrap
import time
from datetime import timedelta
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from tests.conftest import BACKEND_DIR, OUTBOX_DIR
from tests.test_api_security import MP4_BYTES, _fake_analysis, _signup, _upload

import account_recovery  # noqa: E402
import ai_analyzer  # noqa: E402
import analysis_jobs  # noqa: E402
import main  # noqa: E402
import models  # noqa: E402
import social_auth  # noqa: E402
from database import SessionLocal  # noqa: E402

PASSWORD = "guclu1234"


@pytest.fixture()
def client(monkeypatch):
    db = SessionLocal()
    for table in (
        models.AnalysisResult,
        models.Video,
        models.AuthSession,
        models.OneTimeCode,
        models.SocialIdentity,
        models.User,
    ):
        db.query(table).delete()
    db.commit()
    db.close()
    for message in OUTBOX_DIR.glob("*.eml"):
        message.unlink()
    monkeypatch.setattr(ai_analyzer, "analyze_video", _fake_analysis)
    with TestClient(main.app, raise_server_exceptions=False) as test_client:
        yield test_client


def _latest_code() -> str:
    newest = max(OUTBOX_DIR.glob("*.eml"), key=os.path.getmtime)
    body = email.message_from_bytes(newest.read_bytes()).get_payload(decode=True)
    return re.search(rb"\b(\d{6})\b", body).group(1).decode()


def _login(client, email_address, password=PASSWORD):
    return client.post("/auth/login", json={"email": email_address, "password": password})


# --- Migrations -----------------------------------------------------------


def test_migrations_upgrade_a_pre_auth_database(tmp_path):
    """The original schema (plaintext users table) upgrades without data loss."""
    db_file = tmp_path / "legacy.db"
    con = sqlite3.connect(db_file)
    con.executescript(
        """
        CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR UNIQUE, password VARCHAR);
        CREATE TABLE videos (id INTEGER PRIMARY KEY, filename VARCHAR, owner_id INTEGER,
            exercise_type VARCHAR, score INTEGER, repetition_count INTEGER, feedback VARCHAR);
        CREATE TABLE analysis_results (id INTEGER PRIMARY KEY, video_id INTEGER,
            exercise_type VARCHAR, score INTEGER, repetition_count INTEGER,
            feedback VARCHAR, status VARCHAR, created_at DATETIME);
        INSERT INTO users (id, username, password) VALUES (1, 'eski', 'x');
        INSERT INTO videos (id, filename, owner_id) VALUES (1, 'IMG.mp4', 1);
        """
    )
    con.commit()
    con.close()

    script = textwrap.dedent(
        """
        import sys
        sys.path.insert(0, sys.argv[1])
        import migrate
        migrate.upgrade_database()
        migrate.upgrade_database()
        """
    )
    env = {**os.environ, "DATABASE_URL": "sqlite:///" + str(db_file).replace("\\", "/")}
    result = subprocess.run(
        [sys.executable, "-c", script, str(BACKEND_DIR)],
        capture_output=True, text=True, env=env, cwd=str(tmp_path), timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]

    con = sqlite3.connect(db_file)
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    user_columns = {r[1] for r in con.execute("pragma table_info(users)")}
    assert {"auth_sessions", "one_time_codes", "social_identities"} <= tables
    assert {"password_hash", "full_name", "email_verified"} <= user_columns
    assert "password" not in user_columns  # plaintext column dropped
    assert con.execute("select username from users").fetchall() == [("eski",)]
    assert con.execute("select count(*) from videos").fetchone() == (1,)
    assert con.execute("select version_num from alembic_version").fetchone() == (
        "0003_drop_plaintext_password",
    )
    con.close()


# --- Background analysis --------------------------------------------------


def test_upload_returns_pending_then_result_is_polled(client, monkeypatch):
    queued = []
    monkeypatch.setattr(analysis_jobs, "submit", queued.append)
    _, alice = _signup(client, "alice@example.com")

    upload = _upload(client, alice)
    analysis_id = upload.json()["data"]["analysis_id"]

    assert upload.status_code == 202
    assert upload.json()["data"]["analysis_status"] == "pending"
    pending = client.get(f"/analysis/{analysis_id}", headers=alice).json()
    assert pending["status"] == "pending"

    analysis_jobs.run_analysis(queued.pop())
    done = client.get(f"/analysis/{analysis_id}", headers=alice).json()

    assert done["status"] == "success"
    assert done["data"]["analysis_status"] == "completed"
    assert done["data"]["repetition_count"] == 3


def test_analysis_list_is_newest_first_with_results(client):
    _, alice = _signup(client, "alice@example.com")
    first = _upload(client, alice).json()["data"]["analysis_id"]
    second = _upload(client, alice).json()["data"]["analysis_id"]

    analyses = client.get("/analyses", headers=alice).json()["analyses"]

    assert [a["analysis_id"] for a in analyses] == [second, first]
    assert analyses[0]["result"]["data"]["score"] == 80


def test_limits_concurrent_analyses_per_user(client, monkeypatch):
    monkeypatch.setattr(analysis_jobs, "submit", lambda analysis_id: None)
    _, alice = _signup(client, "alice@example.com")

    for _ in range(main.MAX_ACTIVE_ANALYSES_PER_USER):
        assert _upload(client, alice).status_code == 202

    assert _upload(client, alice).status_code == 429


def test_interrupted_analyses_are_marked_failed(client, monkeypatch):
    monkeypatch.setattr(analysis_jobs, "submit", lambda analysis_id: None)
    _, alice = _signup(client, "alice@example.com")
    analysis_id = _upload(client, alice).json()["data"]["analysis_id"]

    assert analysis_jobs.fail_interrupted_analyses() == 1

    data = client.get(f"/analysis/{analysis_id}", headers=alice).json()
    assert data["status"] == "failed"
    assert "tekrar yükle" in data["data"]["feedback"]


# --- Video retention ------------------------------------------------------


def _age_video(video_id: int, days: int) -> str:
    db = SessionLocal()
    video = db.get(models.Video, video_id)
    video.created_at = models.utcnow() - timedelta(days=days)
    db.commit()
    path = analysis_jobs.video_path(video)
    db.close()
    return path


def test_retention_deletes_old_files_and_keeps_results(client):
    _, alice = _signup(client, "alice@example.com")
    old = _upload(client, alice).json()["data"]
    recent = _upload(client, alice).json()["data"]
    old_path = _age_video(old["video_id"], 31)
    recent_path = _age_video(recent["video_id"], 5)

    assert analysis_jobs.delete_expired_videos(retention_days=30) == 1

    assert not os.path.exists(old_path)
    assert os.path.exists(recent_path)
    result = client.get(f"/analysis/{old['analysis_id']}", headers=alice).json()
    assert result["data"]["score"] == 80  # the analysis survives the file


def test_retention_skips_legacy_rows_and_running_analyses(client, monkeypatch):
    _, alice = _signup(client, "alice@example.com")
    legacy = _upload(client, alice).json()["data"]
    db = SessionLocal()
    db.get(models.Video, legacy["video_id"]).created_at = None  # pre-policy row
    db.commit()
    db.close()

    monkeypatch.setattr(analysis_jobs, "submit", lambda analysis_id: None)
    running = _upload(client, alice).json()["data"]
    running_path = _age_video(running["video_id"], 90)

    assert analysis_jobs.delete_expired_videos(retention_days=30) == 0
    assert os.path.exists(running_path)
    assert analysis_jobs.delete_expired_videos(retention_days=0) == 0


# --- Password reset -------------------------------------------------------


def test_password_reset_flow(client):
    _signup(client, "alice@example.com")
    old_session = _login(client, "alice@example.com").json()["access_token"]

    response = client.post("/auth/password-reset/request", json={"email": "alice@example.com"})
    code = _latest_code()

    assert response.status_code == 202
    wrong = client.post(
        "/auth/password-reset/confirm",
        json={"email": "alice@example.com", "code": "000000" if code != "000000" else "111111",
              "new_password": "yeniSifre99"},
    )
    assert wrong.status_code == 400

    ok = client.post(
        "/auth/password-reset/confirm",
        json={"email": "alice@example.com", "code": code, "new_password": "yeniSifre99"},
    )
    assert ok.status_code == 200
    assert _login(client, "alice@example.com").status_code == 401
    assert _login(client, "alice@example.com", "yeniSifre99").status_code == 200
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {old_session}"})
    assert me.status_code == 401  # all sessions ended
    # A used code cannot be replayed.
    replay = client.post(
        "/auth/password-reset/confirm",
        json={"email": "alice@example.com", "code": code, "new_password": "baskaSifre77"},
    )
    assert replay.status_code == 400


def test_password_reset_does_not_reveal_accounts(client):
    _signup(client, "alice@example.com")
    known = client.post("/auth/password-reset/request", json={"email": "alice@example.com"})
    unknown = client.post("/auth/password-reset/request", json={"email": "yok@example.com"})

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()


def test_reset_code_locks_after_too_many_attempts(client):
    _signup(client, "alice@example.com")
    client.post("/auth/password-reset/request", json={"email": "alice@example.com"})
    code = _latest_code()
    wrong = "000000" if code != "000000" else "111111"

    for _ in range(account_recovery.MAX_CODE_ATTEMPTS):
        client.post(
            "/auth/password-reset/confirm",
            json={"email": "alice@example.com", "code": wrong, "new_password": "yeniSifre99"},
        )
    correct = client.post(
        "/auth/password-reset/confirm",
        json={"email": "alice@example.com", "code": code, "new_password": "yeniSifre99"},
    )

    assert correct.status_code == 400


def test_expired_reset_code_is_rejected(client):
    _signup(client, "alice@example.com")
    client.post("/auth/password-reset/request", json={"email": "alice@example.com"})
    code = _latest_code()
    db = SessionLocal()
    for record in db.query(models.OneTimeCode).all():
        record.expires_at = models.utcnow() - timedelta(seconds=1)
    db.commit()
    db.close()

    response = client.post(
        "/auth/password-reset/confirm",
        json={"email": "alice@example.com", "code": code, "new_password": "yeniSifre99"},
    )
    assert response.status_code == 400


def test_reset_codes_are_not_stored_or_logged(client, caplog):
    _signup(client, "alice@example.com")
    client.post("/auth/password-reset/request", json={"email": "alice@example.com"})
    code = _latest_code()

    db = SessionLocal()
    stored = [r.code_hash for r in db.query(models.OneTimeCode).all()]
    db.close()
    assert all(code not in value for value in stored)
    assert code not in caplog.text


def test_reset_unavailable_in_production_without_smtp(client, monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SMTP_HOST", raising=False)

    response = client.post("/auth/password-reset/request", json={"email": "a@example.com"})

    assert response.status_code == 503


# --- E-mail verification --------------------------------------------------


def test_signup_sends_verification_code(client):
    _, alice = _signup(client, "alice@example.com")
    code = _latest_code()

    assert client.get("/auth/me", headers=alice).json()["email_verified"] is False
    bad = client.post("/auth/email-verification/confirm", headers=alice,
                      json={"code": "000000" if code != "000000" else "111111"})
    assert bad.status_code == 400

    ok = client.post("/auth/email-verification/confirm", headers=alice, json={"code": code})
    assert ok.status_code == 200
    assert client.get("/auth/me", headers=alice).json()["email_verified"] is True


def test_verification_code_can_be_resent(client):
    _, alice = _signup(client, "alice@example.com")
    first = _latest_code()
    time.sleep(0.02)

    response = client.post("/auth/email-verification/request", headers=alice)
    second = _latest_code()

    assert response.status_code == 202
    old = client.post("/auth/email-verification/confirm", headers=alice, json={"code": first})
    if first != second:
        assert old.status_code == 400  # the previous code was replaced
    new = client.post("/auth/email-verification/confirm", headers=alice, json={"code": second})
    assert new.status_code == 200


# --- Google / Apple sign-in -----------------------------------------------

_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_OTHER_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
GOOGLE_CLIENT = "test-client.apps.googleusercontent.com"
APPLE_CLIENT = "com.ait.fitness"


@pytest.fixture()
def providers(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_IDS", GOOGLE_CLIENT)
    monkeypatch.setenv("APPLE_CLIENT_IDS", APPLE_CLIENT)
    monkeypatch.setattr(social_auth, "signing_key", lambda provider, token: _KEY.public_key())


def _token(key=_KEY, **overrides):
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": GOOGLE_CLIENT,
        "sub": "google-user-1",
        "email": "ayse@gmail.com",
        "email_verified": True,
        "name": "Ayşe Yılmaz",
        "iat": now,
        "exp": now + 600,
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def test_social_sign_in_not_configured(client):
    response = client.post("/auth/google", json={"id_token": _token()})
    assert response.status_code == 503
    assert "yapılandırılmadı" in response.json()["detail"]


def test_google_sign_in_creates_and_reuses_account(client, providers):
    first = client.post("/auth/google", json={"id_token": _token()})
    second = client.post("/auth/google", json={"id_token": _token()})

    assert first.status_code == second.status_code == 200
    user = first.json()["user"]
    assert user["email"] == "ayse@gmail.com"
    assert user["full_name"] == "Ayşe Yılmaz"
    assert user["email_verified"] is True
    assert second.json()["user"]["id"] == user["id"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {first.json()['access_token']}"})
    assert me.status_code == 200


def test_google_links_existing_password_account(client, providers):
    user_id, _ = _signup(client, "ayse@gmail.com")

    response = client.post("/auth/google", json={"id_token": _token()})

    assert response.json()["user"]["id"] == user_id
    assert _login(client, "ayse@gmail.com").status_code == 200  # password still works


@pytest.mark.parametrize(
    "token",
    [
        pytest.param(lambda: _token(aud="someone-elses-app"), id="wrong-audience"),
        pytest.param(lambda: _token(iss="https://evil.example"), id="wrong-issuer"),
        pytest.param(lambda: _token(exp=int(time.time()) - 10), id="expired"),
        pytest.param(lambda: _token(key=_OTHER_KEY), id="forged-signature"),
        pytest.param(lambda: _token(email_verified=False), id="unverified-email"),
        pytest.param(lambda: "not-a-jwt", id="garbage"),
    ],
)
def test_google_rejects_invalid_tokens(client, providers, token):
    response = client.post("/auth/google", json={"id_token": token()})
    assert response.status_code == 401
    db = SessionLocal()
    assert db.query(models.User).count() == 0
    db.close()


def test_apple_sign_in_uses_name_from_app(client, providers):
    token = _token(
        iss="https://appleid.apple.com",
        aud=APPLE_CLIENT,
        sub="apple-user-1",
        email="abc123@privaterelay.appleid.com",
        email_verified="true",
        name=None,
    )

    response = client.post(
        "/auth/apple", json={"identity_token": token, "full_name": "Mehmet Demir"}
    )

    assert response.status_code == 200
    assert response.json()["user"]["full_name"] == "Mehmet Demir"


def test_google_token_cannot_be_used_for_apple(client, providers):
    response = client.post("/auth/apple", json={"identity_token": _token()})
    assert response.status_code == 401


def test_account_deletion_removes_social_links_and_codes(client, providers):
    session = client.post("/auth/google", json={"id_token": _token()}).json()
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    client.post("/auth/password-reset/request", json={"email": "ayse@gmail.com"})

    assert client.delete("/auth/me", headers=headers).status_code == 200

    db = SessionLocal()
    assert db.query(models.SocialIdentity).count() == 0
    assert db.query(models.OneTimeCode).count() == 0
    db.close()
