"""Front-camera squat support: view lock, 3D calibration, knee tracking."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from frontal_view import (  # noqa: E402
    VIEW_LOCK_FRAMES,
    FrontalSquatTracker,
    knee_tracking_errors,
)
from squat_analyzer import SquatAnalyzer  # noqa: E402

GOOD = {"out_left": 0.35, "out_right": 0.40, "shift": -0.025}
CAVED = {"out_left": -0.14, "out_right": 0.05, "shift": -0.095}
SHIFTED = {"out_left": 0.38, "out_right": -0.27, "shift": 0.325}


def test_knee_tracking_errors():
    assert knee_tracking_errors(GOOD, 90) == []
    assert knee_tracking_errors(CAVED, 110) == ["knee_valgus"]
    assert knee_tracking_errors(SHIFTED, 135) == ["knee_lateral_shift"]
    # Standing: knees sit slightly inside the ankles, which is not valgus.
    assert knee_tracking_errors(CAVED, 170) == []
    assert knee_tracking_errors(None, 90) == []


def _landmarks(shoulder_half_width: float) -> SimpleNamespace:
    pts = [SimpleNamespace(x=0.5, y=0.5, z=0.0, visibility=1.0) for _ in range(33)]
    for idx, x, y in (
        (11, 0.5 - shoulder_half_width, 0.30), (12, 0.5 + shoulder_half_width, 0.30),
        (23, 0.45, 0.55), (24, 0.55, 0.55),
        (25, 0.44, 0.72), (26, 0.56, 0.72),
        (27, 0.43, 0.90), (28, 0.57, 0.90),
    ):
        pts[idx] = SimpleNamespace(x=x, y=y, z=0.0, visibility=1.0)
    return SimpleNamespace(landmark=pts)


def _world_straight_legs() -> list[SimpleNamespace]:
    pts = [SimpleNamespace(x=0.0, y=0.0, z=0.0) for _ in range(33)]
    for idx, x, y in (
        (11, -0.2, -0.5), (12, 0.2, -0.5), (23, -0.1, 0.0), (24, 0.1, 0.0),
        (25, -0.1, 0.45), (26, 0.1, 0.45), (27, -0.1, 0.9), (28, 0.1, 0.9),
    ):
        pts[idx] = SimpleNamespace(x=x, y=y, z=0.0)
    return pts


def test_side_view_is_left_alone():
    tracker = FrontalSquatTracker()
    for _ in range(VIEW_LOCK_FRAMES + 2):
        out = tracker.update(_landmarks(0.02), _world_straight_legs(), 1000, 1000)
    assert tracker.view == "side"
    assert out is None


def test_front_view_uses_calibrated_3d_angles():
    tracker = FrontalSquatTracker()
    out = None
    for _ in range(VIEW_LOCK_FRAMES + 10):
        out = tracker.update(_landmarks(0.15), _world_straight_legs(), 1000, 1000)
    assert tracker.view == "frontal"
    assert out is not None
    assert out["average"] >= 170
    assert out["tracking"]["out_left"] > -0.2


def _feed(analyzer: SquatAnalyzer, angles: list[float], tracking: dict) -> None:
    for angle in angles:
        analyzer.analyze_frame(
            {
                "left": angle, "right": angle, "average": angle, "avg_knee": angle,
                "left_hip": angle, "right_hip": angle, "avg_hip": angle,
                "selected_hip": angle, "selected_side": "frontal",
                "frontal_tracking": tracking,
            },
            pose_confidence=0.95, torso_lean=10.0, fps=30.0,
            landmark_visibility_ok=True,
        )


def _squat(bottom: float) -> list[float]:
    down = [168 - (168 - bottom) * i / 17 for i in range(18)]
    return [168] * 12 + down + [bottom] * 4 + down[::-1] + [168] * 12


def test_deep_rep_with_caved_knees_is_faulty():
    clean = SquatAnalyzer(fps=30)
    _feed(clean, _squat(80), GOOD)
    assert clean.get_result()["valid_reps"] == 1

    caved = SquatAnalyzer(fps=30)
    _feed(caved, _squat(80), CAVED)
    result = caved.get_result()
    assert result["rep_count"] == 1
    assert result["valid_reps"] == 0
    assert result["rep_history"][0]["errors"] == ["knee_valgus"]
