"""MediaPipe Tasks PoseLandmarker wrapper and landmark adapters."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import vision as mp_vision
from mediapipe.tasks.python.core import base_options as mp_base_options
from mediapipe.tasks.python.vision import pose_landmarker as mp_pose_landmarker

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "pose_landmarker_full.task"


@dataclass
class NormalizedLandmarkPoint:
    """Landmark point compatible with angle_utils (.x/.y/.z/.visibility)."""

    x: float
    y: float
    z: float
    visibility: float


@dataclass
class LandmarkListAdapter:
    """Adapter matching MediaPipe Legacy pose_landmarks.landmark access."""

    landmark: list[NormalizedLandmarkPoint]


@dataclass
class PoseDetectionResult:
    landmarks: LandmarkListAdapter | None
    world_landmarks: list[Any] | None
    pose_detected: bool


def resolve_pose_model_path(model_path: str | Path | None = None) -> Path:
    """Resolve model path: explicit → env → default full model."""
    if model_path is not None:
        return Path(model_path).expanduser().resolve()

    env_path = os.environ.get("AIT_POSE_MODEL_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()

    return DEFAULT_MODEL_PATH.resolve()


def _landmark_visibility(raw: Any) -> float:
    """Prefer visibility; fall back to presence for Tasks landmarks."""
    vis = getattr(raw, "visibility", None)
    if vis is not None:
        try:
            return float(vis)
        except (TypeError, ValueError):
            pass
    presence = getattr(raw, "presence", None)
    if presence is not None:
        try:
            return float(presence)
        except (TypeError, ValueError):
            pass
    return 0.0


def adapt_pose_landmarks(raw_landmarks: list[Any] | None) -> LandmarkListAdapter | None:
    """Convert Tasks landmark list into Legacy-compatible adapter."""
    if not raw_landmarks:
        return None
    adapted: list[NormalizedLandmarkPoint] = []
    for raw in raw_landmarks:
        adapted.append(
            NormalizedLandmarkPoint(
                x=float(getattr(raw, "x", 0.0)),
                y=float(getattr(raw, "y", 0.0)),
                z=float(getattr(raw, "z", 0.0)),
                visibility=_landmark_visibility(raw),
            )
        )
    return LandmarkListAdapter(landmark=adapted)


class PoseDetector:
    """Wraps MediaPipe Tasks PoseLandmarker (VIDEO mode)."""

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        num_poses: int = 1,
    ) -> None:
        resolved = resolve_pose_model_path(model_path)
        if not resolved.is_file():
            raise FileNotFoundError(
                f"Pose Landmarker model file not found: {resolved}. "
                "Run scripts/download_pose_model.py first."
            )

        self.model_path = resolved
        options = mp_pose_landmarker.PoseLandmarkerOptions(
            base_options=mp_base_options.BaseOptions(
                model_asset_path=str(resolved),
                delegate=mp_base_options.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp_vision.RunningMode.VIDEO,
            num_poses=num_poses,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = (
            mp_pose_landmarker.PoseLandmarker.create_from_options(options)
        )
        self._closed = False

    def process_frame(
        self,
        bgr_frame: Any,
        timestamp_ms: int,
    ) -> PoseDetectionResult:
        if self._closed:
            raise RuntimeError("PoseDetector is closed")

        if bgr_frame is None:
            return PoseDetectionResult(
                landmarks=None,
                world_landmarks=None,
                pose_detected=False,
            )

        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        if not rgb.flags["C_CONTIGUOUS"]:
            rgb = np.ascontiguousarray(rgb)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, int(timestamp_ms))

        pose_list = getattr(result, "pose_landmarks", None) or []
        world_list = getattr(result, "pose_world_landmarks", None) or []

        if not pose_list:
            return PoseDetectionResult(
                landmarks=None,
                world_landmarks=None,
                pose_detected=False,
            )

        landmarks = adapt_pose_landmarks(pose_list[0])
        world = list(world_list[0]) if world_list else None
        return PoseDetectionResult(
            landmarks=landmarks,
            world_landmarks=world,
            pose_detected=landmarks is not None,
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        closer = getattr(self._landmarker, "close", None)
        if callable(closer):
            closer()

    def __enter__(self) -> "PoseDetector":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
