"""Point the app at a throwaway database, upload folder and e-mail outbox
before any test module imports the backend, so tests never touch
backend/test.db or real mailboxes."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

_TMP_DIR = tempfile.mkdtemp(prefix="ait-backend-tests-")
os.environ.setdefault(
    "DATABASE_URL", "sqlite:///" + os.path.join(_TMP_DIR, "test.db").replace("\\", "/")
)
os.environ.setdefault("UPLOAD_FOLDER", os.path.join(_TMP_DIR, "uploads"))
os.environ.setdefault("DEV_OUTBOX_DIR", os.path.join(_TMP_DIR, "outbox"))
for _name in ("APP_ENV", "SMTP_HOST", "GOOGLE_CLIENT_IDS", "APPLE_CLIENT_IDS"):
    os.environ.pop(_name, None)

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

OUTBOX_DIR = Path(os.environ["DEV_OUTBOX_DIR"])


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Rate-limit counters are process-global; start every test clean."""
    import auth
    from rate_limit import RateLimiter

    RateLimiter.reset_all()
    auth._failed_logins.clear()
    yield


@pytest.fixture(autouse=True)
def _run_analysis_inline(monkeypatch):
    """Runs queued analyses immediately so tests are deterministic."""
    import analysis_jobs

    monkeypatch.setattr(analysis_jobs, "submit", analysis_jobs.run_analysis)
    yield
