"""Tests for PushupAnalyzer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.pushup_analyzer import PushupAnalyzer


def _a(
    elbow: float,
    shoulder: float = 80.0,
    hip: float = 170.0,
    *,
    body_alignment_angle: float | None = 175.0,
    body_line_offset: float | None = 0.01,
    alignment_side: str = "left",
) -> dict:
    return {
        "avg_elbow": elbow,
        "avg_shoulder": shoulder,
        "avg_hip": hip,
        "body_alignment_angle": body_alignment_angle,
        "body_line_offset": body_line_offset,
        "alignment_side": alignment_side,
    }


def _hold(
    analyzer: PushupAnalyzer,
    elbow: float,
    frames: int,
    **form_kwargs,
) -> None:
    for _ in range(frames):
        analyzer.analyze_frame(_a(elbow, **form_kwargs))


def _full_rep(analyzer: PushupAnalyzer, **form_kwargs) -> None:
    """Drive one complete up → descending → bottom → ascending → up cycle."""
    _hold(analyzer, 165, 6, **form_kwargs)  # settle in up / fill median
    _hold(analyzer, 125, 8, **form_kwargs)  # descending (median + 3-frame confirm)
    _hold(analyzer, 80, 8, **form_kwargs)  # bottom
    _hold(analyzer, 120, 8, **form_kwargs)  # ascending
    _hold(analyzer, 160, 8, **form_kwargs)  # up / complete


def test_pushup_analyzer_initial_state():
    analyzer = PushupAnalyzer()
    assert analyzer.state == "up"
    assert analyzer.rep_count == 0
    assert analyzer.valid_reps == 0
    assert analyzer.invalid_reps == 0
    assert analyzer.rep_in_progress is False
    assert analyzer.reached_bottom is False
    assert analyzer.movement_direction == "unknown"
    assert analyzer.form_errors["back_bending"] == 0


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
    assert analyzer.state == "up"
    assert "Elbow angle not detected" in analyzer.feedback


def test_low_confidence_does_not_change_state_or_counters():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 5)
    before_state = analyzer.state
    before_reps = analyzer.rep_count
    analyzer.analyze_frame(_a(90), pose_confidence=0.2)
    assert analyzer.state == before_state
    assert analyzer.rep_count == before_reps
    assert analyzer.invalid_reps == 0
    assert "Low pose confidence" in analyzer.feedback
    assert analyzer.form_errors["low_confidence"] >= 1


def test_pushup_analyzer_complete_rep():
    analyzer = PushupAnalyzer()
    _full_rep(analyzer)
    assert analyzer.rep_count == 1
    assert analyzer.valid_reps == 1
    assert analyzer.invalid_reps == 0
    result = analyzer.get_result()
    assert result["exercise"] == "pushup"
    assert result["rep_count"] == 1
    assert result["valid_reps"] == 1


def test_two_full_reps():
    analyzer = PushupAnalyzer()
    _full_rep(analyzer)
    _full_rep(analyzer)
    assert analyzer.rep_count == 2
    assert analyzer.valid_reps == 2
    assert analyzer.invalid_reps == 0


def test_incomplete_without_bottom_counts_one_invalid():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)  # enter descending
    assert analyzer.state == "descending"
    assert analyzer.rep_in_progress is True
    _hold(analyzer, 160, 10)  # return up without bottom
    assert analyzer.state == "up"
    assert analyzer.rep_count == 0
    assert analyzer.valid_reps == 0
    assert analyzer.invalid_reps == 1
    assert analyzer.form_errors["not_low_enough"] == 1
    assert any("Go lower to complete the push-up" in m for m in analyzer.feedback)


def test_threshold_noise_does_not_create_reps():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 5)
    noise = [157, 154, 156, 153, 155, 157, 154]
    for value in noise * 4:
        analyzer.analyze_frame(_a(value))
    assert analyzer.rep_count == 0
    assert analyzer.valid_reps == 0
    assert analyzer.state == "up"


def test_single_spike_does_not_create_bottom_or_rep():
    analyzer = PushupAnalyzer()
    for value in [165, 165, 90, 165, 165]:
        analyzer.analyze_frame(_a(value))
    assert analyzer.rep_count == 0
    assert analyzer.state != "bottom"
    assert analyzer.reached_bottom is False


def test_skipping_state_order_does_not_create_valid_rep():
    analyzer = PushupAnalyzer()
    # Stay near top / noisy — never complete full cycle.
    _hold(analyzer, 165, 5)
    _hold(analyzer, 160, 10)
    assert analyzer.rep_count == 0
    assert analyzer.valid_reps == 0


def test_finalize_after_bottom_without_up_one_invalid():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    _hold(analyzer, 80, 8)
    assert analyzer.state == "bottom"
    assert analyzer.reached_bottom is True
    analyzer.finalize_session()
    assert analyzer.invalid_reps == 1
    assert analyzer.rep_count == 0
    assert any(
        "Complete the upward phase of the push-up" in m for m in analyzer.feedback
    )


def test_finalize_mid_descent_without_bottom_one_invalid():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.state == "descending"
    analyzer.finalize_session()
    assert analyzer.invalid_reps == 1
    assert analyzer.rep_count == 0
    assert analyzer.form_errors["not_low_enough"] == 1
    assert any("Go lower to complete the push-up" in m for m in analyzer.feedback)


def test_finalize_session_is_idempotent():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    analyzer.finalize_session()
    first = analyzer.invalid_reps
    analyzer.finalize_session()
    assert analyzer.invalid_reps == first == 1


def test_get_result_is_idempotent_for_counters():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    r1 = analyzer.get_result()
    r2 = analyzer.get_result()
    assert r1["invalid_reps"] == r2["invalid_reps"] == 1
    assert r1["rep_count"] == r2["rep_count"] == 0


def test_low_confidence_does_not_cancel_in_progress_rep():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.rep_in_progress is True
    assert analyzer.state == "descending"
    for _ in range(4):
        analyzer.analyze_frame(_a(80), pose_confidence=0.1)
    assert analyzer.rep_in_progress is True
    assert analyzer.state == "descending"
    # Continue and complete the rep after confidence recovers.
    _hold(analyzer, 80, 8)
    _hold(analyzer, 120, 8)
    _hold(analyzer, 160, 8)
    assert analyzer.rep_count == 1
    assert analyzer.valid_reps == 1


def test_none_angle_does_not_complete_or_cancel_in_progress_rep():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.rep_in_progress is True
    for _ in range(4):
        analyzer.analyze_frame(
            {"avg_elbow": None, "avg_shoulder": 80, "avg_hip": 170}
        )
    assert analyzer.rep_in_progress is True
    assert analyzer.state == "descending"
    assert analyzer.rep_count == 0
    _hold(analyzer, 80, 8)
    _hold(analyzer, 120, 8)
    _hold(analyzer, 160, 8)
    assert analyzer.rep_count == 1


def test_minimum_elbow_angle_tracks_lowest_smoothed():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.rep_in_progress is True
    _hold(analyzer, 88, 5)
    _hold(analyzer, 70, 5)
    assert analyzer.minimum_elbow_angle is not None
    assert analyzer.minimum_elbow_angle <= 88


def test_hysteresis_prevents_rapid_state_flicker():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    _hold(analyzer, 80, 8)
    assert analyzer.state == "bottom"
    # Oscillate near bottom/ascent boundary without lasting confirm.
    flicker = [100, 108, 100, 107, 99, 106, 100]
    states = []
    for value in flicker:
        analyzer.analyze_frame(_a(value))
        states.append(analyzer.state)
    # Should not bounce up to ascending then immediately leave every frame.
    assert states.count("ascending") < len(flicker)
    assert analyzer.rep_count == 0


def test_non_numeric_elbow_does_not_crash():
    analyzer = PushupAnalyzer()
    analyzer.analyze_frame(
        {"avg_elbow": "bad", "avg_shoulder": 80, "avg_hip": 170}
    )
    assert analyzer.state == "up"
    assert analyzer.rep_count == 0
    assert "Elbow angle not detected" in analyzer.feedback


def test_snapshot_includes_new_fields():
    analyzer = PushupAnalyzer()
    snap = analyzer.analyze_frame(_a(165))
    for key in (
        "rep_in_progress",
        "reached_bottom",
        "movement_direction",
        "minimum_elbow_angle",
        "smoothed_avg_elbow",
        "current_state",
        "state",
        "current_form_state",
        "body_alignment_angle",
        "body_line_offset",
        "alignment_side",
        "current_rep_form_errors",
    ):
        assert key in snap
    assert "raw_avg_elbow" in snap["angles"]
    assert "smoothed_avg_elbow" in snap["angles"]
    assert "hips_sagging" in snap["current_rep_form_errors"]


# ---- Body-line form error tests ----


def test_form_needs_three_frames_to_confirm_sag():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)  # enter descending / rep_in_progress
    assert analyzer.rep_in_progress is True
    # Reset candidate so the next three sag frames are a clean confirmation window.
    analyzer.candidate_form_state = None
    analyzer.candidate_form_frames = 0
    analyzer.current_form_state = "unknown"
    analyzer.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    analyzer.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    assert analyzer.current_form_state != "hips_sagging"
    assert analyzer.current_rep_hips_sagging is False
    analyzer.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    assert analyzer.current_form_state == "hips_sagging"
    assert analyzer.current_rep_hips_sagging is True
    # Not committed to session counters until rep ends.
    assert analyzer.form_errors["hips_not_aligned"] == 0


def test_single_noisy_sag_frame_does_not_confirm():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.rep_in_progress is True
    analyzer.candidate_form_state = None
    analyzer.candidate_form_frames = 0
    analyzer.current_form_state = "unknown"
    analyzer.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    _hold(analyzer, 125, 3, body_line_offset=0.01, body_alignment_angle=175)
    assert analyzer.current_form_state == "aligned"
    assert analyzer.current_rep_hips_sagging is False
    assert analyzer.form_errors["hips_not_aligned"] == 0


def test_aligned_frames_reset_candidate_error():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.rep_in_progress is True
    analyzer.candidate_form_state = None
    analyzer.candidate_form_frames = 0
    analyzer.current_form_state = "unknown"
    analyzer.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    analyzer.analyze_frame(_a(120, body_line_offset=0.09, body_alignment_angle=150))
    assert analyzer.candidate_form_frames == 2
    analyzer.analyze_frame(_a(120, body_line_offset=0.01, body_alignment_angle=175))
    assert analyzer.candidate_form_state is None
    assert analyzer.candidate_form_frames == 0
    assert analyzer.current_form_state == "aligned"


def test_hips_sagging_counted_once_per_rep():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.current_form_state == "hips_sagging"
    # Many more sag frames in the same rep.
    _hold(analyzer, 80, 20, body_line_offset=0.09, body_alignment_angle=150)
    _hold(analyzer, 120, 8, body_line_offset=0.09, body_alignment_angle=150)
    _hold(analyzer, 160, 8, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.rep_count == 1
    assert analyzer.valid_reps == 1
    assert analyzer.form_errors["hips_not_aligned"] == 1


def test_hips_too_high_counted_once_per_rep():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8, body_line_offset=-0.09, body_alignment_angle=150)
    _hold(analyzer, 80, 8, body_line_offset=-0.09, body_alignment_angle=150)
    _hold(analyzer, 120, 8, body_line_offset=-0.09, body_alignment_angle=150)
    _hold(analyzer, 160, 8, body_line_offset=-0.09, body_alignment_angle=150)
    assert analyzer.rep_count == 1
    assert analyzer.form_errors["hips_too_high"] == 1
    assert analyzer.form_errors["hips_not_aligned"] == 0


def test_back_bent_counted_once_per_rep():
    analyzer = PushupAnalyzer()
    # Offset inside sag/high thresholds but angle bent.
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8, body_line_offset=0.0, body_alignment_angle=150)
    _hold(analyzer, 80, 8, body_line_offset=0.0, body_alignment_angle=150)
    _hold(analyzer, 120, 8, body_line_offset=0.0, body_alignment_angle=150)
    _hold(analyzer, 160, 8, body_line_offset=0.0, body_alignment_angle=150)
    assert analyzer.rep_count == 1
    assert analyzer.form_errors["back_bending"] == 1


def test_sag_across_two_reps_counts_twice():
    analyzer = PushupAnalyzer()
    _full_rep(analyzer, body_line_offset=0.09, body_alignment_angle=150)
    _full_rep(analyzer, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.rep_count == 2
    assert analyzer.form_errors["hips_not_aligned"] == 2


def test_unknown_metrics_do_not_cancel_in_progress_rep():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8)
    assert analyzer.rep_in_progress is True
    before = analyzer.state
    for _ in range(5):
        analyzer.analyze_frame(
            _a(
                120,
                body_alignment_angle=None,
                body_line_offset=None,
                alignment_side="unknown",
            )
        )
    assert analyzer.rep_in_progress is True
    assert analyzer.state == before or analyzer.state in {
        "descending",
        "bottom",
        "ascending",
    }
    assert analyzer.form_errors["hips_not_aligned"] == 0


def test_low_confidence_does_not_create_form_error():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 4)
    before = dict(analyzer.form_errors)
    for _ in range(5):
        analyzer.analyze_frame(
            _a(120, body_line_offset=0.09, body_alignment_angle=150),
            pose_confidence=0.1,
        )
    assert analyzer.current_rep_hips_sagging is False
    assert analyzer.form_errors["hips_not_aligned"] == before["hips_not_aligned"]
    assert analyzer.form_errors["low_confidence"] >= 5


def test_form_error_full_rep_still_valid():
    analyzer = PushupAnalyzer()
    _full_rep(analyzer, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.rep_count == 1
    assert analyzer.valid_reps == 1
    assert analyzer.invalid_reps == 0
    assert analyzer.form_errors["hips_not_aligned"] == 1


def test_form_error_half_rep_keeps_invalid_logic():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8, body_line_offset=0.09, body_alignment_angle=150)
    _hold(analyzer, 160, 10, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.rep_count == 0
    assert analyzer.invalid_reps == 1
    assert analyzer.form_errors["not_low_enough"] == 1
    assert analyzer.form_errors["hips_not_aligned"] == 1


def test_finalize_commits_form_error_once():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.current_rep_hips_sagging is True
    analyzer.finalize_session()
    assert analyzer.form_errors["hips_not_aligned"] == 1
    analyzer.finalize_session()
    assert analyzer.form_errors["hips_not_aligned"] == 1


def test_get_result_form_errors_idempotent():
    analyzer = PushupAnalyzer()
    _hold(analyzer, 165, 6)
    _hold(analyzer, 125, 8, body_line_offset=0.09, body_alignment_angle=150)
    r1 = analyzer.get_result()
    r2 = analyzer.get_result()
    assert r1["form_errors"] == r2["form_errors"]
    assert r1["form_errors"]["hips_not_aligned"] == 1
    assert "back_bending" in r1["form_errors"]
    assert "current_form_state" in r1
    assert "body_line_offset" in r1


def test_form_flags_do_not_carry_to_next_rep():
    analyzer = PushupAnalyzer()
    _full_rep(analyzer, body_line_offset=0.09, body_alignment_angle=150)
    assert analyzer.form_errors["hips_not_aligned"] == 1
    assert analyzer.current_rep_hips_sagging is False
    # Next clean rep should not inherit flags.
    _full_rep(analyzer, body_line_offset=0.01, body_alignment_angle=175)
    assert analyzer.rep_count == 2
    assert analyzer.form_errors["hips_not_aligned"] == 1
    assert analyzer.current_rep_hips_sagging is False
