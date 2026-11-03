"""Phone videos must be decoded upright (rotation tag applied)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from video_processor import _open_video_capture  # noqa: E402


def test_open_video_capture_applies_the_rotation_tag(tmp_path: Path):
    fake = MagicMock()
    fake.isOpened.return_value = True
    fake.get.return_value = 30.0
    fake.read.return_value = (True, np.zeros((4, 4, 3), dtype=np.uint8))

    with patch("video_processor.cv2.VideoCapture", return_value=fake):
        _open_video_capture(tmp_path / "phone.mov")

    fake.set.assert_any_call(cv2.CAP_PROP_ORIENTATION_AUTO, 1)
