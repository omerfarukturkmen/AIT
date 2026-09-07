"""Tests for combined push-up form evaluation (elbow + shoulder + body)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pushup_analyzer import (  # noqa: E402
    FORM_CONFIRMATION_FRAMES,
    FORM_MSG_ELBOWS_FLARED,
    SHOULDER_ALIGNMENT_MAX,
    PushupAnalyzer,
)


def _a(
    elbow: float,
    *,
    shoulder: float = 70.0,
    hip: float = 170.0,
    body_alignment_angle: float | None = 175.0,
    body_line_offset: float | None = 0.01,
) -> dict:
    return {
        "avg_elbow": elbow,
        "avg_shoulder": shoulder,
        "avg_hip": hip,
        "body_alignment_angle": body_alignment_angle,
        "body_line_offset": body_line_offset,
        "alignment_side": "left",
        "left_elbow": elbow,
        "right_elbow": elbow,
        "left_shoulder": shoulder,
        "right_shoulder": shoulder,
        "left_hip": hip,
        "right_hip": hip,
    }


def _hold(analyzer: PushupAnalyzer, elbow: float, frames: int, **kwargs) -> None:
    for _ in range(frames):
        analyzer.analyze_frame(_a(elbow, **kwargs))


def _enter_active_phase(analyzer: PushupAnalyzer, **kwargs) -> None:
    _hold(analyzer, 165, 6, **kwargs)
    _hold(analyzer, 125, 8, **kwargs)


def test_normal_form_aligned():
    a = PushupAnalyzer()
    _enter_active_phase(a, shoulder=70.0)
    assert a.active_form_issues == []
    assert a.current_form_state == "aligned"


def test_elbows_flared_confirmed_after_three_frames():
    a = PushupAnalyzer()
    _enter_active_phase(a, shoulder=SHOULDER_ALIGNMENT_MAX + 10)
    assert "elbows_flared" in a.active_form_issues
    assert a.current_form_state == "elbows_flared"
    assert FORM_MSG_ELBOWS_FLARED in a.feedback
    assert a.form_errors["elbows_flared"] == 1


def test_single_frame_flare_not_confirmed():
    a = PushupAnalyzer()
    _enter_active_phase(a)
    before = dict(a.form_errors)
    a.analyze_frame(_a(125, shoulder=SHOULDER_ALIGNMENT_MAX + 10))
    _hold(a, 125, 5, shoulder=70.0)
    assert a.form_errors["elbows_flared"] == before["elbows_flared"]


def test_hip_sagging_still_works():
    a = PushupAnalyzer()
    _enter_active_phase(a, body_line_offset=0.09, body_alignment_angle=150)
    assert a.current_form_state == "hips_sagging"
    assert "hips_sagging" in a.active_form_issues


def test_hips_too_high_still_works():
    a = PushupAnalyzer()
    _enter_active_phase(a, body_line_offset=-0.09, body_alignment_angle=150)
    assert a.current_form_state == "hips_too_high"


def test_back_bent_still_works():
    a = PushupAnalyzer()
    _enter_active_phase(a, body_line_offset=0.0, body_alignment_angle=150)
    assert a.current_form_state == "back_bent"


def test_multiple_form_issues():
    a = PushupAnalyzer()
    _enter_active_phase(
        a,
        shoulder=SHOULDER_ALIGNMENT_MAX + 10,
        body_line_offset=0.09,
        body_alignment_angle=150,
    )
    assert a.current_form_state == "multiple_form_issues"
    assert "elbows_flared" in a.active_form_issues
    assert "hips_sagging" in a.active_form_issues


def test_metrics_incomplete_no_crash():
    a = PushupAnalyzer()
    _hold(a, 165, 4)
    a.analyze_frame(_a(125, body_alignment_angle=None))
    a.analyze_frame(_a(125, shoulder=None))
    assert a.rep_count == 0
    assert a.current_form_state in ("metrics_incomplete", "unknown", "aligned")


def test_error_segment_count_elbows_flared():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8, shoulder=SHOULDER_ALIGNMENT_MAX + 10)
    _hold(a, 125, FORM_CONFIRMATION_FRAMES, shoulder=SHOULDER_ALIGNMENT_MAX + 10)
    assert a.form_errors["elbows_flared"] == 1
    _hold(a, 125, 10, shoulder=SHOULDER_ALIGNMENT_MAX + 10)
    assert a.form_errors["elbows_flared"] == 1
    _hold(a, 125, FORM_CONFIRMATION_FRAMES, shoulder=70.0)
    assert a.form_errors["elbows_flared"] == 1
    _hold(a, 125, FORM_CONFIRMATION_FRAMES, shoulder=SHOULDER_ALIGNMENT_MAX + 10)
    assert a.form_errors["elbows_flared"] == 2


def _full_rep(analyzer: PushupAnalyzer, **kwargs) -> None:
    _hold(analyzer, 165, 6, **kwargs)
    _hold(analyzer, 125, 8, **kwargs)
    _hold(analyzer, 80, 8, **kwargs)
    _hold(analyzer, 120, 8, **kwargs)
    _hold(analyzer, 160, 8, **kwargs)


def test_rep_form_summary_includes_issues():
    a = PushupAnalyzer()
    _full_rep(
        a,
        shoulder=SHOULDER_ALIGNMENT_MAX + 10,
        body_line_offset=0.09,
        body_alignment_angle=150,
    )
    assert a.rep_count == 1
    assert a.valid_reps == 1
    assert "elbows_flared" in a.last_rep_form_issues
    assert "hips_sagging" in a.last_rep_form_issues


def test_form_error_does_not_invalidate_rep():
    a = PushupAnalyzer()
    _full_rep(a, shoulder=SHOULDER_ALIGNMENT_MAX + 10, body_line_offset=0.09, body_alignment_angle=150)
    assert a.rep_count == 1
    assert a.valid_reps == 1
    assert a.form_errors["elbows_flared"] >= 1 or a.form_errors["hips_not_aligned"] >= 1


def test_up_phase_shoulder_flare_not_confirmed():
    a = PushupAnalyzer()
    _hold(a, 165, 6, shoulder=SHOULDER_ALIGNMENT_MAX + 20)
    assert "elbows_flared" not in a.confirmed_form_issues
    assert a.form_errors["elbows_flared"] == 0


def test_active_phase_shoulder_flare_confirmed():
    a = PushupAnalyzer()
    _hold(a, 165, 6)
    _hold(a, 125, 8)
    _hold(a, 125, FORM_CONFIRMATION_FRAMES, shoulder=SHOULDER_ALIGNMENT_MAX + 15)
    assert "elbows_flared" in a.confirmed_form_issues


def test_get_result_idempotent_form_fields():
    a = PushupAnalyzer()
    _enter_active_phase(a, shoulder=SHOULDER_ALIGNMENT_MAX + 10)
    r1 = a.get_result()
    r2 = a.get_result()
    assert r1["form_errors"] == r2["form_errors"]
    assert r1["active_form_issues"] == r2["active_form_issues"]
    assert "form_metrics" in r1
    assert "elbows_flared" in r1["form_errors"]


def test_snapshot_has_combined_form_fields():
    a = PushupAnalyzer()
    snap = a.analyze_frame(_a(165))
    assert "form_metrics" in snap
    assert "active_form_issues" in snap
    assert "current_rep_form_issues" in snap
    assert "elbow_angle" in snap["form_metrics"]
