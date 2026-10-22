"""P0 security checks for the HTTP API: authentication on every data
endpoint, per-user data isolation, safe uploads, brute-force limits, CORS."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    import ai_analyzer  # noqa: F401
except ImportError:
    # The analyzer needs OpenCV/mediapipe; these tests only exercise the API
    # layer and patch analyze_video anyway.
    stub = types.ModuleType("ai_analyzer")

    class AnalysisError(Exception):
        def __init__(self, message="", status_code=500):
            super().__init__(message)
            self.message = message
            self.status_code = status_code

    stub.AnalysisError = AnalysisError
    stub.analyze_video = lambda *args, **kwargs: {"status": "failed"}
    sys.modules["ai_analyzer"] = stub

# ai_analyzer prepends ai/src (which has its own main.py) to sys.path.
sys.path.remove(str(BACKEND_DIR))
sys.path.insert(0, str(BACKEND_DIR))

import auth  # noqa: E402
import main  # noqa: E402
import models  # noqa: E402
from database import SessionLocal  # noqa: E402

PROTECTED = [
    ("get", "/auth/me", None),
    ("get", "/user-videos/1", None),
    ("get", "/user-analysis-history/1", None),
    ("get", "/analysis/1", None),
    ("get", "/analysis-history", None),
    ("post", "/upload-video", {"exercise_type": "squat"}),
    ("post", "/live-analysis", {"exercise_type": "squat", "frame_data": "x" * 30}),
    ("delete", "/videos/1", None),
    ("delete", "/auth/me", None),
    ("post", "/auth/logout", None),
]

# Smallest header that passes the MP4 signature check (ISO-BMFF "ftyp" box).
MP4_BYTES = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 16


def _fake_analysis(file_path, exercise_type):
    return {
        "status": "success",
        "score": 80,
        "repetition_count": 3,
        "feedback": "ok",
        "exercise_name": "Squat",
        "errors": [],
        "details": {},
    }


@pytest.fixture()
def client(monkeypatch):
    db = SessionLocal()
    for table in (models.AnalysisResult, models.Video, models.User):
        db.query(table).delete()
    db.commit()
    db.close()
    auth._failed_logins.clear()
    monkeypatch.setattr(main, "analyze_video", _fake_analysis)
    with TestClient(main.app) as test_client:
        yield test_client


def _signup(client, email):
    response = client.post(
        "/auth/register",
        json={"full_name": "Test Kişi", "email": email, "password": "guclu1234"},
    )
    assert response.status_code == 201
    data = response.json()
    return data["user"]["id"], {"Authorization": f"Bearer {data['access_token']}"}


def _upload(client, headers, filename="video.mp4", content=MP4_BYTES, **fields):
    return client.post(
        "/upload-video",
        headers=headers,
        data={"exercise_type": "squat", **fields},
        files={"file": (filename, content, "video/mp4")},
    )


@pytest.mark.parametrize("method,path,data", PROTECTED)
def test_endpoints_reject_missing_or_forged_token(client, method, path, data):
    kwargs = {"data": data} if data else {}
    if path == "/upload-video":
        kwargs["files"] = {"file": ("v.mp4", MP4_BYTES, "video/mp4")}

    assert getattr(client, method)(path, **kwargs).status_code == 401

    forged = {"Authorization": "Bearer eyJzdWIiOjF9.c2lnbmF0dXJl"}
    assert getattr(client, method)(path, headers=forged, **kwargs).status_code == 401


def test_users_cannot_read_each_others_data(client):
    alice_id, alice = _signup(client, "alice@example.com")
    bob_id, bob = _signup(client, "bob@example.com")

    upload = _upload(client, bob)
    assert upload.status_code == 200
    bob_analysis_id = upload.json()["data"]["analysis_id"]

    assert client.get(f"/user-videos/{bob_id}", headers=alice).status_code == 403
    assert (
        client.get(f"/user-analysis-history/{bob_id}", headers=alice).status_code
        == 403
    )
    assert client.get(f"/analysis/{bob_analysis_id}", headers=alice).status_code == 404
    assert client.get("/analysis-history", headers=alice).json()[
        "analysis_history"
    ] == []

    assert client.get(f"/analysis/{bob_analysis_id}", headers=bob).status_code == 200
    assert len(client.get(f"/user-videos/{bob_id}", headers=bob).json()) == 1


def test_upload_owner_comes_from_token_not_form(client):
    alice_id, alice = _signup(client, "alice@example.com")
    bob_id, _ = _signup(client, "bob@example.com")

    response = _upload(client, alice, user_id=str(bob_id))

    assert response.status_code == 200
    assert response.json()["data"]["user_id"] == alice_id
    db = SessionLocal()
    assert db.query(models.Video).one().owner_id == alice_id
    db.close()


def test_upload_filename_cannot_escape_folder(client):
    _, alice = _signup(client, "alice@example.com")

    response = _upload(client, alice, filename="../../evil.mp4")

    assert response.status_code == 200
    stored = response.json()["data"]["filename"]
    assert "evil" not in stored and "/" not in stored and "\\" not in stored
    assert os.path.isfile(os.path.join(main.UPLOAD_FOLDER, stored))
    assert not (Path(main.UPLOAD_FOLDER).parent.parent / "evil.mp4").exists()


def test_upload_size_limit(client, monkeypatch):
    _, alice = _signup(client, "alice@example.com")
    monkeypatch.setattr(main, "MAX_UPLOAD_BYTES", 10)

    response = _upload(client, alice, content=MP4_BYTES)

    assert response.status_code == 413
    db = SessionLocal()
    assert db.query(models.Video).count() == 0
    db.close()


def test_login_locks_after_repeated_failures(client):
    _signup(client, "alice@example.com")

    for _ in range(auth.MAX_FAILED_LOGINS):
        wrong = client.post(
            "/auth/login",
            json={"email": "alice@example.com", "password": "yanlis1234"},
        )
        assert wrong.status_code == 401

    locked = client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "guclu1234"}
    )
    assert locked.status_code == 429


def test_cors_only_allows_local_origins_by_default(client):
    def preflight(origin):
        return client.options(
            "/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
            },
        )

    assert (
        preflight("http://localhost:5055").headers.get("access-control-allow-origin")
        == "http://localhost:5055"
    )
    assert "access-control-allow-origin" not in preflight("https://evil.example").headers


def test_only_owner_can_delete_video_and_file_is_removed(client):
    _, alice = _signup(client, "alice@example.com")
    _, bob = _signup(client, "bob@example.com")
    data = _upload(client, bob).json()["data"]
    video_path = os.path.join(main.UPLOAD_FOLDER, data["filename"])

    assert client.delete(f"/videos/{data['video_id']}", headers=alice).status_code == 404
    assert os.path.isfile(video_path)

    assert client.delete(f"/videos/{data['video_id']}", headers=bob).status_code == 200
    assert not os.path.exists(video_path)
    assert client.get(f"/analysis/{data['analysis_id']}", headers=bob).status_code == 404


def test_delete_account_erases_all_user_data(client):
    _, alice = _signup(client, "alice@example.com")
    _, bob = _signup(client, "bob@example.com")
    alice_file = _upload(client, alice).json()["data"]["filename"]
    _upload(client, bob)

    assert client.delete("/auth/me", headers=alice).status_code == 200

    assert not os.path.exists(os.path.join(main.UPLOAD_FOLDER, alice_file))
    assert client.get("/auth/me", headers=alice).status_code == 401
    login = client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "guclu1234"}
    )
    assert login.status_code == 401
    db = SessionLocal()
    assert db.query(models.User).count() == 1
    assert db.query(models.Video).count() == 1
    assert db.query(models.AnalysisResult).count() == 1
    db.close()
