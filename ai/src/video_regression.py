"""Expected-vs-actual video analysis comparison (Week 3 Task 7).

Test/report helpers only — does not alter analyzer algorithms or the
schema 1.0 production JSON contract. Expected values must come from
verified fixtures / existing assertions, never from live actual output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from analysis_response import (
    ANALYSIS_SCHEMA_VERSION,
    ANALYSIS_KEYS,
    FEEDBACK_KEYS,
    REPS_KEYS,
    SCORE_KEYS,
    TOP_LEVEL_KEYS,
)


class MismatchKind(str, Enum):
    """Classification codes for expected vs actual comparison (test-only)."""

    REP_COUNT_MISMATCH = "REP_COUNT_MISMATCH"
    SUCCESS_CLASSIFICATION_MISMATCH = "SUCCESS_CLASSIFICATION_MISMATCH"
    FAILURE_CLASSIFICATION_MISMATCH = "FAILURE_CLASSIFICATION_MISMATCH"
    SCORE_MISMATCH = "SCORE_MISMATCH"
    FEEDBACK_MISMATCH = "FEEDBACK_MISMATCH"
    FORM_ERROR_MISMATCH = "FORM_ERROR_MISMATCH"
    CONTRACT_MISMATCH = "CONTRACT_MISMATCH"
    VIDEO_READ_FAILURE = "VIDEO_READ_FAILURE"
    POSE_DETECTION_FAILURE = "POSE_DETECTION_FAILURE"
    EXPECTED_RESULT_MISSING = "EXPECTED_RESULT_MISSING"
    REP_INVARIANT_VIOLATION = "REP_INVARIANT_VIOLATION"
    ANALYSIS_ERROR = "ANALYSIS_ERROR"


class ComparisonStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    EXPECTED_RESULT_NOT_DEFINED = "EXPECTED_RESULT_NOT_DEFINED"
    VIDEO_MISSING = "VIDEO_MISSING"
    VIDEO_UNREADABLE = "VIDEO_UNREADABLE"


@dataclass(frozen=True)
class ExpectedReps:
    """Verified expected rep counters. Missing fields stay None (not compared)."""

    total: int | None = None
    successful: int | None = None
    failed: int | None = None


@dataclass
class FieldMismatch:
    kind: MismatchKind
    field: str
    expected: Any
    actual: Any


@dataclass
class ComparisonResult:
    status: ComparisonStatus
    mismatches: list[FieldMismatch] = field(default_factory=list)
    invariant_ok: bool | None = None
    contract_ok: bool | None = None
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.status == ComparisonStatus.PASS


def extract_reps_from_ai_result(ai_result: Mapping[str, Any] | None) -> dict[str, int]:
    """Read schema 1.0 ``reps``; fall back to legacy ``rep_count`` if present."""
    ai = ai_result or {}
    reps = ai.get("reps")
    if isinstance(reps, Mapping):
        successful = int(reps.get("successful") or 0)
        failed = int(reps.get("failed") or 0)
        total = int(reps.get("total") or 0)
        return {"successful": successful, "failed": failed, "total": total}

    legacy = ai.get("rep_count")
    if legacy is not None:
        count = int(legacy or 0)
        return {"successful": count, "failed": 0, "total": count}

    return {"successful": 0, "failed": 0, "total": 0}


def validate_rep_invariant(reps: Mapping[str, Any]) -> bool:
    try:
        total = int(reps.get("total") or 0)
        successful = int(reps.get("successful") or 0)
        failed = int(reps.get("failed") or 0)
    except (TypeError, ValueError):
        return False
    return total == successful + failed and total >= 0 and successful >= 0 and failed >= 0


def validate_final_json_contract(ai_result: Any) -> list[FieldMismatch]:
    """Validate schema 1.0 top-level shape (test-only; does not mutate payload)."""
    mismatches: list[FieldMismatch] = []
    if not isinstance(ai_result, Mapping):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "ai_result",
                "object",
                type(ai_result).__name__,
            )
        )
        return mismatches

    if set(ai_result.keys()) != set(TOP_LEVEL_KEYS):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "top_level_keys",
                list(TOP_LEVEL_KEYS),
                sorted(ai_result.keys()),
            )
        )

    if ai_result.get("schema_version") != ANALYSIS_SCHEMA_VERSION:
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "schema_version",
                ANALYSIS_SCHEMA_VERSION,
                ai_result.get("schema_version"),
            )
        )

    if ai_result.get("exercise_type") not in {"squat", "pushup"}:
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "exercise_type",
                "squat|pushup",
                ai_result.get("exercise_type"),
            )
        )

    analysis = ai_result.get("analysis")
    if not isinstance(analysis, Mapping) or set(analysis.keys()) != set(ANALYSIS_KEYS):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "analysis.keys",
                list(ANALYSIS_KEYS),
                sorted(analysis.keys()) if isinstance(analysis, Mapping) else type(analysis).__name__,
            )
        )

    reps = ai_result.get("reps")
    if not isinstance(reps, Mapping) or set(reps.keys()) != set(REPS_KEYS):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "reps.keys",
                list(REPS_KEYS),
                sorted(reps.keys()) if isinstance(reps, Mapping) else type(reps).__name__,
            )
        )
    elif not validate_rep_invariant(reps):
        mismatches.append(
            FieldMismatch(
                MismatchKind.REP_INVARIANT_VIOLATION,
                "reps.invariant",
                "total == successful + failed",
                dict(reps),
            )
        )

    score = ai_result.get("score")
    if not isinstance(score, Mapping) or set(score.keys()) != set(SCORE_KEYS):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "score.keys",
                list(SCORE_KEYS),
                sorted(score.keys()) if isinstance(score, Mapping) else type(score).__name__,
            )
        )
    elif not isinstance(score.get("overall"), int):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "score.overall",
                "int",
                type(score.get("overall")).__name__,
            )
        )

    feedback = ai_result.get("feedback")
    if not isinstance(feedback, Mapping) or set(feedback.keys()) != set(FEEDBACK_KEYS):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "feedback.keys",
                list(FEEDBACK_KEYS),
                sorted(feedback.keys())
                if isinstance(feedback, Mapping)
                else type(feedback).__name__,
            )
        )

    warnings = ai_result.get("warnings")
    if not isinstance(warnings, list):
        mismatches.append(
            FieldMismatch(
                MismatchKind.CONTRACT_MISMATCH,
                "warnings",
                "list",
                type(warnings).__name__,
            )
        )

    return mismatches


def parse_expected_reps(entry: Mapping[str, Any]) -> ExpectedReps | None:
    """Build ExpectedReps from a manifest entry.

    Supports:
      - expected_reps: int  → total only (legacy squat manifest)
      - expected_successful / expected_failed / expected_total
      - expected_reps: {successful, failed, total}

    Returns None when no verified expectation is defined.
    """
    nested = entry.get("expected_reps")
    successful = entry.get("expected_successful")
    failed = entry.get("expected_failed")
    total = entry.get("expected_total")

    if isinstance(nested, Mapping):
        successful = nested.get("successful", successful)
        failed = nested.get("failed", failed)
        total = nested.get("total", total)
    elif isinstance(nested, int):
        # Legacy: only total (and historically treated as overall attempt count).
        if total is None:
            total = nested

    if successful is None and failed is None and total is None:
        return None

    def _opt_int(value: Any) -> int | None:
        if value is None:
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"Expected rep field must be int or null, got {value!r}")
        return value

    return ExpectedReps(
        total=_opt_int(total),
        successful=_opt_int(successful),
        failed=_opt_int(failed),
    )


def compare_expected_vs_actual(
    *,
    expected: ExpectedReps | None,
    actual_reps: Mapping[str, Any] | None,
    actual_ai_result: Mapping[str, Any] | None = None,
    expected_score_overall: int | None = None,
    expected_feedback_codes: Sequence[str] | None = None,
    require_contract: bool = True,
) -> ComparisonResult:
    """Compare verified expectations to an analysis payload."""
    mismatches: list[FieldMismatch] = []
    expectation_defined = not (
        expected is None
        and expected_score_overall is None
        and expected_feedback_codes is None
    )

    contract_mismatches: list[FieldMismatch] = []
    if require_contract and actual_ai_result is not None:
        contract_mismatches = validate_final_json_contract(actual_ai_result)
        mismatches.extend(contract_mismatches)

    reps = (
        extract_reps_from_ai_result(actual_ai_result)
        if actual_ai_result is not None
        else {
            "successful": int((actual_reps or {}).get("successful") or 0),
            "failed": int((actual_reps or {}).get("failed") or 0),
            "total": int((actual_reps or {}).get("total") or 0),
        }
    )
    invariant_ok = validate_rep_invariant(reps)
    if not invariant_ok:
        mismatches.append(
            FieldMismatch(
                MismatchKind.REP_INVARIANT_VIOLATION,
                "reps.invariant",
                "total == successful + failed",
                dict(reps),
            )
        )

    if not expectation_defined:
        # Still report contract/invariant problems, but do not invent PASS/FAIL
        # against missing ground truth.
        hard = [
            m
            for m in mismatches
            if m.kind
            in {
                MismatchKind.CONTRACT_MISMATCH,
                MismatchKind.REP_INVARIANT_VIOLATION,
            }
        ]
        if hard:
            return ComparisonResult(
                status=ComparisonStatus.FAIL,
                mismatches=hard,
                invariant_ok=invariant_ok,
                contract_ok=len(contract_mismatches) == 0 if require_contract else None,
                notes="Expected result missing; contract/invariant failed.",
            )
        return ComparisonResult(
            status=ComparisonStatus.EXPECTED_RESULT_NOT_DEFINED,
            mismatches=[
                FieldMismatch(
                    MismatchKind.EXPECTED_RESULT_MISSING,
                    "expected",
                    "verified expectation",
                    None,
                )
            ],
            invariant_ok=invariant_ok,
            contract_ok=len(contract_mismatches) == 0 if require_contract else None,
            notes="No verified expected result defined for this case.",
        )

    if expected is not None:
        if expected.total is not None and int(reps["total"]) != expected.total:
            mismatches.append(
                FieldMismatch(
                    MismatchKind.REP_COUNT_MISMATCH,
                    "reps.total",
                    expected.total,
                    reps["total"],
                )
            )
        if expected.successful is not None and int(reps["successful"]) != expected.successful:
            mismatches.append(
                FieldMismatch(
                    MismatchKind.SUCCESS_CLASSIFICATION_MISMATCH,
                    "reps.successful",
                    expected.successful,
                    reps["successful"],
                )
            )
        if expected.failed is not None and int(reps["failed"]) != expected.failed:
            mismatches.append(
                FieldMismatch(
                    MismatchKind.FAILURE_CLASSIFICATION_MISMATCH,
                    "reps.failed",
                    expected.failed,
                    reps["failed"],
                )
            )

    if expected_score_overall is not None:
        score = (actual_ai_result or {}).get("score") if actual_ai_result else None
        overall = score.get("overall") if isinstance(score, Mapping) else None
        if overall != expected_score_overall:
            mismatches.append(
                FieldMismatch(
                    MismatchKind.SCORE_MISMATCH,
                    "score.overall",
                    expected_score_overall,
                    overall,
                )
            )

    if expected_feedback_codes is not None:
        feedback = (actual_ai_result or {}).get("feedback") if actual_ai_result else None
        codes: list[str] = []
        if isinstance(feedback, Mapping):
            for item in feedback.get("all") or []:
                if isinstance(item, Mapping) and item.get("code") is not None:
                    codes.append(str(item["code"]))
        if list(expected_feedback_codes) != codes:
            mismatches.append(
                FieldMismatch(
                    MismatchKind.FEEDBACK_MISMATCH,
                    "feedback.all.codes",
                    list(expected_feedback_codes),
                    codes,
                )
            )

    contract_ok = len(contract_mismatches) == 0 if require_contract else None
    if mismatches:
        return ComparisonResult(
            status=ComparisonStatus.FAIL,
            mismatches=mismatches,
            invariant_ok=invariant_ok,
            contract_ok=contract_ok,
        )
    return ComparisonResult(
        status=ComparisonStatus.PASS,
        mismatches=[],
        invariant_ok=invariant_ok,
        contract_ok=contract_ok,
    )


def _resolve_manifest_path(manifest_path: Path) -> Path:
    return manifest_path.expanduser().resolve()


def _resolve_video_path(manifest_path: Path, video_path: str) -> Path:
    raw = Path(video_path)
    if raw.is_absolute():
        return raw.resolve()
    return (manifest_path.parent / raw).resolve()


def load_video_regression_manifest(manifest_path: str | Path) -> list[dict[str, Any]]:
    """Load a video regression manifest (squat or push-up)."""
    resolved = _resolve_manifest_path(Path(manifest_path))
    if not resolved.is_file():
        raise FileNotFoundError(f"Video regression manifest not found: {resolved}")

    with open(resolved, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Manifest root must be an object")
    videos = data.get("videos", [])
    if videos is None:
        videos = []
    if not isinstance(videos, list):
        raise ValueError("Manifest 'videos' must be an array")

    for i, entry in enumerate(videos):
        if not isinstance(entry, dict):
            raise ValueError(f"videos[{i}] must be an object")
        if not entry.get("id") or not isinstance(entry["id"], str):
            raise ValueError(f"videos[{i}] missing string id")
        if not entry.get("path") or not isinstance(entry["path"], str):
            raise ValueError(f"videos[{i}] missing string path")
        exercise = entry.get("exercise_type")
        if exercise is not None and exercise not in {"squat", "pushup"}:
            raise ValueError(f"videos[{i}] invalid exercise_type: {exercise!r}")
        # Validate expected fields parse cleanly.
        parse_expected_reps(entry)
    return videos


def run_video_regression_case(
    entry: Mapping[str, Any],
    *,
    manifest_path: Path,
    run_analysis: Callable[..., dict[str, Any]] | None = None,
    default_exercise_type: str = "squat",
) -> dict[str, Any]:
    """Run one manifest case and return a structured comparison row."""
    video_id = str(entry["id"])
    exercise_type = str(entry.get("exercise_type") or default_exercise_type)
    video_path = _resolve_video_path(manifest_path, str(entry["path"]))
    expected = parse_expected_reps(entry)
    expected_score = entry.get("expected_score_overall")
    if expected_score is not None and not isinstance(expected_score, int):
        raise ValueError(f"{video_id}: expected_score_overall must be int or null")
    expected_feedback_codes = entry.get("expected_feedback_codes")

    row: dict[str, Any] = {
        "id": video_id,
        "path": str(video_path),
        "exercise_type": exercise_type,
        "expected": {
            "total": expected.total if expected else None,
            "successful": expected.successful if expected else None,
            "failed": expected.failed if expected else None,
            "score_overall": expected_score,
            "feedback_codes": expected_feedback_codes,
        },
        "actual": {
            "total": None,
            "successful": None,
            "failed": None,
            "score_overall": None,
            "feedback_codes": None,
        },
        "status": ComparisonStatus.VIDEO_MISSING.value,
        "mismatches": [],
        "invariant_ok": None,
        "contract_ok": None,
        "notes": entry.get("notes") or "",
        "analysis_error": None,
        "metrics": {},
    }

    if not video_path.is_file():
        row["status"] = ComparisonStatus.VIDEO_MISSING.value
        row["mismatches"] = [
            {
                "kind": MismatchKind.VIDEO_READ_FAILURE.value,
                "field": "video_path",
                "expected": "existing file",
                "actual": str(video_path),
            }
        ]
        row["notes"] = f"Video file not found: {video_path}"
        return row

    if run_analysis is None:
        from video_processor import run_video_analysis

        run_analysis = run_video_analysis

    try:
        result = run_analysis(
            video_path=str(video_path),
            exercise_type=exercise_type,
            show_preview=False,
            write_json=False,
        )
    except Exception as exc:  # noqa: BLE001 - regression must capture failures
        row["status"] = ComparisonStatus.VIDEO_UNREADABLE.value
        row["analysis_error"] = f"{type(exc).__name__}: {exc}"
        row["mismatches"] = [
            {
                "kind": MismatchKind.ANALYSIS_ERROR.value,
                "field": "analysis",
                "expected": "completed",
                "actual": row["analysis_error"],
            }
        ]
        return row

    ai = result.get("ai_result") or {}
    metrics = result.get("metrics") or {}
    reps = extract_reps_from_ai_result(ai)
    score = ai.get("score") if isinstance(ai, Mapping) else None
    feedback = ai.get("feedback") if isinstance(ai, Mapping) else None
    codes: list[str] = []
    if isinstance(feedback, Mapping):
        for item in feedback.get("all") or []:
            if isinstance(item, Mapping) and item.get("code") is not None:
                codes.append(str(item["code"]))

    row["actual"] = {
        "total": reps["total"],
        "successful": reps["successful"],
        "failed": reps["failed"],
        "score_overall": score.get("overall") if isinstance(score, Mapping) else None,
        "feedback_codes": codes,
    }
    row["metrics"] = {
        "fps": metrics.get("fps"),
        "total_frames": metrics.get("total_frames"),
        "processed_frames": metrics.get("processed_frames"),
        "duration_seconds": metrics.get("duration_seconds"),
        "landmark_frames": metrics.get("landmark_frames"),
    }

    comparison = compare_expected_vs_actual(
        expected=expected,
        actual_reps=reps,
        actual_ai_result=ai if isinstance(ai, Mapping) else None,
        expected_score_overall=expected_score,
        expected_feedback_codes=expected_feedback_codes,
        require_contract=True,
    )
    row["status"] = comparison.status.value
    row["invariant_ok"] = comparison.invariant_ok
    row["contract_ok"] = comparison.contract_ok
    row["mismatches"] = [
        {
            "kind": m.kind.value,
            "field": m.field,
            "expected": m.expected,
            "actual": m.actual,
        }
        for m in comparison.mismatches
    ]
    if comparison.notes:
        row["notes"] = comparison.notes
    return row


def summarize_regression_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate pass/fail rates excluding undefined expectations."""
    total = len(rows)
    passed = sum(1 for r in rows if r.get("status") == ComparisonStatus.PASS.value)
    failed = sum(1 for r in rows if r.get("status") == ComparisonStatus.FAIL.value)
    missing_expected = sum(
        1
        for r in rows
        if r.get("status") == ComparisonStatus.EXPECTED_RESULT_NOT_DEFINED.value
    )
    video_missing = sum(
        1 for r in rows if r.get("status") == ComparisonStatus.VIDEO_MISSING.value
    )
    unreadable = sum(
        1 for r in rows if r.get("status") == ComparisonStatus.VIDEO_UNREADABLE.value
    )

    defined = [
        r
        for r in rows
        if r.get("status")
        in {
            ComparisonStatus.PASS.value,
            ComparisonStatus.FAIL.value,
        }
    ]
    defined_pass = sum(1 for r in defined if r.get("status") == ComparisonStatus.PASS.value)
    pass_rate = (
        round(100.0 * defined_pass / len(defined), 2) if defined else None
    )

    def _rate_for(exercise: str) -> float | None:
        subset = [
            r
            for r in rows
            if r.get("exercise_type") == exercise
            and r.get("status")
            in {ComparisonStatus.PASS.value, ComparisonStatus.FAIL.value}
        ]
        if not subset:
            return None
        ok = sum(1 for r in subset if r.get("status") == ComparisonStatus.PASS.value)
        return round(100.0 * ok / len(subset), 2)

    return {
        "total_cases": total,
        "passed": passed,
        "failed": failed,
        "expected_result_missing": missing_expected,
        "video_missing": video_missing,
        "video_unreadable": unreadable,
        "cases_with_defined_expectation": len(defined),
        "pass_rate": pass_rate,
        "squat_pass_rate": _rate_for("squat"),
        "pushup_pass_rate": _rate_for("pushup"),
    }


def run_video_regression_manifest(
    manifest_path: str | Path,
    *,
    run_analysis: Callable[..., dict[str, Any]] | None = None,
    default_exercise_type: str = "squat",
) -> dict[str, Any]:
    """Evaluate all entries in a regression manifest."""
    resolved = _resolve_manifest_path(Path(manifest_path))
    entries = load_video_regression_manifest(resolved)
    rows = [
        run_video_regression_case(
            entry,
            manifest_path=resolved,
            run_analysis=run_analysis,
            default_exercise_type=default_exercise_type,
        )
        for entry in entries
    ]
    return {
        "manifest_path": str(resolved),
        "results": rows,
        "summary": summarize_regression_rows(rows),
    }


def format_regression_table(rows: Sequence[Mapping[str, Any]]) -> str:
    """Human-readable table for CLI / reports."""
    header = (
        f"{'VIDEO':<28} {'EX':<7} {'E_TOT':<6} {'A_TOT':<6} "
        f"{'E_SUC':<6} {'A_SUC':<6} {'E_FAIL':<6} {'A_FAIL':<6} "
        f"{'SCORE':<8} {'STATUS':<24}"
    )
    lines = [header, "-" * len(header)]
    for row in rows:
        exp = row.get("expected") or {}
        act = row.get("actual") or {}

        def _cell(value: Any) -> str:
            return "N/A" if value is None else str(value)

        score_match = "N/A"
        if exp.get("score_overall") is not None:
            score_match = "YES" if exp.get("score_overall") == act.get("score_overall") else "NO"

        lines.append(
            f"{str(row.get('id', '')):<28} "
            f"{str(row.get('exercise_type', '')):<7} "
            f"{_cell(exp.get('total')):<6} {_cell(act.get('total')):<6} "
            f"{_cell(exp.get('successful')):<6} {_cell(act.get('successful')):<6} "
            f"{_cell(exp.get('failed')):<6} {_cell(act.get('failed')):<6} "
            f"{score_match:<8} "
            f"{str(row.get('status', '')):<24}"
        )
    return "\n".join(lines)
