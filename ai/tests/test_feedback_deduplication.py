"""Unit tests for feedback deduplication by stable feedback code."""

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
    CRITICAL_MIN_IMPORTANCE,
    FEEDBACK_IMPORTANCE,
    FeedbackCode,
    FeedbackItem,
    FeedbackSeverity,
    MEDIUM_MIN_IMPORTANCE,
    build_feedback_items,
    build_feedback_payload,
    deduplicate_feedback,
    make_feedback_item,
    messages_from_items,
    severity_from_importance,
)
from pushup_analyzer import FORM_MSG_HIPS_SAGGING, PushupAnalyzer  # noqa: E402
from squat_analyzer import ERROR_MESSAGES, SquatAnalyzer  # noqa: E402
from visibility_utils import VISIBILITY_WARNING  # noqa: E402


def _item(code: str, *, importance: int | None = None, message: str | None = None) -> FeedbackItem:
    return make_feedback_item(code, importance=importance, message=message)


def test_empty_input_returns_empty():
    assert deduplicate_feedback([]) == []


def test_single_item_unchanged():
    item = _item(FeedbackCode.SQUAT_READY)
    out = deduplicate_feedback([item])
    assert len(out) == 1
    assert out[0] == item


def test_exact_duplicate_collapses_to_one():
    item = _item(FeedbackCode.SQUAT_TORSO_LEAN)
    out = deduplicate_feedback([item, item])
    assert len(out) == 1
    assert out[0].code == FeedbackCode.SQUAT_TORSO_LEAN


def test_ten_duplicates_collapse_to_one():
    item = _item(FeedbackCode.PUSHUP_HIPS_SAGGING)
    out = deduplicate_feedback([item] * 10)
    assert len(out) == 1


def test_same_code_higher_importance_wins():
    low = FeedbackItem(
        code=FeedbackCode.SQUAT_TORSO_LEAN,
        message="low msg",
        importance=40,
    )
    high = FeedbackItem(
        code=FeedbackCode.SQUAT_TORSO_LEAN,
        message="high msg",
        importance=80,
    )
    out = deduplicate_feedback([low, high])
    assert len(out) == 1
    assert out[0].importance == 80
    assert out[0].message == "high msg"


def test_same_code_same_importance_keeps_first():
    first = FeedbackItem(
        code=FeedbackCode.SQUAT_TOO_FAST,
        message="first",
        importance=65,
    )
    second = FeedbackItem(
        code=FeedbackCode.SQUAT_TOO_FAST,
        message="second",
        importance=65,
    )
    out = deduplicate_feedback([first, second], sort=False)
    assert len(out) == 1
    assert out[0].message == "first"


def test_same_code_different_message_keeps_higher_importance_message():
    a = FeedbackItem(code="CUSTOM_X", message="msg-a", importance=55)
    b = FeedbackItem(code="CUSTOM_X", message="msg-b", importance=77)
    out = deduplicate_feedback([a, b])
    assert len(out) == 1
    assert out[0].message == "msg-b"
    assert out[0].importance == 77


def test_different_codes_same_message_both_kept():
    a = FeedbackItem(code="CODE_A", message="Formunu duzelt.", importance=60)
    b = FeedbackItem(code="CODE_B", message="Formunu duzelt.", importance=60)
    out = deduplicate_feedback([a, b], sort=False)
    assert len(out) == 2
    assert {i.code for i in out} == {"CODE_A", "CODE_B"}


def test_different_codes_same_importance_both_kept():
    a = FeedbackItem(
        code=FeedbackCode.SQUAT_TOO_FAST,
        message="fast",
        importance=70,
    )
    b = FeedbackItem(
        code=FeedbackCode.SQUAT_HIP_FLEXION_MISMATCH,
        message="hip",
        importance=70,
    )
    out = deduplicate_feedback([a, b])
    assert len(out) == 2


def test_critical_duplicates_collapse():
    item = _item(FeedbackCode.LOW_VISIBILITY)
    assert item.severity == FeedbackSeverity.CRITICAL
    out = deduplicate_feedback([item, item, item])
    assert len(out) == 1
    assert out[0].severity == FeedbackSeverity.CRITICAL


def test_medium_duplicates_collapse():
    item = _item(FeedbackCode.SQUAT_TORSO_LEAN)
    assert item.severity == FeedbackSeverity.MEDIUM
    out = deduplicate_feedback([item] * 5)
    assert len(out) == 1
    assert out[0].severity == FeedbackSeverity.MEDIUM


def test_suggestion_duplicates_collapse():
    item = _item(FeedbackCode.SQUAT_READY)
    assert item.severity == FeedbackSeverity.SUGGESTION
    out = deduplicate_feedback([item, item])
    assert len(out) == 1
    assert out[0].severity == FeedbackSeverity.SUGGESTION


def test_low_visibility_many_frames_one_item():
    item = _item(FeedbackCode.LOW_VISIBILITY)
    out = deduplicate_feedback([item] * 100)
    assert len(out) == 1
    assert out[0].message == VISIBILITY_WARNING


def test_camera_duplicates_collapse():
    close = _item("too_close")
    out = deduplicate_feedback([close] * 20)
    assert len(out) == 1
    assert out[0].code == FeedbackCode.CAMERA_TOO_CLOSE
    assert out[0].message == CAMERA_FEEDBACK_MESSAGES["too_close"]


def test_squat_form_duplicate_in_build_pipeline():
    items = build_feedback_items(
        codes=["torso_lean", "torso_lean", "torso_lean"],
        sort=True,
    )
    assert len(items) == 1
    assert items[0].code == FeedbackCode.SQUAT_TORSO_LEAN
    assert items[0].message == ERROR_MESSAGES["torso_lean"]


def test_pushup_form_duplicate_in_build_pipeline():
    items = build_feedback_items(
        messages=[FORM_MSG_HIPS_SAGGING, FORM_MSG_HIPS_SAGGING, FORM_MSG_HIPS_SAGGING],
        sort=True,
    )
    assert len(items) == 1
    assert items[0].code == FeedbackCode.PUSHUP_HIPS_SAGGING


def test_dedupe_then_importance_sorting():
    items = [
        FeedbackItem(code="A", message="a", importance=50),
        FeedbackItem(code="B", message="b", importance=90),
        FeedbackItem(code="C", message="c", importance=70),
        FeedbackItem(code="A", message="a2", importance=50),
    ]
    out = deduplicate_feedback(items, sort=True)
    assert [i.importance for i in out] == [90, 70, 50]
    assert [i.code for i in out] == ["B", "C", "A"]


def test_same_importance_tie_break_deterministic():
    a = FeedbackItem(code="ZZZ", message="z", importance=70)
    b = FeedbackItem(code="AAA", message="a", importance=70)
    first = deduplicate_feedback([a, b], sort=True)
    second = deduplicate_feedback([b, a], sort=True)
    assert [i.code for i in first] == [i.code for i in second]
    assert first[0].code < first[1].code


def test_legacy_list_shows_unique_code_messages():
    payload = build_feedback_payload(
        codes=[
            "torso_lean",
            "torso_lean",
            FeedbackCode.LOW_VISIBILITY,
            FeedbackCode.LOW_VISIBILITY,
        ]
    )
    assert payload["feedback"].count(ERROR_MESSAGES["torso_lean"]) == 1
    assert payload["feedback"].count(VISIBILITY_WARNING) == 1
    assert len(payload["feedback_items"]) == 2


def test_different_codes_same_message_kept_in_structured_and_legacy():
    items = deduplicate_feedback(
        [
            FeedbackItem(code="CODE_A", message="Formunu duzelt.", importance=60),
            FeedbackItem(code="CODE_B", message="Formunu duzelt.", importance=55),
        ],
        sort=True,
    )
    assert len(items) == 2
    legacy = messages_from_items(items)
    assert legacy.count("Formunu duzelt.") == 2


def test_severity_mapping_unchanged():
    assert severity_from_importance(CRITICAL_MIN_IMPORTANCE) == FeedbackSeverity.CRITICAL
    assert severity_from_importance(MEDIUM_MIN_IMPORTANCE) == FeedbackSeverity.MEDIUM
    assert severity_from_importance(MEDIUM_MIN_IMPORTANCE - 1) == FeedbackSeverity.SUGGESTION


def test_importance_mapping_unchanged():
    assert FEEDBACK_IMPORTANCE[FeedbackCode.LOW_VISIBILITY] == 95
    assert FEEDBACK_IMPORTANCE[FeedbackCode.SQUAT_TORSO_LEAN] == 75
    assert FEEDBACK_IMPORTANCE[FeedbackCode.PUSHUP_HIPS_SAGGING] == 78


def test_deduplicate_does_not_mutate_input():
    items = [
        _item(FeedbackCode.SQUAT_READY),
        _item(FeedbackCode.SQUAT_READY),
        _item(FeedbackCode.LOW_VISIBILITY),
    ]
    original_len = len(items)
    original_ids = [id(x) for x in items]
    deduplicate_feedback(items)
    assert len(items) == original_len
    assert [id(x) for x in items] == original_ids


def test_analyzer_get_feedback_items_are_unique_by_code():
    a = SquatAnalyzer(fps=30)
    a.errors = ["torso_lean", "torso_lean", "incomplete_rep"]
    a._session_feedback = [
        ERROR_MESSAGES["torso_lean"],
        ERROR_MESSAGES["torso_lean"],
        ERROR_MESSAGES["incomplete_rep"],
    ]
    items = a.get_feedback_items()
    codes = [i["code"] for i in items]
    assert len(codes) == len(set(codes))
    assert FeedbackCode.SQUAT_TORSO_LEAN in codes
    assert FeedbackCode.SQUAT_INCOMPLETE_REP in codes


def test_pushup_analyzer_get_feedback_items_dedupe():
    a = PushupAnalyzer()
    a._session_feedback = [FORM_MSG_HIPS_SAGGING, FORM_MSG_HIPS_SAGGING]
    items = a.get_feedback_items()
    assert len(items) == 1
    assert items[0]["code"] == FeedbackCode.PUSHUP_HIPS_SAGGING
