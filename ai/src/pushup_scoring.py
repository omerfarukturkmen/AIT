"""Push-up-specific 0–100 scoring built on the shared weighted scoring API.

Consumes metrics already produced by PushupAnalyzer (elbow ROM, body-line flags,
reached_bottom, frame durations, form issues). Does not reimplement pose analysis.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

from scoring import SCORE_MAX, SCORE_MIN, ScoreBreakdown, calculate_score_breakdown
from pushup_analyzer import (
    ASCENT_START_ANGLE,
    BACK_BEND_ANGLE_THRESHOLD,
    BOTTOM_POSITION_ANGLE,
    DESCENT_START_ANGLE,
    HIP_HIGH_OFFSET_THRESHOLD,
    HIP_SAG_OFFSET_THRESHOLD,
    UP_POSITION_ANGLE,
)

# --- Component keys & default weights (must sum to 1.0) ---
PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE = "elbow_angle"
PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT = "body_alignment"
PUSHUP_SCORE_COMPONENT_REP_DEPTH = "rep_depth"
PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL = "tempo_control"

PUSHUP_SCORE_COMPONENT_KEYS: tuple[str, ...] = (
    PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE,
    PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT,
    PUSHUP_SCORE_COMPONENT_REP_DEPTH,
    PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL,
)

PUSHUP_SCORE_WEIGHTS: dict[str, float] = {
    PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE: 0.30,
    PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT: 0.30,
    PUSHUP_SCORE_COMPONENT_REP_DEPTH: 0.25,
    PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL: 0.15,
}

# Body-alignment issue penalties (aligned with analyzer form issue codes)
_BODY_ISSUE_PENALTIES: dict[str, float] = {
    "hips_sagging": 35.0,
    "hips_too_high": 30.0,
    "back_bent": 30.0,
    "elbows_flared": 20.0,
    "shoulder_alignment_issue": 20.0,
}

# Rep depth
_REP_DEPTH_NO_BOTTOM = 20.0
_REP_DEPTH_BOTTOM_INVALID = 45.0
_REP_DEPTH_SHALLOW_BOTTOM = 70.0

# Tempo from frame counts (derived from 3-frame state confirmation pattern)
_TEMPO_MIN_GOOD_FRAMES = 24
_TEMPO_MIN_ACCEPTABLE_FRAMES = 12
_TEMPO_VERY_SHORT_FRAMES = 6
_TEMPO_SHORT_SCORE = 35.0
_TEMPO_ACCEPTABLE_SCORE = 70.0
_TEMPO_CV_SOFT = 0.25
_TEMPO_CV_HARD = 0.50
_TEMPO_CV_SOFT_FACTOR = 0.85
_TEMPO_CV_HARD_FACTOR = 0.70


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


def _as_int(value: Any) -> int | None:
    number = _as_float(value)
    if number is None:
        return None
    return int(number)


@dataclass(frozen=True)
class PushupRepScoreInput:
    """Normalized per-rep metrics consumed by push-up scoring."""

    min_elbow_angle: float | None = None
    rep_start_elbow_angle: float | None = None
    reached_bottom: bool = False
    valid: bool = False
    completed_full_cycle: bool = False
    form_issues: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    duration_frames: int | None = None
    max_abs_body_line_offset: float | None = None
    min_body_alignment_angle: float | None = None
    usable: bool = True

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> PushupRepScoreInput:
        issues_raw = raw.get("form_issues") or ()
        if isinstance(issues_raw, str):
            form_issues: tuple[str, ...] = (issues_raw,)
        else:
            form_issues = tuple(str(x) for x in issues_raw)

        errors_raw = raw.get("errors") or ()
        if isinstance(errors_raw, str):
            errors: tuple[str, ...] = (errors_raw,)
        else:
            errors = tuple(str(x) for x in errors_raw)

        usable = raw.get("usable", True)
        if usable is None:
            usable = True
        if raw.get("landmark_visibility_ok") is False:
            usable = False
        if raw.get("low_visibility") is True:
            usable = False
        if raw.get("visibility_blocked") is True:
            usable = False

        valid = bool(raw.get("valid", False))
        completed = raw.get("completed_full_cycle")
        if completed is None:
            completed = valid
        else:
            completed = bool(completed)

        reached = raw.get("reached_bottom")
        if reached is None:
            reached = "not_low_enough" not in errors and (
                valid or "incomplete_up" in errors
            )
        else:
            reached = bool(reached)

        duration = _as_int(raw.get("duration_frames"))
        if duration is None:
            start = _as_int(raw.get("start_frame"))
            end = _as_int(raw.get("end_frame"))
            if start is not None and end is not None and end >= start:
                duration = end - start + 1

        return cls(
            min_elbow_angle=_as_float(raw.get("min_elbow_angle")),
            rep_start_elbow_angle=_as_float(raw.get("rep_start_elbow_angle")),
            reached_bottom=reached,
            valid=valid,
            completed_full_cycle=completed,
            form_issues=form_issues,
            errors=errors,
            duration_frames=duration,
            max_abs_body_line_offset=_as_float(raw.get("max_abs_body_line_offset")),
            min_body_alignment_angle=_as_float(raw.get("min_body_alignment_angle")),
            usable=bool(usable),
        )


@dataclass(frozen=True)
class PushupScoreResult:
    """Internal push-up score payload (not a backend JSON contract)."""

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
    return {key: 0.0 for key in PUSHUP_SCORE_COMPONENT_KEYS}


def score_elbow_angle_component(rep: PushupRepScoreInput) -> float:
    """Elbow ROM quality using analyzer hysteresis thresholds."""
    min_elbow = rep.min_elbow_angle
    if min_elbow is None:
        return 0.0

    value = float(min_elbow)
    if value <= BOTTOM_POSITION_ANGLE:
        return 100.0
    if value <= ASCENT_START_ANGLE:
        span = ASCENT_START_ANGLE - BOTTOM_POSITION_ANGLE
        t = (value - BOTTOM_POSITION_ANGLE) / span if span > 0 else 1.0
        return _clamp(100.0 - t * 20.0)
    if value <= DESCENT_START_ANGLE:
        span = DESCENT_START_ANGLE - ASCENT_START_ANGLE
        t = (value - ASCENT_START_ANGLE) / span if span > 0 else 1.0
        return _clamp(80.0 - t * 55.0)
    if value >= UP_POSITION_ANGLE:
        return 0.0
    span = UP_POSITION_ANGLE - DESCENT_START_ANGLE
    t = (value - DESCENT_START_ANGLE) / span if span > 0 else 1.0
    return _clamp(25.0 - t * 25.0)


def score_body_alignment_component(rep: PushupRepScoreInput) -> float:
    """Body line / hip / shoulder issues from analyzer form flags + metrics."""
    score = 100.0
    issue_set = set(rep.form_issues) | set(rep.errors)
    for issue, penalty in _BODY_ISSUE_PENALTIES.items():
        if issue in issue_set:
            score -= penalty

    offset = rep.max_abs_body_line_offset
    if offset is not None:
        sag_thr = abs(HIP_SAG_OFFSET_THRESHOLD)
        high_thr = abs(HIP_HIGH_OFFSET_THRESHOLD)
        thr = max(sag_thr, high_thr)
        if offset >= thr:
            excess = offset - thr
            score -= min(25.0, excess / thr * 25.0)

    align = rep.min_body_alignment_angle
    if align is not None and align < BACK_BEND_ANGLE_THRESHOLD:
        deficit = BACK_BEND_ANGLE_THRESHOLD - float(align)
        score -= min(25.0, deficit * 1.5)

    return _clamp(score)


def score_rep_depth_component(rep: PushupRepScoreInput) -> float:
    """Whether the rep achieved confirmed bottom / full ROM (not elbow quality)."""
    error_set = set(rep.errors)
    if not rep.reached_bottom or "not_low_enough" in error_set:
        return _REP_DEPTH_NO_BOTTOM

    if not rep.valid or not rep.completed_full_cycle:
        return _REP_DEPTH_BOTTOM_INVALID

    min_elbow = rep.min_elbow_angle
    if min_elbow is None:
        return 85.0
    if float(min_elbow) <= BOTTOM_POSITION_ANGLE:
        return 100.0
    if float(min_elbow) <= ASCENT_START_ANGLE:
        return _REP_DEPTH_SHALLOW_BOTTOM
    return 55.0


def score_tempo_control_component(rep: PushupRepScoreInput) -> float:
    """Tempo from rep duration_frames — rejects ultra-short false-positive cycles."""
    frames = rep.duration_frames
    if frames is None or frames <= 0:
        # Missing duration: neutral-good for otherwise valid reps, low for invalid
        if rep.valid and rep.completed_full_cycle:
            return 80.0
        return 40.0

    n = int(frames)
    if n <= _TEMPO_VERY_SHORT_FRAMES:
        return 15.0
    if n < _TEMPO_MIN_ACCEPTABLE_FRAMES:
        span = _TEMPO_MIN_ACCEPTABLE_FRAMES - _TEMPO_VERY_SHORT_FRAMES
        t = (n - _TEMPO_VERY_SHORT_FRAMES) / span if span > 0 else 1.0
        return _clamp(15.0 + t * (_TEMPO_SHORT_SCORE - 15.0))
    if n < _TEMPO_MIN_GOOD_FRAMES:
        span = _TEMPO_MIN_GOOD_FRAMES - _TEMPO_MIN_ACCEPTABLE_FRAMES
        t = (n - _TEMPO_MIN_ACCEPTABLE_FRAMES) / span if span > 0 else 1.0
        return _clamp(_TEMPO_SHORT_SCORE + t * (_TEMPO_ACCEPTABLE_SCORE - _TEMPO_SHORT_SCORE))
    return 100.0


def calculate_pushup_rep_components(rep: PushupRepScoreInput) -> dict[str, float]:
    return {
        PUSHUP_SCORE_COMPONENT_ELBOW_ANGLE: score_elbow_angle_component(rep),
        PUSHUP_SCORE_COMPONENT_BODY_ALIGNMENT: score_body_alignment_component(rep),
        PUSHUP_SCORE_COMPONENT_REP_DEPTH: score_rep_depth_component(rep),
        PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL: score_tempo_control_component(rep),
    }


def calculate_pushup_rep_score(
    rep: PushupRepScoreInput | Mapping[str, Any],
) -> ScoreBreakdown:
    """Score a single push-up rep; returns shared ScoreBreakdown."""
    normalized = (
        rep
        if isinstance(rep, PushupRepScoreInput)
        else PushupRepScoreInput.from_mapping(rep)
    )
    if not normalized.usable:
        return ScoreBreakdown(score=0, components=_zero_components())
    components = calculate_pushup_rep_components(normalized)
    return calculate_score_breakdown(components, PUSHUP_SCORE_WEIGHTS)


def _average_components(
    component_rows: Sequence[Mapping[str, float]],
) -> dict[str, float]:
    totals = {key: 0.0 for key in PUSHUP_SCORE_COMPONENT_KEYS}
    for row in component_rows:
        for key in PUSHUP_SCORE_COMPONENT_KEYS:
            totals[key] += float(row[key])
    n = float(len(component_rows))
    return {key: totals[key] / n for key in PUSHUP_SCORE_COMPONENT_KEYS}


def _tempo_consistency_factor(durations: Sequence[int]) -> float:
    if len(durations) < 2:
        return 1.0
    mean = statistics.fmean(durations)
    if mean <= 0:
        return 1.0
    cv = statistics.pstdev(durations) / mean
    if cv >= _TEMPO_CV_HARD:
        return _TEMPO_CV_HARD_FACTOR
    if cv >= _TEMPO_CV_SOFT:
        return _TEMPO_CV_SOFT_FACTOR
    return 1.0


def calculate_pushup_score(
    reps: Iterable[PushupRepScoreInput | Mapping[str, Any]] | None,
) -> PushupScoreResult:
    """Video-level push-up score from completed usable reps.

    Aggregation mirrors squat scoring: mean of per-rep components, then shared
    weighted scoring. Multi-rep tempo consistency may scale tempo_control only.
    """
    if reps is None:
        return PushupScoreResult(
            score=0,
            components=_zero_components(),
            scored_rep_count=0,
            reason="no_completed_reps",
        )

    normalized: list[PushupRepScoreInput] = []
    for item in reps:
        if isinstance(item, PushupRepScoreInput):
            normalized.append(item)
        else:
            normalized.append(PushupRepScoreInput.from_mapping(item))

    usable = [rep for rep in normalized if rep.usable]
    if not usable:
        reason = "no_completed_reps" if not normalized else "no_usable_reps"
        return PushupScoreResult(
            score=0,
            components=_zero_components(),
            scored_rep_count=0,
            reason=reason,
        )

    rows = [calculate_pushup_rep_components(rep) for rep in usable]
    avg_components = _average_components(rows)

    durations = [
        int(rep.duration_frames)
        for rep in usable
        if rep.duration_frames is not None and rep.duration_frames > 0
    ]
    factor = _tempo_consistency_factor(durations)
    if factor != 1.0:
        avg_components[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL] = _clamp(
            avg_components[PUSHUP_SCORE_COMPONENT_TEMPO_CONTROL] * factor
        )

    breakdown = calculate_score_breakdown(avg_components, PUSHUP_SCORE_WEIGHTS)
    return PushupScoreResult(
        score=breakdown.score,
        components=dict(breakdown.components),
        scored_rep_count=len(usable),
        reason=None,
    )


def calculate_pushup_score_from_history(
    rep_history: Sequence[Mapping[str, Any]] | None,
) -> PushupScoreResult:
    """Convenience wrapper for PushupAnalyzer.rep_history."""
    if not rep_history:
        return calculate_pushup_score([])
    return calculate_pushup_score(rep_history)
