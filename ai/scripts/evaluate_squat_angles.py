#!/usr/bin/env python3
"""CLI: evaluate squat analysis across camera angles from a manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = (
    PROJECT_ROOT / "tests" / "fixtures" / "squat_video_manifest.json"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "output" / "squat_angle_evaluation.json"

SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from squat_evaluator import evaluate_squat_manifest  # noqa: E402


def _fmt_bool(value: bool | None) -> str:
    if value is None:
        return "-"
    return "YES" if value else "NO"


def _print_table(report: dict) -> None:
    print("Squat Multi-Angle Evaluation")
    print()
    header = (
        f"{'VIDEO':<28} {'ANGLE':<10} {'REPS':<6} {'EXPECTED':<9} "
        f"{'MATCH':<6} {'VISIBILITY':<10} {'ANALYZABLE':<10}"
    )
    print(header)
    print("-" * len(header))

    for item in report.get("results", []):
        rep = item.get("rep_count")
        expected = item.get("expected_reps")
        print(
            f"{str(item.get('video_id', '')):<28} "
            f"{str(item.get('camera_angle', '')):<10} "
            f"{str(rep if rep is not None else '-'):<6} "
            f"{str(expected if expected is not None else '-'):<9} "
            f"{_fmt_bool(item.get('rep_count_match')):<6} "
            f"{item.get('mean_landmark_visibility', 0.0):<10.4f} "
            f"{_fmt_bool(item.get('observed_analyzable')):<10}"
        )
        if item.get("analysis_error"):
            print(f"  error: {item['analysis_error']}")

    print()
    print("Summary:")
    summary = report.get("summary") or {}
    print(f"- total videos: {summary.get('total_videos', 0)}")
    print(f"- analyzed videos: {summary.get('analyzed_videos', 0)}")
    rep_acc = summary.get("rep_accuracy_known_samples")
    if rep_acc is None:
        print("- rep accuracy (known samples): n/a")
    else:
        print(f"- rep accuracy (known samples): {rep_acc:.2%}")

    by_angle = summary.get("by_camera_angle") or {}
    if not by_angle:
        print("- by camera angle: (none)")
        return

    for angle, stats in sorted(by_angle.items()):
        print(
            f"- {angle}: videos={stats.get('video_count', 0)}, "
            f"analysis_success_rate={stats.get('analysis_success_rate', 0.0):.2%}, "
            f"rep_match_rate={stats.get('rep_match_rate', 0.0):.2%}, "
            f"mean_visibility={stats.get('mean_visibility', 0.0):.4f}, "
            f"observed_analyzable={stats.get('observed_analyzable_count', 0)}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate squat analysis across camera angles."
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help=f"Path to squat manifest JSON (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write JSON report",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = (PROJECT_ROOT / manifest_path).resolve()

    report = evaluate_squat_manifest(manifest_path)
    _print_table(report)

    output_path = args.output
    if output_path:
        out = Path(output_path)
        if not out.is_absolute():
            out = (PROJECT_ROOT / out).resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print()
        print(f"JSON report written to: {out}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
