"""Contract tests for final analysis response schema 1.0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from analysis_response import (  # noqa: E402
    ANALYSIS_KEYS,
    ANALYSIS_SCHEMA_VERSION,
    ANALYSIS_STATUS_COMPLETED,
    ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY,
    FEEDBACK_ITEM_KEYS,
    FEEDBACK_KEYS,
    REPS_KEYS,
    SCORE_KEYS,
    SEVERITY_VALUES,
    TOP_LEVEL_KEYS,
    AnalysisResponse,
    build_analysis_response,
    empty_analysis_response,
    serialize_analysis_response,
)
from feedback_priority import FeedbackSeverity  # noqa: E402
from pushup_analyzer import PushupAnalyzer  # noqa: E402
from pushup_scoring import PUSHUP_SCORE_COMPONENT_KEYS  # noqa: E402
from result_writer import build_result, write_result_json  # noqa: E402
from squat_analyzer import SquatAnalyzer  # noqa: E402
from squat_scoring import SQUAT_SCORE_COMPONENT_KEYS  # noqa: E402


def _assert_contract_shape(payload: dict) -> None:
    assert set(payload.keys()) == set(TOP_LEVEL_KEYS)
    assert set(payload["analysis"].keys()) == set(ANALYSIS_KEYS)
    assert set(payload["reps"].keys()) == set(REPS_KEYS)
    assert set(payload["score"].keys()) == set(SCORE_KEYS)
    assert set(payload["feedback"].keys()) == set(FEEDBACK_KEYS)
    assert isinstance(payload["warnings"], list)


def _assert_feedback_items(items: list) -> None:
    for item in items:
        assert set(item.keys()) == set(FEEDBACK_ITEM_KEYS)
        assert isinstance(item["code"], str)
        assert isinstance(item["message"], str)
        assert isinstance(item["importance"], int)
        assert 0 <= item["importance"] <= 100
        assert item["severity"] in SEVERITY_VALUES
        assert not str(item["severity"]).startswith("FeedbackSeverity")


def _squat_metrics(knee: float, hip: float | None = None, torso: float = 15.0) -> dict:
    if hip is None:
        hip = knee if knee >= 155 else max(75.0, knee - 5.0)
        if knee >= 155:
            hip = max(hip, 155.0)
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


def _feed_squat(a: SquatAnalyzer, angles: list[float], torso: float = 15.0) -> None:
    for angle in angles:
        a.analyze_frame(
            _squat_metrics(angle, torso=torso),
            pose_confidence=0.9,
            torso_lean=torso,
            fps=30.0,
        )


def _full_squat_cycle() -> list[float]:
    return [165] * 10 + [125] * 8 + [80] * 10 + [120] * 8 + [165] * 10


def _pushup_angles(
    elbow: float,
    *,
    body_alignment_angle: float = 175.0,
    body_line_offset: float = 0.01,
) -> dict:
    return {
        "avg_elbow": elbow,
        "avg_shoulder": 80.0,
        "avg_hip": 170.0,
        "body_alignment_angle": body_alignment_angle,
        "body_line_offset": body_line_offset,
        "alignment_side": "left",
    }


def _hold_pushup(a: PushupAnalyzer, elbow: float, frames: int, **kwargs) -> None:
    for _ in range(frames):
        a.analyze_frame(_pushup_angles(elbow, **kwargs))


def _full_pushup(a: PushupAnalyzer, **kwargs) -> None:
    _hold_pushup(a, 165, 6, **kwargs)
    _hold_pushup(a, 125, 8, **kwargs)
    _hold_pushup(a, 80, 8, **kwargs)
    _hold_pushup(a, 120, 8, **kwargs)
    _hold_pushup(a, 160, 8, **kwargs)


def test_top_level_exact_keys():
    payload = empty_analysis_response()
    assert list(payload.keys()) == list(TOP_LEVEL_KEYS)


def test_schema_version_is_1_0():
    assert ANALYSIS_SCHEMA_VERSION == "1.0"
    assert serialize_analysis_response(SquatAnalyzer(fps=30))["schema_version"] == "1.0"


def test_exercise_type_canonical_squat_and_pushup():
    squat = serialize_analysis_response(SquatAnalyzer(fps=30))
    push = serialize_analysis_response(PushupAnalyzer())
    assert squat["exercise_type"] == "squat"
    assert push["exercise_type"] == "pushup"


def test_analysis_exact_keys():
    payload = empty_analysis_response()
    assert set(payload["analysis"].keys()) == set(ANALYSIS_KEYS)


def test_reps_exact_keys_and_invariant():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    payload = serialize_analysis_response(a)
    assert set(payload["reps"].keys()) == set(REPS_KEYS)
    reps = payload["reps"]
    assert reps["total"] == reps["successful"] + reps["failed"]
    assert reps["successful"] >= 0
    assert reps["failed"] >= 0


def test_score_exact_keys_and_ranges():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    payload = serialize_analysis_response(a)
    assert set(payload["score"].keys()) == set(SCORE_KEYS)
    assert isinstance(payload["score"]["overall"], int)
    assert 0 <= payload["score"]["overall"] <= 100
    for key, value in payload["score"]["components"].items():
        assert isinstance(value, int)
        assert 0 <= value <= 100


def test_feedback_exact_keys_and_top_limit():
    payload = empty_analysis_response()
    assert set(payload["feedback"].keys()) == set(FEEDBACK_KEYS)
    assert len(payload["feedback"]["top"]) <= 3


def test_top_codes_subset_of_all():
    a = PushupAnalyzer()
    _full_pushup(a, body_line_offset=0.09, body_alignment_angle=145.0)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    all_codes = {item["code"] for item in payload["feedback"]["all"]}
    for item in payload["feedback"]["top"]:
        assert item["code"] in all_codes


def test_feedback_item_exact_keys_and_severity():
    a = PushupAnalyzer()
    _hold_pushup(a, 165, 6)
    _hold_pushup(a, 125, 8)
    _hold_pushup(a, 160, 8)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    _assert_feedback_items(payload["feedback"]["all"])
    _assert_feedback_items(payload["feedback"]["top"])


def test_feedback_all_unique_codes():
    a = PushupAnalyzer()
    _full_pushup(a, body_line_offset=0.09, body_alignment_angle=145.0)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    codes = [item["code"] for item in payload["feedback"]["all"]]
    assert len(codes) == len(set(codes))


def test_feedback_top_importance_order():
    a = PushupAnalyzer()
    _full_pushup(a, body_line_offset=0.09, body_alignment_angle=145.0)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    importances = [item["importance"] for item in payload["feedback"]["top"]]
    assert importances == sorted(importances, reverse=True)


def test_warnings_always_list():
    payload = serialize_analysis_response(SquatAnalyzer(fps=30), warnings=["x"])
    assert payload["warnings"] == ["x"]
    payload2 = serialize_analysis_response(SquatAnalyzer(fps=30))
    assert payload2["warnings"] == []


def test_no_feedback_empty_lists():
    payload = serialize_analysis_response(SquatAnalyzer(fps=30))
    assert payload["feedback"]["top"] == []
    assert payload["feedback"]["all"] == []


def test_no_reps_zero_contract():
    payload = serialize_analysis_response(PushupAnalyzer())
    assert payload["reps"] == {"successful": 0, "failed": 0, "total": 0}
    assert payload["score"]["overall"] == 0
    _assert_contract_shape(payload)


def test_json_dumps_succeeds():
    payload = serialize_analysis_response(SquatAnalyzer(fps=30))
    raw = json.dumps(payload)
    assert isinstance(raw, str)


def test_json_roundtrip():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    payload = serialize_analysis_response(
        a, frames=10, processed_frames=10, duration_seconds=1.5
    )
    restored = json.loads(json.dumps(payload))
    assert restored == payload


def test_write_result_json_roundtrip(tmp_path: Path):
    payload = serialize_analysis_response(
        PushupAnalyzer(),
        frames=5,
        processed_frames=5,
        duration_seconds=0.5,
    )
    path = write_result_json(tmp_path, payload)
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "1.0"
    assert set(loaded.keys()) == set(TOP_LEVEL_KEYS)


def test_enum_not_leaked_into_json():
    from analysis_response import _normalize_feedback_item

    item = {
        "code": "X",
        "message": "m",
        "importance": 90,
        "severity": FeedbackSeverity.CRITICAL,
    }
    normalized = _normalize_feedback_item(item)
    assert normalized["severity"] == "critical"
    assert json.dumps(normalized)


def test_numpy_numeric_types_coerced():
    np = pytest.importorskip("numpy")
    from analysis_response import ScoreSummary

    summary = ScoreSummary(
        overall=np.float64(84.4),
        components={"depth": np.int64(88), "knee_control": np.float32(82.2)},
    )
    as_dict = summary.as_dict()
    assert type(as_dict["overall"]) is int
    assert type(as_dict["components"]["depth"]) is int
    assert type(as_dict["components"]["knee_control"]) is int
    json.dumps(as_dict)


def test_squat_score_component_keys():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    payload = serialize_analysis_response(a)
    assert set(payload["score"]["components"].keys()) == set(SQUAT_SCORE_COMPONENT_KEYS)


def test_squat_rep_count_domain_unchanged():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle())
    a.finalize_session()
    domain = a.get_result()
    payload = serialize_analysis_response(a)
    assert domain["rep_count"] == domain["valid_reps"] + domain["invalid_reps"]
    assert payload["reps"]["successful"] == domain["successful_reps"]
    assert payload["reps"]["failed"] == domain["failed_reps"]
    assert payload["reps"]["total"] == domain["total_reps"]


def test_squat_feedback_and_score_in_contract():
    a = SquatAnalyzer(fps=30)
    _feed_squat(a, _full_squat_cycle(), torso=40.0)
    a.finalize_session()
    payload = build_result(a, frames=100, processed_frames=100, duration_seconds=3.3)
    _assert_contract_shape(payload)
    assert payload["exercise_type"] == "squat"
    assert isinstance(payload["score"]["overall"], int)
    _assert_feedback_items(payload["feedback"]["all"])


def test_pushup_same_top_level_contract():
    a = PushupAnalyzer()
    _full_pushup(a)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    _assert_contract_shape(payload)
    assert payload["exercise_type"] == "pushup"


def test_pushup_score_component_keys():
    a = PushupAnalyzer()
    _full_pushup(a)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    assert set(payload["score"]["components"].keys()) == set(PUSHUP_SCORE_COMPONENT_KEYS)


def test_pushup_rep_summary_contract():
    a = PushupAnalyzer()
    _full_pushup(a)
    _hold_pushup(a, 165, 6)
    _hold_pushup(a, 125, 8)
    _hold_pushup(a, 160, 8)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    assert payload["reps"]["successful"] == 1
    assert payload["reps"]["failed"] == 1
    assert payload["reps"]["total"] == 2
    assert a.rep_count == 1


def test_pushup_feedback_contract():
    a = PushupAnalyzer()
    _full_pushup(a, body_line_offset=0.09, body_alignment_angle=145.0)
    a.finalize_session()
    payload = serialize_analysis_response(a)
    assert len(payload["feedback"]["top"]) <= 3
    _assert_feedback_items(payload["feedback"]["top"])


def test_low_visibility_status_keeps_shape():
    a = SquatAnalyzer(fps=30)
    payload = serialize_analysis_response(
        a,
        status=ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY,
        extra_feedback_messages=["Landmark visibility dusuk; analiz guvenilir degil."],
    )
    _assert_contract_shape(payload)
    assert payload["analysis"]["status"] == ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY
    json.dumps(payload)


def test_camera_invalid_keeps_shape():
    a = PushupAnalyzer()
    payload = serialize_analysis_response(
        a,
        status=ANALYSIS_STATUS_COMPLETED,
        warnings=["Kamera cok uzakta; daha yakina gelin."],
        extra_feedback_messages=["Kameraya biraz daha yaklas."],
    )
    _assert_contract_shape(payload)
    assert isinstance(payload["warnings"], list)
    assert payload["warnings"]
    json.dumps(payload)


def test_analysis_response_dataclass_as_dict_keys():
    response = AnalysisResponse()
    assert list(response.as_dict().keys()) == list(TOP_LEVEL_KEYS)
    assert response.analysis.status == ANALYSIS_STATUS_COMPLETED
    assert build_analysis_response(SquatAnalyzer(fps=30)).schema_version == "1.0"
