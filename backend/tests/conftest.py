"""Point the app at a throwaway database and upload folder before any test
module imports `database` or `main`, so tests never touch backend/test.db."""

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

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Rate-limit counters are process-global; start every test clean."""
    import auth
    from rate_limit import RateLimiter

    RateLimiter.reset_all()
    auth._failed_logins.clear()
    yield
