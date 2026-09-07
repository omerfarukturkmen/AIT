"""Tests for local PoseLandmark schema (no MediaPipe)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from pose_schema import POSE_CONNECTIONS, PoseLandmark  # noqa: E402


def test_pose_landmark_key_indices():
    assert PoseLandmark.LEFT_SHOULDER == 11
    assert PoseLandmark.RIGHT_SHOULDER == 12
    assert PoseLandmark.LEFT_HIP == 23
    assert PoseLandmark.RIGHT_HIP == 24
    assert PoseLandmark.LEFT_KNEE == 25
    assert PoseLandmark.RIGHT_KNEE == 26
    assert PoseLandmark.LEFT_ANKLE == 27
    assert PoseLandmark.RIGHT_ANKLE == 28


def test_pose_connections_cover_core_body():
    pairs = set(POSE_CONNECTIONS)
    assert (PoseLandmark.LEFT_SHOULDER, PoseLandmark.RIGHT_SHOULDER) in pairs
    assert (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_ELBOW) in pairs
    assert (PoseLandmark.LEFT_ELBOW, PoseLandmark.LEFT_WRIST) in pairs
    assert (PoseLandmark.LEFT_SHOULDER, PoseLandmark.LEFT_HIP) in pairs
    assert (PoseLandmark.LEFT_HIP, PoseLandmark.RIGHT_HIP) in pairs
    assert (PoseLandmark.LEFT_HIP, PoseLandmark.LEFT_KNEE) in pairs
    assert (PoseLandmark.LEFT_KNEE, PoseLandmark.LEFT_ANKLE) in pairs
    assert (PoseLandmark.LEFT_ANKLE, PoseLandmark.LEFT_HEEL) in pairs
    assert (PoseLandmark.LEFT_HEEL, PoseLandmark.LEFT_FOOT_INDEX) in pairs


def test_pose_schema_does_not_import_mediapipe():
    import pose_schema as schema

    source = Path(schema.__file__).read_text(encoding="utf-8")
    forbidden = ("mediapipe", "mp." + "solutions")
    for token in forbidden:
        assert token not in source
