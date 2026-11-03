"""Videos whose result would mislead stop with guidance (task 23 / AIT-027).

Thresholds were checked on IMG_5512 variants: cropped below the knees
(41% usable frames, lost a rep), truncated file, 1 s clip, 8 fps copy.
"""

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
from video_processor import VideoValidationError  # noqa: E402


def _analysis(*, metrics=None, domain=None):
    base_metrics = {
        "total_frames": 330, "reported_frame_count": 332, "fps": 29.97,
        "duration_seconds": 11.0, "landmark_detection_ratio": 1.0,
        "quality": {"usable_landmark_frame_ratio": 1.0},
    }
    base_metrics.update(metrics or {})
    base_domain = {"rep_count": 2, "valid_reps": 2, "invalid_reps": 0,
                   "errors": [], "feedback": [], "rep_history": []}
    base_domain.update(domain or {})
    return {
        "domain_result": base_domain,
        "ai_result": {"score": {"overall": 90, "components": {}}, "feedback": {"top": []}},
        "metrics": base_metrics,
    }


@pytest.fixture
def video(tmp_path):
    path = tmp_path / "clip.mp4"
    path.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    return str(path)


def _run(monkeypatch, video, analysis):
    monkeypatch.setattr(ai_analyzer, "run_video_analysis", lambda **_: analysis)
    return ai_analyzer.analyze_video(video, "squat")


def _stops_with(monkeypatch, video, analysis, message):
    with pytest.raises(ai_analyzer.AnalysisError) as exc_info:
        _run(monkeypatch, video, analysis)
    assert exc_info.value.status_code == 422
    assert exc_info.value.user_message == message


def test_good_video_passes_without_warnings(monkeypatch, video):
    result = _run(monkeypatch, video, _analysis())
    assert result["valid_reps"] == 2
    assert result["camera_warnings"] == []


def test_truncated_file_is_reported_as_unreadable(monkeypatch, video):
    analysis = _analysis(metrics={"total_frames": 18, "duration_seconds": 0.6})
    _stops_with(monkeypatch, video, analysis, ai_analyzer.UNREADABLE_MESSAGE)


def test_unopenable_file_is_reported_as_unreadable(monkeypatch, video):
    def _broken(**_):
        raise VideoValidationError("Video acilamadi")

    monkeypatch.setattr(ai_analyzer, "run_video_analysis", _broken)
    with pytest.raises(ai_analyzer.AnalysisError) as exc_info:
        ai_analyzer.analyze_video(video, "squat")
    assert exc_info.value.user_message == ai_analyzer.UNREADABLE_MESSAGE


def test_very_short_clip_asks_for_a_longer_video(monkeypatch, video):
    analysis = _analysis(metrics={"total_frames": 30, "reported_frame_count": 30,
                                  "duration_seconds": 1.0})
    _stops_with(monkeypatch, video, analysis, ai_analyzer.TOO_SHORT_MESSAGE)


def test_feet_out_of_frame_stops_instead_of_undercounting(monkeypatch, video):
    analysis = _analysis(metrics={"quality": {"usable_landmark_frame_ratio": 0.41}},
                         domain={"rep_count": 1, "valid_reps": 1})
    _stops_with(monkeypatch, video, analysis, ai_analyzer.PARTIAL_BODY_MESSAGE)


def test_mostly_visible_body_analyzes_with_a_warning(monkeypatch, video):
    analysis = _analysis(metrics={"quality": {"usable_landmark_frame_ratio": 0.7}})
    result = _run(monkeypatch, video, analysis)
    assert ai_analyzer.PARTIAL_BODY_WARNING in result["camera_warnings"]


def test_low_frame_rate_still_analyzes_but_warns(monkeypatch, video):
    # An 8 fps copy of IMG_5512 still counted 2/2 reps.
    analysis = _analysis(metrics={"fps": 8.0, "total_frames": 90, "reported_frame_count": 90})
    result = _run(monkeypatch, video, analysis)
    assert result["valid_reps"] == 2
    assert ai_analyzer.LOW_FPS_WARNING in result["camera_warnings"]


def test_unusably_low_frame_rate_stops(monkeypatch, video):
    analysis = _analysis(metrics={"fps": 3.0, "total_frames": 33, "reported_frame_count": 33})
    _stops_with(monkeypatch, video, analysis, ai_analyzer.UNREADABLE_MESSAGE)


@pytest.mark.parametrize(
    ("metrics", "code"),
    [
        ({"total_frames": 18, "duration_seconds": 0.6}, "video_unreadable"),
        ({"total_frames": 30, "reported_frame_count": 30, "duration_seconds": 1.0},
         "video_too_short"),
        ({"quality": {"usable_landmark_frame_ratio": 0.41}}, "body_out_of_frame"),
    ],
)
def test_stops_carry_a_code_the_app_translates(monkeypatch, video, metrics, code):
    with pytest.raises(ai_analyzer.AnalysisError) as exc_info:
        _run(monkeypatch, video, _analysis(metrics=metrics))
    assert exc_info.value.code == code
    assert exc_info.value.user_message == ai_analyzer.FAILURE_MESSAGES[code]


def test_soft_warnings_come_with_codes(monkeypatch, video):
    analysis = _analysis(metrics={
        "fps": 8.0, "total_frames": 90, "reported_frame_count": 90,
        "quality": {"usable_landmark_frame_ratio": 0.7},
        "camera_warning_codes": ["camera_too_far"],
    })
    result = _run(monkeypatch, video, analysis)
    assert result["warning_codes"] == [
        "camera_too_far", "body_partly_out_of_frame", "low_frame_rate",
    ]


def test_good_video_has_no_warning_codes(monkeypatch, video):
    assert _run(monkeypatch, video, _analysis())["warning_codes"] == []
