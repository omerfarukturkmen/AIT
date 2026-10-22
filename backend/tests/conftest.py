"""Point the app at a throwaway database and upload folder before any test
module imports `database` or `main`, so tests never touch backend/test.db."""

import os
import tempfile

_TMP_DIR = tempfile.mkdtemp(prefix="ait-backend-tests-")
os.environ.setdefault(
    "DATABASE_URL", "sqlite:///" + os.path.join(_TMP_DIR, "test.db").replace("\\", "/")
)
os.environ.setdefault("UPLOAD_FOLDER", os.path.join(_TMP_DIR, "uploads"))
