"""Final versioned AI analysis response contract (schema 1.0).

Serializes existing domain results (reps, score, feedback) into a single
JSON-safe payload shared by squat and push-up. Does not recompute domain logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from feedback_priority import build_feedback_payload
from rep_summary import RepSummary, summarize_rep_counters

ANALYSIS_SCHEMA_VERSION = "1.0"

ANALYSIS_STATUS_COMPLETED = "completed"
ANALYSIS_STATUS_INSUFFICIENT_VISIBILITY = "insufficient_landmark_visibility"

CANONICAL_EXERCISE_TYPES = frozenset({"squat", "pushup"})


def _canonical_exercise_types() -> frozenset[str]:
    try:
        from exercise_registry import registered_exercise_keys

        return frozenset(registered_exercise_keys())
    except Exception:
        return CANONICAL_EXERCISE_TYPES

TOP_LEVEL_KEYS: tuple[str, ...] = (
    "schema_version",
    "exercise_type",
    "analysis",
    "reps",
    "score",
    "feedback",
    "warnings",
)

ANALYSIS_KEYS: tuple[str, ...] = (
    "status",
    "frames",
    "processed_frames",
    "duration_seconds",
)

REPS_KEYS: tuple[str, ...] = ("successful", "failed", "total")

SCORE_KEYS: tuple[str, ...] = ("overall", "components")

FEEDBACK_KEYS: tuple[str, ...] = ("top", "all")

FEEDBACK_ITEM_KEYS: tuple[str, ...] = (
    "code",
    "message",
    "importance",
    "severity",
)

SEVERITY_VALUES: frozenset[str] = frozenset({"critical", "medium", "suggestion"})


def _json_number(value: Any) -> float:
    """Coerce numpy / numeric wrappers to a native float."""
    if hasattr(value, "item") and callable(value.item):
        try:
            value = value.item()
        except Exception:
            pass
    return float(value)


def _json_int_score(value: Any) -> int:
    """Round to a clamped 0–100 integer (matches scoring round convention)."""
    n = int(round(_json_number(value)))
    return max(0, min(100, n))


def _json_nonneg_int(value: Any) -> int:
    n = int(round(_json_number(value)))
    return max(0, n)


def _json_nonneg_float(value: Any) -> float:
    return max(0.0, float(_json_number(value)))


def normalize_exercise_type_for_response(exercise_type: str | None) -> str:
    raw = (exercise_type or "").strip().lower().replace("_", "-")
    if raw in {"push-up", "push up"}:
        raw = "pushup"
    allowed = _canonical_exercise_types()
    if raw not in allowed:
        # Fall back to registry normalization when available.
        try:
            from exercise_registry import normalize_exercise_type

            return normalize_exercise_type(str(exercise_type))
        except Exception as exc:
            raise ValueError(
                f"Unsupported exercise_type for response: {exercise_type!r}"
            ) from exc
    return raw


def resolve_exercise_type(analyzer: Any) -> str:
    for attr in ("exercise", "exercise_type"):
        value = getattr(analyzer, attr, None)
        if value:
            return normalize_exercise_type_for_response(str(value))
    # Fallback from class name
    name = type(analyzer).__name__.lower()
    if "push" in name:
        return "pushup"
    return "squat"


@dataclass(frozen=True)
class AnalysisMetadata:
    status: str = ANALYSIS_STATUS_COMPLETED
    frames: int = 0
    processed_frames: int = 0
    duration_seconds: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "frames", _json_nonneg_int(self.frames))
        object.__setattr__(
            self, "processed_frames", _json_nonneg_int(self.processed_frames)
        )
        object.__setattr__(
            self, "duration_seconds", _json_nonneg_float(self.duration_seconds)
        )
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("analysis.status must be a non-empty string")

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": str(self.status),
            "frames": int(self.frames),
            "processed_frames": int(self.processed_frames),
            "duration_seconds": float(self.duration_seconds),
        }


@dataclass(frozen=True)
class ScoreSummary:
    overall: int = 0
    components: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        overall = _json_int_score(self.overall)
        comps = {
            str(k): _json_int_score(v) for k, v in dict(self.components).items()
        }
        object.__setattr__(self, "overall", overall)
        object.__setattr__(self, "components", comps)

    def as_dict(self) -> dict[str, Any]:
        return {
            "overall": int(self.overall),
            "components": {k: int(v) for k, v in self.components.items()},
        }


@dataclass(frozen=True)
class FeedbackSummary:
    top: list[dict[str, Any]] = field(default_factory=list)
    all: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "top": [dict(item) for item in self.top],
            "all": [dict(item) for item in self.all],
        }


@dataclass(frozen=True)
class AnalysisResponse:
    """Canonical backend analysis payload (schema 1.0)."""

    schema_version: str = ANALYSIS_SCHEMA_VERSION
    exercise_type: str = "squat"
    analysis: AnalysisMetadata = field(default_factory=AnalysisMetadata)
    reps: RepSummary = field(
        default_factory=lambda: RepSummary(
            successful_reps=0, failed_reps=0, total_reps=0
        )
    )
    score: ScoreSummary = field(default_factory=ScoreSummary)
    feedback: FeedbackSummary = field(default_factory=FeedbackSummary)
    warnings: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "exercise_type",
            normalize_exercise_type_for_response(self.exercise_type),
        )
        if self.schema_version != ANALYSIS_SCHEMA_VERSION:
            # Allow only the active schema version in this module.
            raise ValueError(
                f"schema_version must be {ANALYSIS_SCHEMA_VERSION!r}, "
                f"got {self.schema_version!r}"
            )
        object.__setattr__(
            self,
            "warnings",
            [str(w) for w in self.warnings if w is not None and str(w)],
        )

    def as_dict(self) -> dict[str, Any]:
        """JSON-safe primitive dict for the final contract."""
        return {
            "schema_version": str(self.schema_version),
            "exercise_type": str(self.exercise_type),
            "analysis": self.analysis.as_dict(),
            "reps": {
                "successful": int(self.reps.successful_reps),
                "failed": int(self.reps.failed_reps),
                "total": int(self.reps.total_reps),
            },
            "score": self.score.as_dict(),
            "feedback": self.feedback.as_dict(),
            "warnings": list(self.warnings),
        }


def _normalize_feedback_item(raw: Mapping[str, Any]) -> dict[str, Any]:
    severity = raw.get("severity", "suggestion")
    if isinstance(severity, Enum):
        severity = severity.value
    severity_str = str(severity).lower()
    if severity_str.startswith("feedbackseverity."):
        severity_str = severity_str.split(".", 1)[-1].lower()
    if severity_str not in SEVERITY_VALUES:
        severity_str = "suggestion"
    importance = _json_nonneg_int(raw.get("importance", 0))
    importance = max(0, min(100, importance))
    return {
        "code": str(raw.get("code", "")),
        "message": str(raw.get("message", "")),
        "importance": int(importance),
        "severity": severity_str,
    }


def _score_from_analyzer(analyzer: Any) -> ScoreSummary:
    if hasattr(analyzer, "get_score_breakdown"):
        breakdown = analyzer.get_score_breakdown()
        if isinstance(breakdown, Mapping):
            overall = breakdown.get("score", breakdown.get("overall", 0))
            components = breakdown.get("components") or {}
            return ScoreSummary(overall=overall, components=dict(components))
    return ScoreSummary()


def _reps_from_analyzer(analyzer: Any) -> RepSummary:
    if hasattr(analyzer, "get_rep_summary"):
        summary = analyzer.get_rep_summary()
        if isinstance(summary, Mapping):
            return summarize_rep_counters(
                successful_reps=int(summary.get("successful_reps", 0)),
                failed_reps=int(summary.get("failed_reps", 0)),
            )
    return RepSummary(successful_reps=0, failed_reps=0, total_reps=0)


def _feedback_from_domain(
    analyzer: Any,
    *,
    extra_feedback_messages: Sequence[str] | None = None,
) -> FeedbackSummary:
    """Build feedback.all / feedback.top via existing feedback_priority helpers."""
    codes: list[str] = []
    messages: list[str] = []

    errors = getattr(analyzer, "errors", None)
    if errors:
        codes.extend(str(c) for c in errors if c)

    session = getattr(analyzer, "_session_feedback", None)
    if session:
        messages.extend(str(m) for m in session if m)
    else:
        fb = getattr(analyzer, "feedback", None)
        if fb:
            messages.extend(str(m) for m in fb if m)

    for msg in extra_feedback_messages or ():
        if msg and str(msg) not in messages:
            messages.append(str(msg))

    # Prefer ready domain getters when no session extras need merging.
    if not extra_feedback_messages and hasattr(analyzer, "get_feedback_items"):
        all_items = [
            _normalize_feedback_item(item)
            for item in (analyzer.get_feedback_items() or [])
        ]
        if hasattr(analyzer, "get_top_feedback_items"):
            top_items = [
                _normalize_feedback_item(item)
                for item in (analyzer.get_top_feedback_items() or [])
            ]
        else:
            top_items = all_items[:3]
        return FeedbackSummary(top=top_items, all=all_items)

    payload = build_feedback_payload(codes=codes, messages=messages)
    all_items = [
        _normalize_feedback_item(item) for item in (payload.get("feedback_items") or [])
    ]
    top_items = [
        _normalize_feedback_item(item) for item in (payload.get("top_feedback") or [])
    ]
    return FeedbackSummary(top=top_items, all=all_items)


def build_analysis_response(
    analyzer: Any,
    *,
    frames: int = 0,
    processed_frames: int = 0,
    duration_seconds: float = 0.0,
    status: str = ANALYSIS_STATUS_COMPLETED,
    extra_feedback_messages: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    exercise_type: str | None = None,
) -> AnalysisResponse:
    """Assemble the final contract from an analyzer and analysis metadata."""
    ex = (
        normalize_exercise_type_for_response(exercise_type)
        if exercise_type
        else resolve_exercise_type(analyzer)
    )
    return AnalysisResponse(
        schema_version=ANALYSIS_SCHEMA_VERSION,
        exercise_type=ex,
        analysis=AnalysisMetadata(
            status=str(status or ANALYSIS_STATUS_COMPLETED),
            frames=frames,
            processed_frames=processed_frames,
            duration_seconds=duration_seconds,
        ),
        reps=_reps_from_analyzer(analyzer),
        score=_score_from_analyzer(analyzer),
        feedback=_feedback_from_domain(
            analyzer,
            extra_feedback_messages=extra_feedback_messages,
        ),
        warnings=list(warnings or []),
    )


def serialize_analysis_response(
    analyzer: Any,
    *,
    frames: int = 0,
    processed_frames: int = 0,
    duration_seconds: float = 0.0,
    status: str = ANALYSIS_STATUS_COMPLETED,
    extra_feedback_messages: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    exercise_type: str | None = None,
) -> dict[str, Any]:
    """Return a JSON-serializable dict for the final analysis contract."""
    return build_analysis_response(
        analyzer,
        frames=frames,
        processed_frames=processed_frames,
        duration_seconds=duration_seconds,
        status=status,
        extra_feedback_messages=extra_feedback_messages,
        warnings=warnings,
        exercise_type=exercise_type,
    ).as_dict()


def empty_analysis_response(
    *,
    exercise_type: str = "squat",
    status: str = ANALYSIS_STATUS_COMPLETED,
    frames: int = 0,
    processed_frames: int = 0,
    duration_seconds: float = 0.0,
    warnings: Sequence[str] | None = None,
    component_defaults: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    """Valid empty payload with the same top-level shape."""
    components = dict(component_defaults or {})
    response = AnalysisResponse(
        schema_version=ANALYSIS_SCHEMA_VERSION,
        exercise_type=exercise_type,
        analysis=AnalysisMetadata(
            status=status,
            frames=frames,
            processed_frames=processed_frames,
            duration_seconds=duration_seconds,
        ),
        reps=RepSummary(successful_reps=0, failed_reps=0, total_reps=0),
        score=ScoreSummary(overall=0, components=components),
        feedback=FeedbackSummary(top=[], all=[]),
        warnings=list(warnings or []),
    )
    return response.as_dict()
