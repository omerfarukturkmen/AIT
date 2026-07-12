"""Tests for push-up angle utilities."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.angle_utils import calculate_pushup_angles


def test_calculate_pushup_angles_with_none():
    result = calculate_pushup_angles(None, 640, 480)
    assert result["avg_elbow"] is None
    assert result["avg_shoulder"] is None
    assert result["avg_hip"] is None
