#!/usr/bin/env python3
"""CLI: run squat/push-up expected-vs-actual video regression from manifests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SQUAT = PROJECT_ROOT / "tests" / "fixtures" / "squat_video_manifest.json"
DEFAULT_PUSHUP = PROJECT_ROOT / "tests" / "fixtures" / "pushup_video_manifest.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "output" / "video_regression_report.json"

SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from video_regression import (  # noqa: E402
    format_regression_table,
    run_video_regression_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--squat-manifest",
        type=Path,
        default=DEFAULT_SQUAT,
        help="Squat regression manifest path",
    )
    parser.add_argument(
        "--pushup-manifest",
        type=Path,
        default=DEFAULT_PUSHUP,
        help="Push-up regression manifest path",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Write combined JSON report",
    )
    parser.add_argument(
        "--skip-pushup",
        action="store_true",
        help="Only evaluate squat manifest",
    )
    args = parser.parse_args()

    squat = run_video_regression_manifest(
        args.squat_manifest,
        default_exercise_type="squat",
    )
    print("=== SQUAT ===")
    print(format_regression_table(squat["results"]))
    print("summary:", json.dumps(squat["summary"], ensure_ascii=False))
    print()

    pushup = None
    if not args.skip_pushup:
        pushup = run_video_regression_manifest(
            args.pushup_manifest,
            default_exercise_type="pushup",
        )
        print("=== PUSH-UP ===")
        print(format_regression_table(pushup["results"]))
        print("summary:", json.dumps(pushup["summary"], ensure_ascii=False))
        print()

    report = {
        "squat": squat,
        "pushup": pushup,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {args.output}")

    # Exit non-zero only when a defined-expectation case FAILED.
    failed = int(squat["summary"].get("failed") or 0)
    if pushup is not None:
        failed += int(pushup["summary"].get("failed") or 0)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
