"""Unit + optional integration tests for video expected-vs-actual regression."""

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

from analysis_response import ANALYSIS_SCHEMA_VERSION, TOP_LEVEL_KEYS  # noqa: E402
from video_regression import (  # noqa: E402
    ComparisonStatus,
    ExpectedReps,
    MismatchKind,
    compare_expected_vs_actual,
    extract_reps_from_ai_result,
    load_video_regression_manifest,
    parse_expected_reps,
    run_video_regression_case,
    run_video_regression_manifest,
    summarize_regression_rows,
    validate_final_json_contract,
    validate_rep_invariant,
)


def _valid_ai(
    *,
    exercise: str = "squat",
    successful: int = 2,
    failed: int = 0,
    score: int = 91,
) -> dict:
    total = successful + failed
    return {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "exercise_type": exercise,
        "analysis": {
            "status": "completed",
            "frames": 332,
            "processed_frames": 332,
            "duration_seconds": 11.08,
        },
        "reps": {
            "successful": successful,
            "failed": failed,
            "total": total,
        },
        "score": {"overall": score, "components": {"depth": 100}},
        "feedback": {"top": [], "all": []},
        "warnings": [],
    }


def test_exact_match_passes():
    ai = _valid_ai()
    result = compare_expected_vs_actual(
        expected=ExpectedReps(total=2, successful=2, failed=0),
        actual_reps=ai["reps"],
        actual_ai_result=ai,
    )
    assert result.status == ComparisonStatus.PASS
    assert result.passed is True
    assert result.invariant_ok is True
    assert result.contract_ok is True


def test_total_rep_mismatch_fails():
    ai = _valid_ai(successful=1, failed=0)
    result = compare_expected_vs_actual(
        expected=ExpectedReps(total=2),
        actual_reps=ai["reps"],
        actual_ai_result=ai,
    )
    assert result.status == ComparisonStatus.FAIL
    assert any(m.kind == MismatchKind.REP_COUNT_MISMATCH for m in result.mismatches)


def test_success_mismatch_fails_even_if_total_matches():
    ai = _valid_ai(successful=1, failed=1)
    result = compare_expected_vs_actual(
        expected=ExpectedReps(total=2, successful=2, failed=0),
        actual_reps=ai["reps"],
        actual_ai_result=ai,
    )
    assert result.status == ComparisonStatus.FAIL
    kinds = {m.kind for m in result.mismatches}
    assert MismatchKind.SUCCESS_CLASSIFICATION_MISMATCH in kinds
    assert MismatchKind.FAILURE_CLASSIFICATION_MISMATCH in kinds


def test_failed_mismatch_fails():
    ai = _valid_ai(successful=2, failed=1)
    result = compare_expected_vs_actual(
        expected=ExpectedReps(failed=0),
        actual_reps=ai["reps"],
        actual_ai_result=ai,
    )
    assert result.status == ComparisonStatus.FAIL
    assert any(
        m.kind == MismatchKind.FAILURE_CLASSIFICATION_MISMATCH for m in result.mismatches
    )


def test_missing_expected_is_explicit_state():
    ai = _valid_ai()
    result = compare_expected_vs_actual(
        expected=None,
        actual_reps=ai["reps"],
        actual_ai_result=ai,
    )
    assert result.status == ComparisonStatus.EXPECTED_RESULT_NOT_DEFINED
    assert any(m.kind == MismatchKind.EXPECTED_RESULT_MISSING for m in result.mismatches)


def test_malformed_contract_fails():
    result = compare_expected_vs_actual(
        expected=ExpectedReps(total=1),
        actual_reps={"successful": 1, "failed": 0, "total": 1},
        actual_ai_result={"schema_version": "9.9"},
    )
    assert result.status == ComparisonStatus.FAIL
    assert any(m.kind == MismatchKind.CONTRACT_MISMATCH for m in result.mismatches)


def test_rep_invariant_helper():
    assert validate_rep_invariant({"successful": 2, "failed": 0, "total": 2})
    assert not validate_rep_invariant({"successful": 2, "failed": 0, "total": 3})


def test_extract_reps_prefers_schema():
    ai = _valid_ai(successful=2, failed=1)
    assert extract_reps_from_ai_result(ai) == {
        "successful": 2,
        "failed": 1,
        "total": 3,
    }
    assert extract_reps_from_ai_result({"rep_count": 4}) == {
        "successful": 4,
        "failed": 0,
        "total": 4,
    }


def test_parse_expected_reps_legacy_and_explicit():
    assert parse_expected_reps({"expected_reps": 2}) == ExpectedReps(total=2)
    assert parse_expected_reps(
        {
            "expected_successful": 2,
            "expected_failed": 0,
            "expected_total": 2,
        }
    ) == ExpectedReps(total=2, successful=2, failed=0)
    assert parse_expected_reps({}) is None


def test_validate_final_json_contract_ok():
    assert validate_final_json_contract(_valid_ai()) == []


def test_missing_video_path_reported(tmp_path: Path):
    manifest = tmp_path / "m.json"
    manifest.write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "id": "missing_case",
                        "path": "does_not_exist.mp4",
                        "exercise_type": "squat",
                        "expected_total": 2,
                        "expected_successful": 2,
                        "expected_failed": 0,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    report = run_video_regression_manifest(manifest)
    row = report["results"][0]
    assert row["status"] == ComparisonStatus.VIDEO_MISSING.value
    assert report["summary"]["video_missing"] == 1


def test_score_mismatch_when_expected_defined():
    ai = _valid_ai(score=80)
    result = compare_expected_vs_actual(
        expected=ExpectedReps(total=2, successful=2, failed=0),
        actual_reps=ai["reps"],
        actual_ai_result=ai,
        expected_score_overall=91,
    )
    assert result.status == ComparisonStatus.FAIL
    assert any(m.kind == MismatchKind.SCORE_MISMATCH for m in result.mismatches)


def test_summarize_excludes_undefined_from_pass_rate():
    rows = [
        {"status": ComparisonStatus.PASS.value, "exercise_type": "squat"},
        {"status": ComparisonStatus.FAIL.value, "exercise_type": "squat"},
        {
            "status": ComparisonStatus.EXPECTED_RESULT_NOT_DEFINED.value,
            "exercise_type": "pushup",
        },
    ]
    summary = summarize_regression_rows(rows)
    assert summary["cases_with_defined_expectation"] == 2
    assert summary["pass_rate"] == 50.0
    assert summary["expected_result_missing"] == 1
    assert summary["squat_pass_rate"] == 50.0
    assert summary["pushup_pass_rate"] is None


def test_load_repo_manifests():
    squat = load_video_regression_manifest(FIXTURES / "squat_video_manifest.json")
    pushup = load_video_regression_manifest(FIXTURES / "pushup_video_manifest.json")
    assert any(e["id"] == "squat_verified_img_5512" for e in squat)
    verified = next(e for e in squat if e["id"] == "squat_verified_img_5512")
    assert parse_expected_reps(verified) == ExpectedReps(
        total=2, successful=2, failed=0
    )
    assert parse_expected_reps(pushup[0]) is None


def test_verified_squat_video_matches_expected():
    """Integration: only IMG_5512 has verified expectations in-repo."""
    video = (
        ROOT.parent
        / "backend"
        / "uploaded_videos"
        / "IMG_5512.mp4"
    )
    if not video.is_file():
        pytest.skip("IMG_5512.mp4 not present")

    entry = {
        "id": "squat_verified_img_5512",
        "path": str(video),
        "exercise_type": "squat",
        "expected_successful": 2,
        "expected_failed": 0,
        "expected_total": 2,
    }
    row = run_video_regression_case(
        entry,
        manifest_path=FIXTURES,
    )
    assert row["status"] == ComparisonStatus.PASS.value
    assert row["actual"]["total"] == 2
    assert row["actual"]["successful"] == 2
    assert row["actual"]["failed"] == 0
    assert row["invariant_ok"] is True
    assert row["contract_ok"] is True
    assert set(row["actual"].keys()) >= {"total", "successful", "failed"}


def test_pushup_manifest_reports_expected_missing_without_inventing():
    manifest = FIXTURES / "pushup_video_manifest.json"
    video = ROOT.parent / "backend" / "uploaded_videos" / "pushup_smoke.mp4"
    if not video.is_file():
        pytest.skip("pushup_smoke.mp4 not present")

    report = run_video_regression_manifest(manifest, default_exercise_type="pushup")
    row = report["results"][0]
    assert row["status"] == ComparisonStatus.EXPECTED_RESULT_NOT_DEFINED.value
    assert report["summary"]["expected_result_missing"] == 1
    assert report["summary"]["pass_rate"] is None
    # Actual may be collected for inventory, but must not become expected.
    assert row["expected"]["total"] is None


def test_full_frame_vs_sampled_same_on_verified_squat():
    """Available verified video is ~30 FPS → sampling step=1; results must match."""
    video = ROOT.parent / "backend" / "uploaded_videos" / "IMG_5512.mp4"
    if not video.is_file():
        pytest.skip("IMG_5512.mp4 not present")

    from video_processor import run_video_analysis

    full = run_video_analysis(
        str(video),
        "squat",
        show_preview=False,
        write_json=False,
        target_processing_fps=10_000.0,  # forces step=1
    )
    sampled = run_video_analysis(
        str(video),
        "squat",
        show_preview=False,
        write_json=False,
        # default TARGET_PROCESSING_FPS=30 → step=1 on this clip
    )
    assert full["ai_result"]["reps"] == sampled["ai_result"]["reps"]
    assert full["ai_result"]["score"]["overall"] == sampled["ai_result"]["score"]["overall"]
    assert set(full["ai_result"].keys()) == set(TOP_LEVEL_KEYS)
