"""Camera warnings come with stable codes the app localizes."""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from video_processor import (  # noqa: E402
    CAMERA_WARNING_TEXTS,
    _build_camera_warnings,
    _camera_warning_codes,
)


def test_codes_and_texts_match():
    stats = {
        "camera_too_far_frames": 40,
        "camera_too_close_frames": 0,
        "low_confidence_frames": 50,
    }
    codes = _camera_warning_codes(stats, 100)
    assert codes == ["camera_too_far", "low_pose_confidence"]
    assert _build_camera_warnings(stats, 100) == [
        CAMERA_WARNING_TEXTS[code] for code in codes
    ]


def test_clean_video_has_no_codes():
    assert _camera_warning_codes({}, 100) == []


def test_empty_video_is_unreadable():
    assert _camera_warning_codes({}, 0) == ["video_unreadable"]
