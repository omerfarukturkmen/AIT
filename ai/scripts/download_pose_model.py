#!/usr/bin/env python3
"""Download MediaPipe Pose Landmarker .task models into ai/models/."""

from __future__ import annotations

import argparse
import sys
import tempfile
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"

MODEL_URLS: dict[str, str] = {
    "lite": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
    ),
    "full": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
    ),
    "heavy": (
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
        "pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task"
    ),
}

MODEL_FILENAMES: dict[str, str] = {
    "lite": "pose_landmarker_lite.task",
    "full": "pose_landmarker_full.task",
    "heavy": "pose_landmarker_heavy.task",
}


def download_pose_model(variant: str = "full", *, force: bool = False) -> Path:
    if variant not in MODEL_URLS:
        raise ValueError(f"Unknown variant: {variant}. Choose lite, full, or heavy.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target = MODELS_DIR / MODEL_FILENAMES[variant]

    if target.is_file() and target.stat().st_size > 0 and not force:
        print(f"Model already present: {target}")
        return target

    url = MODEL_URLS[variant]
    print(f"Downloading {variant} model from:\n  {url}")

    with tempfile.NamedTemporaryFile(
        dir=MODELS_DIR,
        prefix=f".{MODEL_FILENAMES[variant]}.",
        suffix=".partial",
        delete=False,
    ) as tmp:
        tmp_path = Path(tmp.name)

    try:
        urllib.request.urlretrieve(url, tmp_path)
        size = tmp_path.stat().st_size
        if size <= 0:
            raise RuntimeError(f"Downloaded empty file for variant={variant}")
        tmp_path.replace(target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        raise

    print(str(target.resolve()))
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Download MediaPipe Pose Landmarker model (.task)."
    )
    parser.add_argument(
        "--variant",
        choices=("lite", "full", "heavy"),
        default="full",
        help="Model variant (default: full)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the model file already exists",
    )
    args = parser.parse_args(argv)
    download_pose_model(args.variant, force=args.force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
