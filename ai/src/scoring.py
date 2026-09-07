"""Shared 0–100 weighted scoring utilities for exercise analysis.

Movement-specific criteria (squat depth, push-up elbow, etc.) are not defined
here; callers supply component scores and weights. This module only validates
inputs and combines them into a safe integer final score plus breakdown.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping

SCORE_MIN = 0.0
SCORE_MAX = 100.0
WEIGHT_SUM_TARGET = 1.0
WEIGHT_SUM_TOLERANCE = 1e-6


@dataclass(frozen=True)
class ScoreBreakdown:
    """Internal score result with clamped component values and final integer."""

    score: int
    components: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "components": dict(self.components),
        }


def _require_mapping(name: str, value: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if value is None or not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping of name -> number")
    if len(value) == 0:
        raise ValueError(f"{name} must not be empty")
    return value


def _validate_finite_number(name: str, key: str, raw: Any) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise ValueError(f"{name}['{key}'] must be a finite number")
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError(f"{name}['{key}'] must be a finite number, got {raw!r}")
    return value


def _clamp_score(value: float) -> float:
    return max(SCORE_MIN, min(SCORE_MAX, value))


def _normalize_components(components: Mapping[str, Any]) -> dict[str, float]:
    mapping = _require_mapping("components", components)
    clamped: dict[str, float] = {}
    for key, raw in mapping.items():
        value = _validate_finite_number("components", str(key), raw)
        clamped[str(key)] = _clamp_score(value)
    return clamped


def _normalize_weights(
    weights: Mapping[str, Any],
    component_keys: set[str],
) -> dict[str, float]:
    mapping = _require_mapping("weights", weights)
    normalized: dict[str, float] = {}
    for key, raw in mapping.items():
        name = str(key)
        value = _validate_finite_number("weights", name, raw)
        if value < 0.0:
            raise ValueError(f"weights['{name}'] must be >= 0, got {value}")
        normalized[name] = value

    weight_keys = set(normalized.keys())
    if weight_keys != component_keys:
        missing = sorted(component_keys - weight_keys)
        extra = sorted(weight_keys - component_keys)
        parts: list[str] = []
        if missing:
            parts.append(f"missing weights for: {missing}")
        if extra:
            parts.append(f"unexpected weight keys: {extra}")
        raise ValueError("component and weight keys must match; " + "; ".join(parts))

    total = sum(normalized.values())
    if total <= 0.0:
        raise ValueError("weights must sum to a positive value near 1.0")
    if not math.isclose(total, WEIGHT_SUM_TARGET, abs_tol=WEIGHT_SUM_TOLERANCE):
        raise ValueError(
            f"weights must sum to {WEIGHT_SUM_TARGET} "
            f"(tolerance={WEIGHT_SUM_TOLERANCE}), got {total}"
        )
    return normalized


def calculate_score_breakdown(
    components: Mapping[str, float],
    weights: Mapping[str, float],
) -> ScoreBreakdown:
    """Combine component scores with weights into a ScoreBreakdown.

    Component scores outside [0, 100] are clamped. Invalid numerics (NaN/inf),
    empty inputs, key mismatches, negative weights, or weight sums not near 1.0
    raise ValueError.
    """
    clamped = _normalize_components(components)
    validated_weights = _normalize_weights(weights, set(clamped.keys()))

    weighted = sum(clamped[key] * validated_weights[key] for key in clamped)
    weighted = _clamp_score(weighted)
    final_score = int(round(weighted))
    final_score = max(int(SCORE_MIN), min(int(SCORE_MAX), final_score))

    return ScoreBreakdown(score=final_score, components=clamped)


def calculate_weighted_score(
    components: Mapping[str, float],
    weights: Mapping[str, float],
) -> int:
    """Return the integer final score from weighted component scores."""
    return calculate_score_breakdown(components, weights).score
