"""Deterministic FPS-aware frame sampling helpers (Week 3 Task 6).

Pure functions only — no MediaPipe, no video I/O. Sampling decisions belong
to the video loop *before* PoseDetector / analyzer work.
"""

from __future__ import annotations

import math

# Conservative target: matches typical phone recording (~24–30 FPS).
# Videos at or below this rate keep frame_step=1 (no accuracy trade-off).
# Higher FPS (e.g. 60) samples down toward this rate.
TARGET_PROCESSING_FPS: float = 30.0


def calculate_frame_step(
    source_fps: float,
    target_fps: float = TARGET_PROCESSING_FPS,
) -> int:
    """Return a positive integer frame stride from source vs target FPS.

    Rules:
      - invalid / non-finite / non-positive FPS → 1 (process every frame)
      - source_fps <= target_fps → 1
      - otherwise → max(1, round(source_fps / target_fps))
    """
    try:
        src = float(source_fps)
    except (TypeError, ValueError):
        return 1
    if not math.isfinite(src) or src <= 0.0:
        return 1

    try:
        tgt = float(target_fps)
    except (TypeError, ValueError):
        tgt = TARGET_PROCESSING_FPS
    if not math.isfinite(tgt) or tgt <= 0.0:
        tgt = TARGET_PROCESSING_FPS

    if src <= tgt:
        return 1

    step = int(round(src / tgt))
    return max(1, step)


def should_process_frame(frame_index: int, frame_step: int) -> bool:
    """True when ``frame_index`` should run pose/analyzer (index 0 always)."""
    step = int(frame_step) if frame_step else 1
    if step < 1:
        step = 1
    idx = int(frame_index)
    if idx < 0:
        return False
    return idx % step == 0


def processing_fps_for_step(
    source_fps: float,
    frame_step: int,
    *,
    fallback_fps: float = TARGET_PROCESSING_FPS,
) -> float:
    """Approximate analyzed-frame rate for analyzer time-based helpers."""
    step = max(1, int(frame_step) if frame_step else 1)
    try:
        src = float(source_fps)
    except (TypeError, ValueError):
        return float(fallback_fps)
    if not math.isfinite(src) or src <= 0.0:
        return float(fallback_fps)
    return src / step
