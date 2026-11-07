"""Squat-specific 0–100 scoring built on the shared weighted scoring API.

Consumes metrics already produced by SquatAnalyzer (depth score/status, knee/hip
angles, torso lean, validity, form errors). Does not reimplement pose analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from scoring import SCORE_MAX, SCORE_MIN, ScoreBreakdown, calculate_score_breakdown
from squat_analyzer import (
    DEPTH_SCORE_HIP_MAX,
    DEPTH_SCORE_HIP_MIN,
    DEPTH_SCORE_HIP_WEIGHT,
    DEPTH_SCORE_KNEE_MAX,
    DEPTH_SCORE_KNEE_MIN,
    DEPTH_SCORE_KNEE_WEIGHT,
    EXCESSIVE_TORSO_LEAN,
    TOO_DEEP_KNEE_ANGLE,
    TORSO_LEAN_THRESHOLD,
)

# --- Component keys & default weights (must sum to 1.0) ---
SQUAT_SCORE_COMPONENT_DEPTH = "depth"
SQUAT_SCORE_COMPONENT_KNEE_CONTROL = "knee_control"
SQUAT_SCORE_COMPONENT_TORSO_POSTURE = "torso_posture"
SQUAT_SCORE_COMPONENT_REP_QUALITY = "rep_quality"

SQUAT_SCORE_COMPONENT_KEYS: tuple[str, ...] = (
    SQUAT_SCORE_COMPONENT_DEPTH,
    SQUAT_SCORE_COMPONENT_KNEE_CONTROL,
    SQUAT_SCORE_COMPONENT_TORSO_POSTURE,
    SQUAT_SCORE_COMPONENT_REP_QUALITY,
)

SQUAT_SCORE_WEIGHTS: dict[str, float] = {
    SQUAT_SCORE_COMPONENT_DEPTH: 0.35,
    SQUAT_SCORE_COMPONENT_KNEE_CONTROL: 0.25,
    SQUAT_SCORE_COMPONENT_TORSO_POSTURE: 0.20,
    SQUAT_SCORE_COMPONENT_REP_QUALITY: 0.20,
}

# Depth status fallbacks when continuous depth_score is unavailable
_DEPTH_STATUS_SCORES: dict[str, float] = {
    "deep": 95.0,
    "acceptable": 75.0,
    "shallow": 25.0,
    "unknown": 0.0,
    "metrics_incomplete": 0.0,
}

# Knee-control continuous penalty using analyzer TOO_DEEP threshold
_KNEE_TOO_DEEP_BASE_PENALTY = 40.0
_KNEE_TOO_DEEP_PER_DEGREE = 2.0
_KNEE_TOO_FAST_PENALTY = 25.0
_KNEE_TRACKING_PENALTY = 50.0
_KNEE_INSUFFICIENT_PENALTY = 35.0

# Torso posture bands aligned with TORSO_LEAN_THRESHOLD / EXCESSIVE_TORSO_LEAN
_TORSO_EXCELLENT_MAX = 20.0
_TORSO_GOOD_FLOOR = 85.0
_TORSO_THRESHOLD_SCORE = 70.0
_TORSO_EXCESSIVE_SCORE = 35.0
_TORSO_EXCESS_PER_DEGREE = 2.0

# Rep quality
_REP_QUALITY_INVALID_BASE = 30.0
_REP_QUALITY_INCOMPLETE_CAP = 25.0
_REP_QUALITY_DEPTH_ERROR_CAP = 40.0
_REP_QUALITY_FORM_ERROR_PENALTY = 10.0


def _clamp(value: float) -> float:
    return max(SCORE_MIN, min(SCORE_MAX, float(value)))


def _as_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def _linear_depth_component(value: float, high_angle: float, low_angle: float) -> float:
    """Same mapping as SquatAnalyzer._linear_depth_component."""
    if value >= high_angle:
        return 0.0
    if value <= low_angle:
        return 100.0
    span = high_angle - low_angle
    if span <= 0:
        return 0.0
    return (high_angle - value) / span * 100.0


def recompute_depth_score_from_angles(
    min_knee_angle: float | None,
    min_hip_angle: float | None,
) -> float | None:
    """Rebuild continuous depth score with analyzer depth constants."""
    if min_knee_angle is None or min_hip_angle is None:
        return None
    knee_part = _linear_depth_component(
        float(min_knee_angle), DEPTH_SCORE_KNEE_MAX, DEPTH_SCORE_KNEE_MIN
    )
    hip_part = _linear_depth_component(
        float(min_hip_angle), DEPTH_SCORE_HIP_MAX, DEPTH_SCORE_HIP_MIN
    )
    score = DEPTH_SCORE_KNEE_WEIGHT * knee_part + DEPTH_SCORE_HIP_WEIGHT * hip_part
    return _clamp(score)


@dataclass(frozen=True)
class SquatRepScoreInput:
    """Normalized per-rep metrics consumed by squat scoring."""

    depth_score: float | None = None
    depth_status: str = "unknown"
    min_knee_angle: float | None = None
    min_hip_angle: float | None = None
    max_torso_lean: float | None = None
    valid: bool = False
    completed_full_cycle: bool = False
    errors: tuple[str, ...] = ()
    usable: bool = True
    # Front-camera 3D angles read deeper than 2D side-view ones.
    too_deep_angle: float = TOO_DEEP_KNEE_ANGLE

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> SquatRepScoreInput:
        errors_raw = raw.get("errors") or ()
        if isinstance(errors_raw, str):
            errors: tuple[str, ...] = (errors_raw,)
        else:
            errors = tuple(str(e) for e in errors_raw)

        usable = raw.get("usable", True)
        if usable is None:
            usable = True
        # Explicit low-visibility / camera-invalid markers
        if raw.get("landmark_visibility_ok") is False:
            usable = False
        if raw.get("low_visibility") is True:
            usable = False
        if str(raw.get("depth_status") or "") == "metrics_incomplete" and (
            raw.get("depth_score") is None
            and raw.get("min_knee_angle") is None
            and raw.get("metric_min_knee_angle") is None
        ):
            usable = False

        min_knee = _as_float(raw.get("min_knee_angle"))
        if min_knee is None:
            min_knee = _as_float(raw.get("metric_min_knee_angle"))
        min_hip = _as_float(raw.get("min_hip_angle"))
        max_torso = _as_float(raw.get("max_torso_lean"))
        if max_torso is None:
            max_torso = _as_float(raw.get("current_rep_max_torso_lean"))

        valid = bool(raw.get("valid", False))
        completed = raw.get("completed_full_cycle")
        if completed is None:
            completed = valid
        else:
            completed = bool(completed)

        return cls(
            depth_score=_as_float(raw.get("depth_score")),
            depth_status=str(raw.get("depth_status") or "unknown"),
            min_knee_angle=min_knee,
            min_hip_angle=min_hip,
            max_torso_lean=max_torso,
            valid=valid,
            completed_full_cycle=completed,
            errors=errors,
            usable=bool(usable),
            too_deep_angle=_as_float(raw.get("too_deep_angle")) or TOO_DEEP_KNEE_ANGLE,
        )


@dataclass(frozen=True)
class SquatScoreResult:
    """Internal squat score payload (not a backend JSON contract)."""

    score: int
    components: dict[str, float] = field(default_factory=dict)
    scored_rep_count: int = 0
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "components": dict(self.components),
            "scored_rep_count": self.scored_rep_count,
            "reason": self.reason,
        }

    def as_breakdown(self) -> ScoreBreakdown:
        return ScoreBreakdown(score=self.score, components=dict(self.components))


def _zero_components() -> dict[str, float]:
    return {key: 0.0 for key in SQUAT_SCORE_COMPONENT_KEYS}


def score_depth_component(rep: SquatRepScoreInput) -> float:
    """Depth component: prefer analyzer continuous depth_score."""
    if rep.depth_score is not None:
        return _clamp(rep.depth_score)

    recomputed = recompute_depth_score_from_angles(
        rep.min_knee_angle, rep.min_hip_angle
    )
    if recomputed is not None:
        return recomputed

    return _clamp(_DEPTH_STATUS_SCORES.get(rep.depth_status, 0.0))


def score_knee_control_component(rep: SquatRepScoreInput) -> float:
    """Knee control from min knee angle + existing form error codes."""
    score = 100.0
    error_set = set(rep.errors)

    if rep.min_knee_angle is not None and rep.min_knee_angle < rep.too_deep_angle:
        deficit = rep.too_deep_angle - float(rep.min_knee_angle)
        score -= _KNEE_TOO_DEEP_BASE_PENALTY + deficit * _KNEE_TOO_DEEP_PER_DEGREE
    elif "too_deep_or_unstable" in error_set:
        score -= _KNEE_TOO_DEEP_BASE_PENALTY

    if "too_fast" in error_set:
        score -= _KNEE_TOO_FAST_PENALTY

    if "knee_valgus" in error_set or "knee_lateral_shift" in error_set:
        score -= _KNEE_TRACKING_PENALTY

    if (
        "knee_angle_insufficient" in error_set
        or "insufficient_depth" in error_set
    ):
        # Shallow bottom often coexists with depth score; apply moderate knee penalty
        score -= _KNEE_INSUFFICIENT_PENALTY

    return _clamp(score)


def score_torso_posture_component(rep: SquatRepScoreInput) -> float:
    """Torso posture from max lean vs analyzer torso thresholds."""
    error_set = set(rep.errors)
    lean = rep.max_torso_lean

    if lean is None:
        if "excessive_forward_lean" in error_set:
            return _TORSO_EXCESSIVE_SCORE
        if "torso_lean" in error_set:
            return _TORSO_THRESHOLD_SCORE
        # No lean measurement and no torso errors → neutral-good
        return 100.0

    lean_v = float(lean)
    if lean_v <= _TORSO_EXCELLENT_MAX:
        return 100.0
    if lean_v < TORSO_LEAN_THRESHOLD:
        span = TORSO_LEAN_THRESHOLD - _TORSO_EXCELLENT_MAX
        t = (lean_v - _TORSO_EXCELLENT_MAX) / span if span > 0 else 1.0
        return _clamp(100.0 - t * (100.0 - _TORSO_GOOD_FLOOR))
    if lean_v < EXCESSIVE_TORSO_LEAN:
        span = EXCESSIVE_TORSO_LEAN - TORSO_LEAN_THRESHOLD
        t = (lean_v - TORSO_LEAN_THRESHOLD) / span if span > 0 else 1.0
        return _clamp(
            _TORSO_GOOD_FLOOR
            - t * (_TORSO_GOOD_FLOOR - _TORSO_EXCESSIVE_SCORE)
        )
    excess = lean_v - EXCESSIVE_TORSO_LEAN
    return _clamp(_TORSO_EXCESSIVE_SCORE - excess * _TORSO_EXCESS_PER_DEGREE)


def score_rep_quality_component(rep: SquatRepScoreInput) -> float:
    """Rep quality from validity, full cycle, and recorded form errors."""
    error_set = set(rep.errors)

    if rep.valid and rep.completed_full_cycle and not error_set:
        return 100.0

    if rep.valid and rep.completed_full_cycle:
        score = 100.0
        score -= len(error_set) * _REP_QUALITY_FORM_ERROR_PENALTY
        return _clamp(score)

    # Invalid / half / incomplete attempt
    score = _REP_QUALITY_INVALID_BASE
    if "incomplete_rep" in error_set:
        score = min(score, _REP_QUALITY_INCOMPLETE_CAP)
    if (
        "insufficient_depth" in error_set
        or "squat_depth_reach" in error_set
        or "knee_angle_insufficient" in error_set
    ):
        score = min(score, _REP_QUALITY_DEPTH_ERROR_CAP)
    if error_set:
        score -= max(0, len(error_set) - 1) * (_REP_QUALITY_FORM_ERROR_PENALTY / 2.0)
    return _clamp(score)


def calculate_squat_rep_components(rep: SquatRepScoreInput) -> dict[str, float]:
    return {
        SQUAT_SCORE_COMPONENT_DEPTH: score_depth_component(rep),
        SQUAT_SCORE_COMPONENT_KNEE_CONTROL: score_knee_control_component(rep),
        SQUAT_SCORE_COMPONENT_TORSO_POSTURE: score_torso_posture_component(rep),
        SQUAT_SCORE_COMPONENT_REP_QUALITY: score_rep_quality_component(rep),
    }


def calculate_squat_rep_score(rep: SquatRepScoreInput | Mapping[str, Any]) -> ScoreBreakdown:
    """Score a single squat rep; returns shared ScoreBreakdown."""
    normalized = (
        rep
        if isinstance(rep, SquatRepScoreInput)
        else SquatRepScoreInput.from_mapping(rep)
    )
    if not normalized.usable:
        return ScoreBreakdown(score=0, components=_zero_components())
    components = calculate_squat_rep_components(normalized)
    return calculate_score_breakdown(components, SQUAT_SCORE_WEIGHTS)


def _average_components(
    component_rows: Sequence[Mapping[str, float]],
) -> dict[str, float]:
    totals = {key: 0.0 for key in SQUAT_SCORE_COMPONENT_KEYS}
    for row in component_rows:
        for key in SQUAT_SCORE_COMPONENT_KEYS:
            totals[key] += float(row[key])
    n = float(len(component_rows))
    return {key: totals[key] / n for key in SQUAT_SCORE_COMPONENT_KEYS}


def calculate_squat_score(
    reps: Iterable[SquatRepScoreInput | Mapping[str, Any]] | None,
) -> SquatScoreResult:
    """Video-level squat score from completed usable reps.

    Aggregation: mean of per-rep component scores across usable recorded reps,
    then shared weighted scoring. Empty / all-unusable → score 0.
    """
    if reps is None:
        return SquatScoreResult(
            score=0,
            components=_zero_components(),
            scored_rep_count=0,
            reason="no_completed_reps",
        )

    normalized: list[SquatRepScoreInput] = []
    for item in reps:
        if isinstance(item, SquatRepScoreInput):
            normalized.append(item)
        else:
            normalized.append(SquatRepScoreInput.from_mapping(item))

    usable = [rep for rep in normalized if rep.usable]
    if not usable:
        reason = "no_completed_reps" if not normalized else "no_usable_reps"
        return SquatScoreResult(
            score=0,
            components=_zero_components(),
            scored_rep_count=0,
            reason=reason,
        )

    rows = [calculate_squat_rep_components(rep) for rep in usable]
    avg_components = _average_components(rows)
    breakdown = calculate_score_breakdown(avg_components, SQUAT_SCORE_WEIGHTS)
    return SquatScoreResult(
        score=breakdown.score,
        components=dict(breakdown.components),
        scored_rep_count=len(usable),
        reason=None,
    )


def calculate_squat_score_from_history(
    rep_history: Sequence[Mapping[str, Any]] | None,
) -> SquatScoreResult:
    """Convenience wrapper for SquatAnalyzer.rep_history."""
    if not rep_history:
        return calculate_squat_score([])
    return calculate_squat_score(rep_history)
