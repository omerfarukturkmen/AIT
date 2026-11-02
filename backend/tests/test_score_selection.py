"""Score selection and push-up error plumbing between ai/src and the API."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
AI_SRC = BACKEND_DIR.parent / "ai" / "src"
for _path in (BACKEND_DIR, AI_SRC):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import ai_analyzer  # noqa: E402
from pushup_analyzer import PushupAnalyzer  # noqa: E402


def _schema(overall, components=None):
    return {"score": {"overall": overall, "components": components or {}}}


def test_finished_reps_use_the_analyzers_own_score():
    domain = {"valid_reps": 3, "invalid_reps": 0, "errors": []}
    components = {"elbow_angle": 95, "body_alignment": 92}
    score, used = ai_analyzer._select_score(domain, _schema(94, components), {})
    assert score == 94
    assert used == components


def test_pushup_is_no_longer_capped_by_squat_depth_formula():
    # Squat-shaped fallback gives a perfect push-up at most ~80.
    domain = {"valid_reps": 5, "invalid_reps": 0, "errors": []}
    metrics = {"landmark_detection_ratio": 1.0, "mean_landmark_visibility": 1.0}
    assert ai_analyzer._compute_score(domain, metrics) <= 81
    score, _ = ai_analyzer._select_score(domain, _schema(97), metrics)
    assert score == 97


def test_no_finished_reps_scores_zero_instead_of_a_misleading_number():
    domain = {"valid_reps": 0, "invalid_reps": 0, "errors": []}
    metrics = {"landmark_detection_ratio": 0.9, "mean_landmark_visibility": 0.9}
    score, _ = ai_analyzer._select_score(domain, _schema(0), metrics)
    assert score == 0


def test_score_is_clamped_and_tolerates_a_missing_schema():
    domain = {"valid_reps": 1, "invalid_reps": 0}
    assert ai_analyzer._select_score(domain, _schema(140), {})[0] == 100
    score, components = ai_analyzer._select_score(domain, {}, {})
    assert 0 <= score <= 100
    assert components == {}


def test_pushup_result_exposes_rep_errors_most_important_first():
    analyzer = PushupAnalyzer()
    analyzer.rep_history = [
        {"rep_index": 1, "valid": True, "errors": ["elbows_flared"]},
        {"rep_index": 2, "valid": False, "errors": ["not_low_enough", "hips_sagging"]},
        {"rep_index": 3, "valid": True, "errors": []},
    ]
    assert analyzer.session_error_codes() == [
        "hips_sagging",
        "elbows_flared",
        "not_low_enough",
    ]


def test_pushup_get_result_contains_errors_and_rep_history():
    result = PushupAnalyzer().get_result()
    assert result["errors"] == []
    assert result["rep_history"] == []


def test_missing_pose_model_is_a_server_error_not_a_bad_video(tmp_path, monkeypatch):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"\x00\x00\x00\x18ftypmp42")

    def _no_model(**_kwargs):
        raise FileNotFoundError(
            "Pose Landmarker model file not found: /x/pose_landmarker_full.task. "
            "Run scripts/download_pose_model.py first."
        )

    monkeypatch.setattr(ai_analyzer, "run_video_analysis", _no_model)
    with pytest.raises(ai_analyzer.AnalysisError) as exc_info:
        ai_analyzer.analyze_video(str(video), "squat")
    assert exc_info.value.status_code == 503


def test_startup_check_reports_a_missing_model(monkeypatch, tmp_path):
    monkeypatch.setenv("AIT_POSE_MODEL_PATH", str(tmp_path / "absent.task"))
    assert ai_analyzer.warn_if_pose_model_missing() is False
    present = tmp_path / "present.task"
    present.write_bytes(b"x")
    monkeypatch.setenv("AIT_POSE_MODEL_PATH", str(present))
    assert ai_analyzer.warn_if_pose_model_missing() is True


def _fake_analysis(domain_extra):
    domain = {"rep_count": 0, "valid_reps": 0, "invalid_reps": 0, "errors": [],
              "feedback": [], "rep_history": []}
    domain.update(domain_extra)
    return {
        "domain_result": domain,
        "ai_result": {"score": {"overall": 0, "components": {}}, "feedback": {"top": []}},
        "metrics": {"total_frames": 30, "landmark_detection_ratio": 0.0},
    }


def _video(tmp_path):
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    return str(video)


def test_video_without_a_visible_person_fails_with_guidance(tmp_path, monkeypatch):
    analysis = _fake_analysis({"analysis_status": "insufficient_landmark_visibility"})
    monkeypatch.setattr(ai_analyzer, "run_video_analysis", lambda **_: analysis)
    with pytest.raises(ai_analyzer.AnalysisError) as exc_info:
        ai_analyzer.analyze_video(_video(tmp_path), "squat")
    assert exc_info.value.status_code == 422
    assert exc_info.value.user_message == ai_analyzer.NO_PERSON_MESSAGE


def test_person_visible_but_no_finished_rep_reports_the_issue(tmp_path, monkeypatch):
    analysis = _fake_analysis({"analysis_status": "completed"})
    monkeypatch.setattr(ai_analyzer, "run_video_analysis", lambda **_: analysis)
    result = ai_analyzer.analyze_video(_video(tmp_path), "pushup")
    assert result["score"] == 0
    assert result["errors"][0] == ai_analyzer.NO_REPS_CODE
