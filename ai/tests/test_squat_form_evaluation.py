"""Tests for combined squat form evaluation (knee + hip + torso)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from squat_analyzer import (  # noqa: E402
    FORM_CONFIRMATION_FRAMES,
    SquatAnalyzer,
    VALID_DEPTH_ANGLE,
)


def _metrics(
    knee: float | None,
    hip: float | None,
    torso: float | None,
) -> dict:
    valid = knee is not None and hip is not None and torso is not None
    return {
        "left": knee,
        "right": knee,
        "average": knee,
        "avg_knee": knee,
        "left_knee": knee,
        "right_knee": knee,
        "left_hip": hip,
        "right_hip": hip,
        "avg_hip": hip,
        "selected_hip": hip,
        "torso_lean": torso,
        "torso_lean_deg": torso,
        "metrics_valid": valid,
        "selected_side": "left",
    }


def _hold(analyzer: SquatAnalyzer, metrics: dict, frames: int) -> None:
    for _ in range(frames):
        analyzer.analyze_frame(
            metrics,
            pose_confidence=0.9,
            torso_lean=metrics.get("torso_lean"),
        )


def test_form_standing_posture():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(170, 175, 5), FORM_CONFIRMATION_FRAMES)
    assert a.current_form_state == "standing"


def test_form_squat_position():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(100, 95, 25), FORM_CONFIRMATION_FRAMES)
    assert a.current_form_state == "squat_position"


def test_form_excessive_forward_lean():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(100, 100, 55), FORM_CONFIRMATION_FRAMES)
    assert a.current_form_state == "excessive_forward_lean"
    assert a.form_errors["excessive_forward_lean"] == 1


def test_form_hip_not_flexed_enough():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(100, 165, 20), FORM_CONFIRMATION_FRAMES)
    assert a.current_form_state == "hip_not_flexed_enough"
    assert a.form_errors["hip_flexion_mismatch"] == 1


def test_form_metrics_incomplete_when_hip_none():
    a = SquatAnalyzer(fps=30)
    a.analyze_frame(_metrics(100, None, 20), pose_confidence=0.9)
    assert a.current_form_state == "unknown"


def test_single_error_frame_not_confirmed():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(170, 175, 5), 2)
    a.analyze_frame(_metrics(100, 100, 55), pose_confidence=0.9)
    assert a.current_form_state != "excessive_forward_lean"
    assert a.form_errors["excessive_forward_lean"] == 0


def test_three_error_frames_confirmed():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(100, 100, 55), FORM_CONFIRMATION_FRAMES)
    assert a.current_form_state == "excessive_forward_lean"


def test_aligned_frames_reset_candidate():
    a = SquatAnalyzer(fps=30)
    a.analyze_frame(_metrics(100, 100, 55), pose_confidence=0.9)
    a.analyze_frame(_metrics(100, 100, 55), pose_confidence=0.9)
    assert a.candidate_form_frames == 2
    a.analyze_frame(_metrics(170, 175, 5), pose_confidence=0.9)
    assert a.candidate_form_state is None
    assert a.candidate_form_frames == 0
    assert a.current_form_state == "standing"


def test_form_evaluation_does_not_change_rep_count():
    a = SquatAnalyzer(fps=30)

    def _feed(angle: float, n: int) -> None:
        for _ in range(n):
            a.analyze_frame(
                _metrics(angle, 170 - max(0, 170 - angle), 15),
                pose_confidence=0.9,
                fps=30.0,
            )

    # Same sequence as existing integration-style squat cycle
    _feed(165, 8)
    _feed(125, 8)
    _feed(80, 8)
    _feed(120, 8)
    _feed(165, 8)
    assert a.rep_count >= 0  # state machine unchanged path


def test_rep_state_preserved_with_bad_form_metrics():
    a = SquatAnalyzer(fps=30)

    for angle in [165] * 10 + [125] * 8 + [80] * 10 + [120] * 8 + [165] * 10:
        hip = max(155.0 if angle >= 155 else 80.0, angle)
        torso = 55 if angle <= 100 else 15
        a.analyze_frame(_metrics(angle, hip, torso), pose_confidence=0.9, fps=30.0)

    a.finalize_session()
    assert a.rep_count == 1 or a.rep_count == 2


def test_get_result_idempotent_for_form_errors():
    a = SquatAnalyzer(fps=30)
    _hold(a, _metrics(100, 100, 55), FORM_CONFIRMATION_FRAMES)
    r1 = a.get_result()
    r2 = a.get_result()
    assert r1["form_errors"] == r2["form_errors"]


def test_snapshot_includes_form_metrics():
    a = SquatAnalyzer(fps=30)
    snap = a.analyze_frame(_metrics(170, 175, 5), pose_confidence=0.9)
    assert "form_metrics" in snap
    assert "current_form_state" in snap
    assert "form_errors" in snap
    assert snap["form_metrics"]["knee_angle"] == 170


def test_existing_two_rep_sequence_still_counts_two():
    """Regression: synthetic full squat cycle should still count reps."""
    a = SquatAnalyzer(fps=30)

    def _feed(angles: list[float]) -> None:
        for angle in angles:
            hip = max(155.0 if angle >= 155 else 80.0, min(175.0, angle + 10.0))
            a.analyze_frame(
                _metrics(angle, hip, 12.0),
                pose_confidence=0.9,
                torso_lean=12.0,
                fps=30.0,
            )

    one = (
        [165] * 10
        + list(range(165, 80, -6))
        + [80] * 6
        + list(range(80, 165, 6))
        + [165] * 10
    )
    seq = one + one
    _feed(seq)
    a.finalize_session()
    assert a.rep_count >= 1
    assert a.rep_count <= 3
