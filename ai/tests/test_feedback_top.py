"""Unit tests for top-N feedback selection."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from feedback_priority import (  # noqa: E402
    DEFAULT_TOP_FEEDBACK_LIMIT,
    FeedbackCode,
    FeedbackItem,
    FeedbackSeverity,
    POSITIVE_FEEDBACK_CODES,
    build_feedback_payload,
    make_feedback_item,
    select_top_feedback,
)
from pushup_analyzer import FORM_MSG_HIPS_SAGGING, PushupAnalyzer  # noqa: E402
from squat_analyzer import ERROR_MESSAGES, SquatAnalyzer  # noqa: E402
from visibility_utils import VISIBILITY_WARNING  # noqa: E402


def _fi(code: str, importance: int, message: str | None = None) -> FeedbackItem:
    return FeedbackItem(
        code=code,
        message=message or code,
        importance=importance,
    )


def test_empty_list_returns_empty():
    assert select_top_feedback([]) == []


def test_single_feedback_returned():
    item = _fi("A", 80)
    assert select_top_feedback([item]) == [item]


def test_two_feedback_sorted_by_importance():
    low = _fi("LOW", 40)
    high = _fi("HIGH", 90)
    out = select_top_feedback([low, high])
    assert [i.code for i in out] == ["HIGH", "LOW"]


def test_exactly_three_feedback_sorted():
    items = [_fi("A", 50), _fi("B", 90), _fi("C", 70)]
    out = select_top_feedback(items)
    assert [i.importance for i in out] == [90, 70, 50]
    assert len(out) == 3


def test_five_unique_returns_top_three_100_90_70():
    items = [
        _fi("A", 10),
        _fi("B", 90),
        _fi("C", 50),
        _fi("D", 100),
        _fi("E", 70),
    ]
    out = select_top_feedback(items)
    assert [i.importance for i in out] == [100, 90, 70]
    assert [i.code for i in out] == ["D", "B", "E"]


def test_unsorted_input_is_ordered():
    items = [_fi("C", 70), _fi("A", 100), _fi("B", 90), _fi("D", 40)]
    out = select_top_feedback(items, limit=3)
    assert [i.code for i in out] == ["A", "B", "C"]


def test_duplicates_do_not_fill_top_slots():
    items = [
        _fi("SAME", 95),
        _fi("SAME", 95),
        _fi("SAME", 95),
        _fi("OTHER", 70),
        _fi("THIRD", 60),
    ]
    out = select_top_feedback(items)
    codes = [i.code for i in out]
    assert codes.count("SAME") == 1
    assert len(out) == 3


def test_same_code_ten_times_appears_once_in_top():
    items = [_fi("DUP", 88)] * 10 + [_fi("B", 70), _fi("C", 60)]
    out = select_top_feedback(items)
    assert [i.code for i in out] == ["DUP", "B", "C"]


def test_mixed_severity_orders_by_importance():
    critical = make_feedback_item(FeedbackCode.LOW_VISIBILITY)
    medium = make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN)
    suggestion_tech = _fi("TECH_TIP", 40)
    out = select_top_feedback([suggestion_tech, medium, critical])
    assert out[0].severity == FeedbackSeverity.CRITICAL
    assert out[1].severity == FeedbackSeverity.MEDIUM
    assert out[2].severity == FeedbackSeverity.SUGGESTION


def test_three_critical_two_medium_picks_highest_three():
    items = [
        _fi("C1", 95),
        _fi("C2", 92),
        _fi("C3", 90),
        _fi("M1", 70),
        _fi("M2", 65),
    ]
    out = select_top_feedback(items)
    assert [i.code for i in out] == ["C1", "C2", "C3"]


def test_one_of_each_severity_all_returned():
    items = [
        _fi("CRIT", 95),
        _fi("MED", 70),
        _fi("SUG", 40),
    ]
    out = select_top_feedback(items)
    assert [i.importance for i in out] == [95, 70, 40]


def test_one_medium_one_suggestion_returns_two():
    out = select_top_feedback([_fi("M", 70), _fi("S", 40)])
    assert len(out) == 2
    assert [i.code for i in out] == ["M", "S"]


def test_camera_feedback_can_enter_top():
    camera = make_feedback_item("too_close")
    low = _fi("MINOR", 30)
    mid = _fi("MID", 55)
    out = select_top_feedback([low, mid, camera])
    assert out[0].code == FeedbackCode.CAMERA_TOO_CLOSE


def test_low_visibility_can_enter_top():
    vis = make_feedback_item(FeedbackCode.LOW_VISIBILITY)
    out = select_top_feedback([_fi("A", 40), _fi("B", 50), vis])
    assert out[0].message == VISIBILITY_WARNING
    assert out[0].code == FeedbackCode.LOW_VISIBILITY


def test_same_importance_tie_break_deterministic():
    items = [_fi("ZZZ", 70), _fi("AAA", 70), _fi("MMM", 70)]
    first = select_top_feedback(items)
    second = select_top_feedback(list(reversed(items)))
    assert [i.code for i in first] == [i.code for i in second]
    assert [i.code for i in first] == ["AAA", "MMM", "ZZZ"]


def test_input_not_mutated():
    items = [_fi("A", 50), _fi("B", 90), _fi("C", 70)]
    before = list(items)
    select_top_feedback(items)
    assert items == before


def test_limit_zero_returns_empty():
    assert select_top_feedback([_fi("A", 90)], limit=0) == []


def test_limit_one_returns_best():
    out = select_top_feedback([_fi("A", 50), _fi("B", 99), _fi("C", 70)], limit=1)
    assert len(out) == 1
    assert out[0].code == "B"


def test_limit_greater_than_count_returns_all():
    items = [_fi("A", 50), _fi("B", 90)]
    out = select_top_feedback(items, limit=10)
    assert len(out) == 2


def test_negative_limit_raises():
    with pytest.raises(ValueError):
        select_top_feedback([_fi("A", 50)], limit=-1)


def test_full_list_preserved_beside_top():
    payload = build_feedback_payload(
        codes=[
            "torso_lean",
            "incomplete_rep",
            "too_fast",
            FeedbackCode.LOW_VISIBILITY,
            "hips_sagging",
        ]
    )
    assert len(payload["feedback_items"]) >= 4
    assert len(payload["top_feedback"]) == DEFAULT_TOP_FEEDBACK_LIMIT
    assert len(payload["feedback_items"]) > len(payload["top_feedback"])
    assert len(payload["feedback"]) == len(payload["feedback_items"])


def test_top_items_keep_structured_fields():
    out = select_top_feedback(
        [
            make_feedback_item(FeedbackCode.LOW_VISIBILITY),
            make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN),
            make_feedback_item("hips_sagging"),
        ]
    )
    for item in out:
        d = item.as_dict()
        assert set(d.keys()) == {"code", "message", "importance", "severity"}
        assert isinstance(d["code"], str)
        assert isinstance(d["message"], str)
        assert isinstance(d["importance"], int)
        assert d["severity"] in {"critical", "medium", "suggestion"}


def test_squat_pipeline_top_three():
    a = SquatAnalyzer(fps=30)
    a.errors = [
        "torso_lean",
        "incomplete_rep",
        "too_fast",
        "hip_flexion_mismatch",
        "insufficient_depth",
    ]
    a._session_feedback = [ERROR_MESSAGES[c] for c in a.errors]
    full = a.get_feedback_items()
    top = a.get_top_feedback_items()
    assert len(full) >= 4
    assert len(top) == 3
    assert [i["importance"] for i in top] == sorted(
        (i["importance"] for i in top), reverse=True
    )
    top_codes = {i["code"] for i in top}
    assert (
        FeedbackCode.SQUAT_INCOMPLETE_REP in top_codes
        or FeedbackCode.SQUAT_INSUFFICIENT_DEPTH in top_codes
    )


def test_pushup_pipeline_top_three():
    a = PushupAnalyzer()
    a._session_feedback = [
        FORM_MSG_HIPS_SAGGING,
        FORM_MSG_HIPS_SAGGING,
        "Go lower to complete the push-up",
        "Keep your elbows closer to your body",
        "Keep your back straight",
        "Keep your shoulders stable and aligned",
    ]
    full = a.get_feedback_items()
    top = a.get_top_feedback_items()
    eligible = [i for i in full if i["code"] not in POSITIVE_FEEDBACK_CODES]
    assert len(full) >= 3
    assert len(top) == min(3, len(eligible))
    codes = [i["code"] for i in top]
    assert len(codes) == len(set(codes))


def test_positive_feedback_excluded_from_top_by_default():
    items = [
        make_feedback_item(FeedbackCode.SQUAT_READY),
        make_feedback_item(FeedbackCode.SQUAT_TORSO_LEAN),
        _fi("TECH", 40),
    ]
    out = select_top_feedback(items)
    assert all(i.code != FeedbackCode.SQUAT_READY for i in out)
    assert len(out) == 2


def test_default_limit_is_three():
    assert DEFAULT_TOP_FEEDBACK_LIMIT == 3
