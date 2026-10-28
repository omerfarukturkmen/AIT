"""Unit tests for squat multi-angle evaluation (mocked analysis)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from squat_evaluator import (  # noqa: E402
    evaluate_squat_manifest,
    evaluate_squat_video,
    load_squat_manifest,
)


def _success_result(
    *,
    rep_count: int = 2,
    processed_frames: int = 300,
    total_frames: int = 332,
    visibility: float = 0.87,
    current_state: str = "standing",
) -> dict:
    return {
        "exercise": "squat",
        "ai_result": {
            "rep_count": rep_count,
            "current_state": current_state,
        },
        "metrics": {
            "processed_frames": processed_frames,
            "total_frames": total_frames,
            "mean_landmark_visibility": visibility,
            "ai_confidence": visibility,
            "camera_warnings": [],
            "quality": {
                "low_confidence_frames": 0,
                "camera_too_far_frames": 0,
                "camera_too_close_frames": 0,
                "camera_unknown_frames": 0,
            },
        },
    }


def test_rep_count_match_true_when_equal(tmp_path: Path):
    video = tmp_path / "fake.mp4"
    video.write_bytes(b"x")

    def _run(**kwargs):
        return _success_result(rep_count=2)

    out = evaluate_squat_video(
        video,
        expected_reps=2,
        run_analysis=_run,
    )
    assert out["rep_count_match"] is True


def test_rep_count_match_false_when_different(tmp_path: Path):
    video = tmp_path / "fake.mp4"
    video.write_bytes(b"x")

    def _run(**kwargs):
        return _success_result(rep_count=1)

    out = evaluate_squat_video(
        video,
        expected_reps=2,
        run_analysis=_run,
    )
    assert out["rep_count_match"] is False


def test_rep_count_match_none_when_expected_missing(tmp_path: Path):
    video = tmp_path / "fake.mp4"
    video.write_bytes(b"x")

    def _run(**kwargs):
        return _success_result(rep_count=2)

    out = evaluate_squat_video(
        video,
        expected_reps=None,
        run_analysis=_run,
    )
    assert out["rep_count_match"] is None


def test_zero_processed_frames_not_analyzable(tmp_path: Path):
    video = tmp_path / "fake.mp4"
    video.write_bytes(b"x")

    def _run(**kwargs):
        return _success_result(processed_frames=0, total_frames=100, visibility=0.9)

    out = evaluate_squat_video(video, run_analysis=_run)
    assert out["observed_analyzable"] is False


def test_successful_video_observed_analyzable(tmp_path: Path):
    video = tmp_path / "fake.mp4"
    video.write_bytes(b"x")

    def _run(**kwargs):
        return _success_result()

    out = evaluate_squat_video(video, run_analysis=_run)
    assert out["analysis_completed"] is True
    assert out["observed_analyzable"] is True


def test_run_video_analysis_exception_is_captured(tmp_path: Path):
    video = tmp_path / "fake.mp4"
    video.write_bytes(b"x")

    def _boom(**kwargs):
        raise RuntimeError("analysis failed")

    out = evaluate_squat_video(video, run_analysis=_boom)
    assert out["analysis_completed"] is False
    assert out["analysis_error"] is not None
    assert "RuntimeError" in out["analysis_error"]
    assert out["observed_analyzable"] is False


def test_manifest_groups_by_camera_angle(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "id": "a",
                        "path": "a.mp4",
                        "camera_angle": "front",
                        "expected_reps": 2,
                        "expected_analyzable": True,
                    },
                    {
                        "id": "b",
                        "path": "b.mp4",
                        "camera_angle": "front",
                        "expected_reps": 2,
                        "expected_analyzable": True,
                    },
                    {
                        "id": "c",
                        "path": "c.mp4",
                        "camera_angle": "side",
                        "expected_reps": None,
                        "expected_analyzable": None,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    def _run_tracked(video_path, **kwargs):
        rep = 2 if video_path.endswith("a.mp4") else 1
        return _success_result(rep_count=rep)

    for name in ("a.mp4", "b.mp4", "c.mp4"):
        (tmp_path / name).write_bytes(b"x")

    report = evaluate_squat_manifest(manifest, run_analysis=_run_tracked)
    summary = report["summary"]
    assert summary["total_videos"] == 3
    assert summary["by_camera_angle"]["front"]["video_count"] == 2
    assert summary["by_camera_angle"]["side"]["video_count"] == 1
    assert summary["by_camera_angle"]["front"]["rep_match_known_count"] == 2
    assert summary["by_camera_angle"]["front"]["rep_match_count"] == 1
    assert summary["by_camera_angle"]["side"]["rep_match_known_count"] == 0


def test_null_expected_reps_excluded_from_rep_accuracy(tmp_path: Path):
    # Self-contained: the real sample videos are not in the repository.
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "id": "known",
                        "path": "known.mp4",
                        "exercise_type": "squat",
                        "camera_angle": "unknown",
                        "expected_reps": 2,
                    },
                    {
                        "id": "unknown",
                        "path": "unknown.mp4",
                        "exercise_type": "squat",
                        "camera_angle": "unknown",
                        "expected_reps": None,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    for name in ("known.mp4", "unknown.mp4"):
        (tmp_path / name).write_bytes(b"x")

    report = evaluate_squat_manifest(
        manifest,
        run_analysis=lambda **kwargs: _success_result(rep_count=2),
    )
    known = [
        r for r in report["results"] if r.get("rep_count_match") is not None
    ]
    assert len(known) == 1  # only "known" has expected_reps=2
    assert report["summary"]["rep_accuracy_known_samples"] == 1.0


def test_empty_manifest_is_valid(tmp_path: Path):
    manifest = tmp_path / "empty.json"
    manifest.write_text(json.dumps({"videos": []}), encoding="utf-8")
    report = evaluate_squat_manifest(manifest)
    assert report["results"] == []
    assert report["summary"]["total_videos"] == 0
    assert report["summary"]["rep_accuracy_known_samples"] is None


def test_invalid_camera_angle_raises(tmp_path: Path):
    manifest = tmp_path / "bad.json"
    manifest.write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "id": "x",
                        "path": "x.mp4",
                        "camera_angle": "diagonal",
                        "expected_reps": None,
                        "expected_analyzable": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="invalid camera_angle"):
        load_squat_manifest(manifest)


def test_missing_video_path_produces_clear_error(tmp_path: Path):
    out = evaluate_squat_video(tmp_path / "missing.mp4")
    assert out["analysis_completed"] is False
    assert out["analysis_error"] is not None
    assert "not found" in out["analysis_error"].lower()


def test_manifest_path_resolution_independent_of_cwd(tmp_path: Path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"x")
    manifest.write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "id": "clip1",
                        "path": "clip.mp4",
                        "camera_angle": "unknown",
                        "expected_reps": None,
                        "expected_analyzable": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(ROOT / "src")
    report = evaluate_squat_manifest(
        manifest,
        run_analysis=lambda **kwargs: _success_result(rep_count=0),
    )
    assert report["results"][0]["analysis_completed"] is True
    assert Path(report["results"][0]["video_path"]).name == "clip.mp4"
