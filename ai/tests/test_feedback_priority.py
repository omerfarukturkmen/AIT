"""Unit tests for shared feedback priority infrastructure."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from camera_utils import CAMERA_FEEDBACK_MESSAGES  # noqa: E402
from feedback_priority import (  # noqa: E402
    DEFAULT_UNKNOWN_IMPORTANCE,
    FEEDBACK_IMPORTANCE,
    FeedbackCode,
    FeedbackItem,
    IMPORTANCE_MAX,
    IMPORTANCE_MIN,
    build_feedback_items,
    build_feedback_payload,
    feedback_item_from_message,
    importance_for_code,
    make_feedback_item,
    messages_from_items,
    sort_feedback_items,
)
from pushup_analyzer import (  # noqa: E402
    FORM_CONFIRMATION_FRAMES,
    FORM_MSG_HIPS_SAGGING,
    PushupAnalyzer,
)
from squat_analyzer import ERROR_MESSAGES, SquatAnalyzer  # noqa: E402
from visibility_utils import VISIBILITY_WARNING  # noqa: E402


def test_feedback_item_fields():
    item = make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN)
    assert item.code == FeedbackCode.SQUAT_TORSO_LEAN
    assert item.message == ERROR_MESSAGES["torso_lean"]
    assert isinstance(item.importance, int)
    assert item.as_dict() == {
        "code": item.code,
        "message": item.message,
        "importance": item.importance,
        "severity": item.severity.value,
    }


def test_importance_within_0_100_for_all_mapped_codes():
    for code, importance in FEEDBACK_IMPORTANCE.items():
        assert IMPORTANCE_MIN <= importance <= IMPORTANCE_MAX
        item = make_feedback_item(code)
        assert IMPORTANCE_MIN <= item.importance <= IMPORTANCE_MAX


def test_invalid_importance_rejected():
    with pytest.raises(ValueError):
        FeedbackItem(code="X", message="x", importance=-1)
    with pytest.raises(ValueError):
        FeedbackItem(code="X", message="x", importance=101)
    with pytest.raises(ValueError):
        make_feedback_item(FeedbackCode.SQUAT_READY, importance=-5)
    with pytest.raises(ValueError):
        make_feedback_item(FeedbackCode.SQUAT_READY, importance=150)


def test_known_code_importance_mapping():
    assert importance_for_code("insufficient_depth") == FEEDBACK_IMPORTANCE[
        FeedbackCode.SQUAT_INSUFFICIENT_DEPTH
    ]
    assert importance_for_code("hips_sagging") == FEEDBACK_IMPORTANCE[
        FeedbackCode.PUSHUP_HIPS_SAGGING
    ]
    assert importance_for_code(FeedbackCode.LOW_VISIBILITY) == 95


def test_unknown_code_does_not_get_high_importance():
    unknown = importance_for_code("TOTALLY_UNKNOWN_FEEDBACK_XYZ")
    assert unknown == DEFAULT_UNKNOWN_IMPORTANCE
    assert unknown < FEEDBACK_IMPORTANCE[FeedbackCode.LOW_VISIBILITY]
    item = make_feedback_item("TOTALLY_UNKNOWN_FEEDBACK_XYZ", message="weird")
    assert item.importance == DEFAULT_UNKNOWN_IMPORTANCE


def test_sorting_higher_importance_first():
    low = make_feedback_item(FeedbackCode.SQUAT_READY)
    high = make_feedback_item(FeedbackCode.LOW_VISIBILITY)
    ordered = sort_feedback_items([low, high])
    assert ordered[0].code == FeedbackCode.LOW_VISIBILITY
    assert ordered[1].code == FeedbackCode.SQUAT_READY


def test_same_importance_ordering_is_deterministic():
    # Force equal importance via explicit override for tie-break test.
    a = make_feedback_item(FeedbackCode.SQUAT_TOO_FAST, importance=70)
    b = make_feedback_item(FeedbackCode.PUSHUP_ELBOWS_FLARED, importance=70)
    first = sort_feedback_items([a, b])
    second = sort_feedback_items([b, a])
    assert [i.code for i in first] == [i.code for i in second]
    assert first[0].code < first[1].code  # alphabetical code tie-break


def test_squat_feedback_messages_unchanged():
    for key, message in ERROR_MESSAGES.items():
        item = make_feedback_item(key)
        assert item.message == message


def test_pushup_hip_sag_message_unchanged():
    item = make_feedback_item("hips_sagging")
    assert item.message == FORM_MSG_HIPS_SAGGING


def test_low_visibility_importance_not_below_form_suggestion():
    visibility = importance_for_code(FeedbackCode.LOW_VISIBILITY)
    ready = importance_for_code(FeedbackCode.SQUAT_READY)
    good = importance_for_code(FeedbackCode.PUSHUP_GOOD_FORM)
    torso = importance_for_code(FeedbackCode.SQUAT_TORSO_LEAN)
    assert visibility > ready
    assert visibility > good
    assert visibility >= torso


def test_camera_invalid_structured_item():
    close = make_feedback_item("too_close")
    far = make_feedback_item(FeedbackCode.CAMERA_TOO_FAR)
    assert close.code == FeedbackCode.CAMERA_TOO_CLOSE
    assert close.message == CAMERA_FEEDBACK_MESSAGES["too_close"]
    assert close.importance == FEEDBACK_IMPORTANCE[FeedbackCode.CAMERA_TOO_CLOSE]
    assert far.message == CAMERA_FEEDBACK_MESSAGES["too_far"]
    assert IMPORTANCE_MIN <= far.importance <= IMPORTANCE_MAX


def test_legacy_message_list_from_structured_items():
    items = build_feedback_items(
        codes=["torso_lean", "too_close"],
        messages=[VISIBILITY_WARNING],
        sort=True,
    )
    legacy = messages_from_items(items)
    assert legacy == [item.message for item in items]
    assert VISIBILITY_WARNING in legacy
    payload = build_feedback_payload(codes=["incomplete_rep"])
    assert payload["feedback"] == [ERROR_MESSAGES["incomplete_rep"]]
    assert payload["feedback_items"][0]["code"] == FeedbackCode.SQUAT_INCOMPLETE_REP


def test_message_reverse_lookup():
    item = feedback_item_from_message(VISIBILITY_WARNING)
    assert item.code == FeedbackCode.LOW_VISIBILITY
    unknown = feedback_item_from_message("completely custom text")
    assert unknown.code == "UNKNOWN_FEEDBACK"
    assert unknown.importance == DEFAULT_UNKNOWN_IMPORTANCE


def _squat_metrics(knee: float, hip: float, torso: float = 15.0) -> dict:
    return {
        "left": knee,
        "right": knee,
        "average": knee,
        "avg_knee": knee,
        "left_hip": hip,
        "right_hip": hip,
        "avg_hip": hip,
        "selected_hip": hip,
        "torso_lean": torso,
        "selected_side": "right",
    }


def test_squat_analyzer_feedback_behavior_preserved():
    a = SquatAnalyzer(fps=30)

    def _feed(angle: float, n: int, torso: float = 15.0) -> None:
        hip = angle if angle >= 155 else max(75.0, angle - 5.0)
        for _ in range(n):
            a.analyze_frame(
                _squat_metrics(angle, hip, torso),
                pose_confidence=0.9,
                torso_lean=torso,
                fps=30.0,
            )

    _feed(165, 10)
    _feed(125, 8)
    _feed(80, 10)
    _feed(120, 8)
    _feed(165, 10)
    a.finalize_session()
    public_before = list(a._session_feedback)
    items = a.get_feedback_items()
    public_after = list(a._session_feedback)
    assert public_before == public_after
    assert isinstance(a.feedback, list)
    assert all(isinstance(m, str) for m in a._session_feedback)
    assert all("code" in i and "message" in i and "importance" in i for i in items)


def test_pushup_analyzer_feedback_behavior_preserved():
    a = PushupAnalyzer()

    def _a(elbow: float, **kwargs) -> dict:
        base = {
            "avg_elbow": elbow,
            "avg_shoulder": 80.0,
            "avg_hip": 170.0,
            "body_alignment_angle": 175.0,
            "body_line_offset": 0.01,
            "alignment_side": "left",
        }
        base.update(kwargs)
        return base

    for _ in range(6):
        a.analyze_frame(_a(165))
    for _ in range(8):
        a.analyze_frame(_a(125, body_line_offset=0.08, body_alignment_angle=150.0))
    for _ in range(FORM_CONFIRMATION_FRAMES):
        a.analyze_frame(_a(80, body_line_offset=0.08, body_alignment_angle=150.0))
    for _ in range(8):
        a.analyze_frame(_a(120, body_line_offset=0.08, body_alignment_angle=150.0))
    for _ in range(8):
        a.analyze_frame(_a(160))
    a.finalize_session()

    public = list(a.feedback)
    items = a.get_feedback_items()
    assert a.feedback == public
    assert all(isinstance(m, str) for m in public)
    if FORM_MSG_HIPS_SAGGING in (a._session_feedback or public):
        codes = {i["code"] for i in items}
        assert FeedbackCode.PUSHUP_HIPS_SAGGING in codes
