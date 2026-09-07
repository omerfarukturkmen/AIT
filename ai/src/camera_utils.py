"""Camera framing / distance evaluation from body bounding-box scale."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# Body scale thresholds (fraction of frame dimension occupied by bbox).
CAMERA_TOO_CLOSE_ENTER = 0.90
CAMERA_TOO_CLOSE_EXIT = 0.85
CAMERA_TOO_FAR_ENTER = 0.30
CAMERA_TOO_FAR_EXIT = 0.35

CAMERA_STATUS_CONFIRMATION_FRAMES = 3
FRAME_EDGE_MARGIN = 0.02

CAMERA_FEEDBACK_MESSAGES: dict[str, str] = {
    "too_close": "Move farther away from the camera so your full body is visible",
    "too_far": "Move closer to the camera so your body is clearly visible",
}

CANONICAL_CAMERA_STATUSES: tuple[str, ...] = ("too_close", "good", "too_far", "unknown")

_DOMINANT_STATUS_ORDER: tuple[str, ...] = ("good", "too_far", "too_close", "unknown")


def compute_body_bbox_metrics(
    body_bbox: tuple[int, int, int, int] | None,
    frame_width: int,
    frame_height: int,
) -> dict[str, Any]:
    """Compute normalized bbox ratios and orientation-invariant body scale."""
    empty: dict[str, Any] = {
        "bbox_width_ratio": None,
        "bbox_height_ratio": None,
        "body_scale": None,
        "min_x_norm": None,
        "max_x_norm": None,
        "min_y_norm": None,
        "max_y_norm": None,
    }
    if body_bbox is None or frame_width <= 0 or frame_height <= 0:
        return empty

    min_x, min_y, max_x, max_y = body_bbox
    bbox_width = max_x - min_x
    bbox_height = max_y - min_y
    if bbox_width <= 0 or bbox_height <= 0:
        return empty

    width_ratio = bbox_width / float(frame_width)
    height_ratio = bbox_height / float(frame_height)
    if not math.isfinite(width_ratio) or not math.isfinite(height_ratio):
        return empty

    body_scale = max(width_ratio, height_ratio)
    if not math.isfinite(body_scale):
        return empty

    return {
        "bbox_width_ratio": width_ratio,
        "bbox_height_ratio": height_ratio,
        "body_scale": body_scale,
        "min_x_norm": min_x / float(frame_width),
        "max_x_norm": max_x / float(frame_width),
        "min_y_norm": min_y / float(frame_height),
        "max_y_norm": max_y / float(frame_height),
    }


def _valid_body_scale(body_scale: float | None) -> bool:
    return body_scale is not None and math.isfinite(body_scale)


def measure_camera_status_with_hysteresis(
    body_scale: float | None,
    confirmed_status: str,
) -> str:
    """Propose next camera status using enter/exit hysteresis."""
    if not _valid_body_scale(body_scale):
        return "unknown"

    scale = float(body_scale)
    current = confirmed_status if confirmed_status in CANONICAL_CAMERA_STATUSES else "unknown"

    if current == "too_close":
        if scale >= CAMERA_TOO_CLOSE_EXIT:
            return "too_close"
        if scale <= CAMERA_TOO_FAR_ENTER:
            return "too_far"
        return "good"

    if current == "too_far":
        if scale <= CAMERA_TOO_FAR_EXIT:
            return "too_far"
        if scale >= CAMERA_TOO_CLOSE_ENTER:
            return "too_close"
        return "good"

    if scale >= CAMERA_TOO_CLOSE_ENTER:
        return "too_close"
    if scale <= CAMERA_TOO_FAR_ENTER:
        return "too_far"
    return "good"


def measure_instant_camera_status(body_scale: float | None) -> str:
    """Single-frame status without hysteresis (for helpers/tests)."""
    return measure_camera_status_with_hysteresis(body_scale, "unknown")


def camera_feedback_for_status(status: str) -> str | None:
    if status in ("too_close", "too_far"):
        return CAMERA_FEEDBACK_MESSAGES.get(status)
    return None


def build_camera_frame_info(
    *,
    status: str,
    metrics: dict[str, Any],
    confirmed: bool,
) -> dict[str, Any]:
    feedback = camera_feedback_for_status(status) if confirmed else None
    return {
        "status": status,
        "body_scale": metrics.get("body_scale"),
        "bbox_width_ratio": metrics.get("bbox_width_ratio"),
        "bbox_height_ratio": metrics.get("bbox_height_ratio"),
        "feedback": feedback,
        "message": feedback or ("Camera distance OK" if status == "good" else "Camera distance unknown"),
        "ratio": metrics.get("bbox_height_ratio"),
        "confirmed": confirmed,
    }


@dataclass
class CameraStatusTracker:
    """Multi-frame confirmed camera framing status for a video session."""

    confirmed_camera_status: str = "unknown"
    candidate_camera_status: str | None = None
    candidate_camera_frames: int = 0
    camera_status_counts: dict[str, int] = field(
        default_factory=lambda: {s: 0 for s in CANONICAL_CAMERA_STATUSES}
    )
    confirmed_too_close_frames: int = 0
    confirmed_too_far_frames: int = 0
    _session_feedback: list[str] = field(default_factory=list)

    def update(
        self,
        body_bbox: tuple[int, int, int, int] | None,
        frame_width: int,
        frame_height: int,
    ) -> dict[str, Any]:
        metrics = compute_body_bbox_metrics(body_bbox, frame_width, frame_height)
        raw_status = measure_camera_status_with_hysteresis(
            metrics.get("body_scale"),
            self.confirmed_camera_status,
        )

        if raw_status == self.candidate_camera_status:
            self.candidate_camera_frames += 1
        else:
            self.candidate_camera_status = raw_status
            self.candidate_camera_frames = 1

        if self.candidate_camera_frames >= CAMERA_STATUS_CONFIRMATION_FRAMES:
            if self.candidate_camera_status != self.confirmed_camera_status:
                self.confirmed_camera_status = self.candidate_camera_status or "unknown"
                msg = camera_feedback_for_status(self.confirmed_camera_status)
                if msg and msg not in self._session_feedback:
                    self._session_feedback.append(msg)

        status = self.confirmed_camera_status
        self.camera_status_counts[status] = self.camera_status_counts.get(status, 0) + 1
        if status == "too_close":
            self.confirmed_too_close_frames += 1
        elif status == "too_far":
            self.confirmed_too_far_frames += 1

        confirmed = (
            self.candidate_camera_frames >= CAMERA_STATUS_CONFIRMATION_FRAMES
            and self.candidate_camera_status == status
        )
        info = build_camera_frame_info(
            status=status,
            metrics=metrics,
            confirmed=confirmed,
        )
        info["raw_status"] = raw_status
        return info

    def session_feedback(self) -> list[str]:
        return list(self._session_feedback)

    def build_summary(self) -> dict[str, Any]:
        counts = dict(self.camera_status_counts)
        dominant = self._dominant_status(counts)
        return {
            "dominant_status": dominant,
            "too_close_frames": self.confirmed_too_close_frames,
            "too_far_frames": self.confirmed_too_far_frames,
            "good_frames": int(counts.get("good") or 0),
            "unknown_frames": int(counts.get("unknown") or 0),
            "camera_status_counts": counts,
        }

    @staticmethod
    def _dominant_status(counts: dict[str, int]) -> str:
        best_status = "unknown"
        best_count = -1
        for status in _DOMINANT_STATUS_ORDER:
            count = int(counts.get(status) or 0)
            if count > best_count:
                best_count = count
                best_status = status
        return best_status
