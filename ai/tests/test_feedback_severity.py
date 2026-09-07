"""Unit tests for feedback severity derived from importance."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from feedback_priority import (  # noqa: E402
    CRITICAL_MIN_IMPORTANCE,
    FEEDBACK_IMPORTANCE,
    FeedbackCode,
    FeedbackItem,
    FeedbackSeverity,
    IMPORTANCE_MAX,
    IMPORTANCE_MIN,
    MEDIUM_MIN_IMPORTANCE,
    build_feedback_items,
    make_feedback_item,
    messages_from_items,
    severity_from_importance,
    sort_feedback_items,
)
from squat_analyzer import ERROR_MESSAGES  # noqa: E402
from pushup_analyzer import FORM_MSG_HIPS_SAGGING  # noqa: E402
from visibility_utils import VISIBILITY_WARNING  # noqa: E402
from camera_utils import CAMERA_FEEDBACK_MESSAGES  # noqa: E402


def test_severity_enum_only_three_values():
    assert {s.value for s in FeedbackSeverity} == {
        "critical",
        "medium",
        "suggestion",
    }
    assert FeedbackSeverity.CRITICAL == "critical"
    assert FeedbackSeverity.MEDIUM == "medium"
    assert FeedbackSeverity.SUGGESTION == "suggestion"


def test_high_importance_is_critical():
    assert severity_from_importance(95) == FeedbackSeverity.CRITICAL


def test_mid_importance_is_medium():
    assert severity_from_importance(70) == FeedbackSeverity.MEDIUM


def test_low_importance_is_suggestion():
    assert severity_from_importance(20) == FeedbackSeverity.SUGGESTION


def test_critical_threshold_boundary_inclusive():
    assert (
        severity_from_importance(CRITICAL_MIN_IMPORTANCE)
        == FeedbackSeverity.CRITICAL
    )


def test_just_below_critical_is_medium():
    assert (
        severity_from_importance(CRITICAL_MIN_IMPORTANCE - 1)
        == FeedbackSeverity.MEDIUM
    )


def test_medium_threshold_boundary_inclusive():
    assert (
        severity_from_importance(MEDIUM_MIN_IMPORTANCE) == FeedbackSeverity.MEDIUM
    )


def test_just_below_medium_is_suggestion():
    assert (
        severity_from_importance(MEDIUM_MIN_IMPORTANCE - 1)
        == FeedbackSeverity.SUGGESTION
    )


def test_importance_min_is_suggestion():
    assert severity_from_importance(IMPORTANCE_MIN) == FeedbackSeverity.SUGGESTION


def test_importance_max_is_critical():
    assert severity_from_importance(IMPORTANCE_MAX) == FeedbackSeverity.CRITICAL


def test_invalid_importance_rejected_for_severity():
    with pytest.raises(ValueError):
        severity_from_importance(-1)
    with pytest.raises(ValueError):
        severity_from_importance(101)


def test_feedback_item_exposes_derived_severity():
    item = make_feedback_item(FeedbackCode.LOW_VISIBILITY)
    assert item.severity == FeedbackSeverity.CRITICAL
    assert item.as_dict()["severity"] == "critical"
    medium = make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN)
    assert medium.severity == FeedbackSeverity.MEDIUM
    suggestion = make_feedback_item(FeedbackCode.SQUAT_READY)
    assert suggestion.severity == FeedbackSeverity.SUGGESTION


def test_stable_feedback_codes_unchanged():
    assert FeedbackCode.LOW_VISIBILITY == "LOW_VISIBILITY"
    assert FeedbackCode.PUSHUP_HIPS_SAGGING == "PUSHUP_HIPS_SAGGING"
    assert FeedbackCode.SQUAT_INCOMPLETE_REP == "SQUAT_INCOMPLETE_REP"


def test_existing_message_text_unchanged():
    assert make_feedback_item("torso_lean").message == ERROR_MESSAGES["torso_lean"]
    assert make_feedback_item("hips_sagging").message == FORM_MSG_HIPS_SAGGING
    assert make_feedback_item(FeedbackCode.LOW_VISIBILITY).message == VISIBILITY_WARNING


def test_low_visibility_severity_is_critical():
    item = make_feedback_item(FeedbackCode.LOW_VISIBILITY)
    assert item.importance >= CRITICAL_MIN_IMPORTANCE
    assert item.severity == FeedbackSeverity.CRITICAL


def test_camera_invalid_severity_is_critical():
    close = make_feedback_item("too_close")
    far = make_feedback_item(FeedbackCode.CAMERA_TOO_FAR)
    assert close.message == CAMERA_FEEDBACK_MESSAGES["too_close"]
    assert close.severity == FeedbackSeverity.CRITICAL
    assert far.severity == FeedbackSeverity.CRITICAL


def test_squat_form_feedback_severity_medium():
    item = make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN)
    assert MEDIUM_MIN_IMPORTANCE <= item.importance < CRITICAL_MIN_IMPORTANCE
    assert item.severity == FeedbackSeverity.MEDIUM


def test_pushup_form_feedback_severity_medium():
    item = make_feedback_item("hips_sagging")
    assert MEDIUM_MIN_IMPORTANCE <= item.importance < CRITICAL_MIN_IMPORTANCE
    assert item.severity == FeedbackSeverity.MEDIUM


def test_sorting_unchanged_by_severity_layer():
    items = [
        make_feedback_item(FeedbackCode.SQUAT_READY),
        make_feedback_item(FeedbackCode.LOW_VISIBILITY),
        make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN),
    ]
    ordered = sort_feedback_items(items)
    assert [i.importance for i in ordered] == sorted(
        (i.importance for i in items), reverse=True
    )
    assert ordered[0].code == FeedbackCode.LOW_VISIBILITY
    assert ordered[-1].code == FeedbackCode.SQUAT_READY


def test_legacy_message_list_unchanged():
    items = build_feedback_items(
        codes=["torso_lean", FeedbackCode.LOW_VISIBILITY],
        sort=True,
    )
    legacy = messages_from_items(items)
    assert legacy == [VISIBILITY_WARNING, ERROR_MESSAGES["torso_lean"]]
    assert all(isinstance(m, str) for m in legacy)


def test_incomplete_rep_is_critical():
    squat = make_feedback_item("incomplete_rep")
    pushup = make_feedback_item("not_low_enough")
    assert squat.severity == FeedbackSeverity.CRITICAL
    assert pushup.severity == FeedbackSeverity.CRITICAL


def test_all_mapped_codes_have_consistent_severity():
    for code, importance in FEEDBACK_IMPORTANCE.items():
        item = make_feedback_item(code)
        assert item.severity == severity_from_importance(importance)
        assert item.as_dict()["severity"] == item.severity.value
