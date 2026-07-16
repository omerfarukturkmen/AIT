"""Tests for PushupAnalyzer."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pushup_analyzer import PushupAnalyzer


def test_pushup_analyzer_initial_state():
    analyzer = PushupAnalyzer()
    assert analyzer.state == "up"
    assert analyzer.rep_count == 0


def test_pushup_analyzer_none_angles_no_crash():
    analyzer = PushupAnalyzer()
    analyzer.analyze_frame(
        {
            "avg_elbow": None,
            "avg_shoulder": None,
            "avg_hip": None,
        }
    )
    assert analyzer.rep_count == 0
    assert "Elbow angle not detected" in analyzer.feedback


def test_pushup_analyzer_complete_rep():
    analyzer = PushupAnalyzer()
    # up
    for _ in range(3):
        analyzer.analyze_frame({"avg_elbow": 165, "avg_shoulder": 80, "avg_hip": 170})
    # descending
    for _ in range(3):
        analyzer.analyze_frame({"avg_elbow": 120, "avg_shoulder": 80, "avg_hip": 170})
    # bottom
    for _ in range(3):
        analyzer.analyze_frame({"avg_elbow": 80, "avg_shoulder": 80, "avg_hip": 170})
    # ascending
    for _ in range(3):
        analyzer.analyze_frame({"avg_elbow": 120, "avg_shoulder": 80, "avg_hip": 170})
    # back to up
    for _ in range(3):
        analyzer.analyze_frame({"avg_elbow": 160, "avg_shoulder": 80, "avg_hip": 170})

    assert analyzer.rep_count == 1
    assert analyzer.valid_reps == 1
    result = analyzer.get_result()
    assert result["exercise"] == "pushup"
    assert result["rep_count"] == 1
