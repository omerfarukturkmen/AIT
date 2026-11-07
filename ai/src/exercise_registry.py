"""Minimal exercise analyzer registry for extensible routing.

Register new exercises here (or via ``register_exercise``) so
``video_processor`` does not grow per-exercise ``if/elif`` blocks.

This is intentionally lightweight: no ABC hierarchy, no plugin discovery.
Lunge frame-level angle scaffold lives in ``lunge_analyzer`` and is intentionally
**not** registered here until rep/score/feedback exist (avoids fake contract data).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from pushup_analyzer import (
    create_pushup_analyzer,
    process_pushup_frame,
    pushup_pose_landmark_indices,
)
from pushup_scoring import PUSHUP_SCORE_COMPONENT_KEYS
from squat_analyzer import (
    create_squat_analyzer,
    process_squat_frame,
    squat_pose_landmark_indices,
)
from squat_scoring import SQUAT_SCORE_COMPONENT_KEYS

CreateAnalyzerFn = Callable[..., Any]
LandmarkIndicesFn = Callable[[Any], tuple[Any, ...]]
ProcessFrameFn = Callable[..., dict[str, Any]]


class UnsupportedExerciseError(ValueError):
    """Raised when exercise_type is not registered / not supported."""


@dataclass(frozen=True)
class ExerciseSpec:
    """Descriptor for one registered exercise analyzer."""

    key: str
    display_name: str
    aliases: frozenset[str]
    create_analyzer: CreateAnalyzerFn
    get_landmark_indices: LandmarkIndicesFn
    process_frame: ProcessFrameFn
    score_component_keys: tuple[str, ...]


_REGISTRY: dict[str, ExerciseSpec] = {}
_ALIAS_TO_KEY: dict[str, str] = {}


def register_exercise(spec: ExerciseSpec, *, replace: bool = False) -> None:
    """Register an exercise spec under its canonical key and aliases."""
    key = str(spec.key).strip().lower()
    if not key:
        raise ValueError("ExerciseSpec.key must be a non-empty string")
    if key in _REGISTRY and not replace:
        raise ValueError(f"Exercise already registered: {key}")

    _REGISTRY[key] = spec
    aliases = set(spec.aliases) | {key, spec.display_name}
    for alias in aliases:
        normalized_alias = _normalize_token(str(alias))
        if not normalized_alias:
            continue
        existing = _ALIAS_TO_KEY.get(normalized_alias)
        if existing is not None and existing != key and not replace:
            raise ValueError(
                f"Alias {alias!r} already mapped to {existing!r}, cannot map to {key!r}"
            )
        _ALIAS_TO_KEY[normalized_alias] = key


def registered_exercise_keys() -> tuple[str, ...]:
    """Canonical keys in stable sorted order."""
    return tuple(sorted(_REGISTRY.keys()))


def cli_exercise_choices() -> list[str]:
    """Argparse-friendly choices including common aliases."""
    choices: list[str] = []
    for key in registered_exercise_keys():
        spec = _REGISTRY[key]
        for token in (key, spec.display_name, *sorted(spec.aliases)):
            if token and token not in choices:
                choices.append(token)
    return choices


def _normalize_token(raw: str) -> str:
    return (raw or "").strip().lower().replace("_", "-")


def normalize_exercise_type(exercise_type: str) -> str:
    """Normalize CLI/backend identifiers to a registered canonical key.

    Raises:
        UnsupportedExerciseError: when the exercise type is not registered.
    """
    token = _normalize_token(exercise_type)
    # Preserve historical spacing alias: "push up" → already handled via replace
    # of "_" only; map explicit spaced form if present.
    if token == "push up":
        token = "push-up"
    key = _ALIAS_TO_KEY.get(token)
    if key is None:
        raise UnsupportedExerciseError(
            f"Unsupported exercise_type: {exercise_type}"
        )
    return key


def validate_exercise_type(exercise_type: str) -> str:
    """Validate and return the canonical exercise key."""
    return normalize_exercise_type(exercise_type)


def get_exercise_spec(exercise_type: str) -> ExerciseSpec:
    """Return the registered ``ExerciseSpec`` for ``exercise_type``."""
    key = normalize_exercise_type(exercise_type)
    return _REGISTRY[key]


def display_exercise_name(normalized_or_raw: str) -> str:
    """Human-facing exercise label for metrics / logs."""
    spec = get_exercise_spec(normalized_or_raw)
    return spec.display_name


def create_analyzer_for_exercise(
    exercise_type: str,
    *,
    fps: float = 30.0,
) -> Any:
    """Construct a fresh analyzer instance for the exercise (isolated state)."""
    spec = get_exercise_spec(exercise_type)
    return spec.create_analyzer(fps=fps)


def default_score_components(exercise_type: str) -> dict[str, int]:
    """Zero-filled score component map for the exercise."""
    spec = get_exercise_spec(exercise_type)
    return {key: 0 for key in spec.score_component_keys}


def _create_squat_analyzer(*, fps: float = 30.0) -> Any:
    return create_squat_analyzer(fps=fps)


def _create_pushup_analyzer(*, fps: float = 30.0) -> Any:
    # fps accepted for uniform factory signature; push-up analyzer ignores it.
    _ = fps
    return create_pushup_analyzer()


def _process_squat_frame(
    analyzer: Any,
    landmarks: object,
    pose_landmarks_enum: object,
    image_width: int,
    image_height: int,
    **kwargs: Any,
) -> dict[str, Any]:
    return process_squat_frame(
        analyzer,
        landmarks,
        pose_landmarks_enum,
        image_width,
        image_height,
        **kwargs,
    )


def _process_pushup_frame(
    analyzer: Any,
    landmarks: object,
    pose_landmarks_enum: object,
    image_width: int,
    image_height: int,
    **kwargs: Any,
) -> dict[str, Any]:
    _ = pose_landmarks_enum
    # last_analysis / effective_fps are squat-oriented; ignore if present.
    kwargs.pop("last_analysis", None)
    kwargs.pop("world_landmarks", None)
    kwargs.pop("effective_fps", None)
    out = process_pushup_frame(
        analyzer,
        landmarks,
        image_width,
        image_height,
        **kwargs,
    )
    out.setdefault("selected_side", None)
    out.setdefault("biomechanics", None)
    return out


def _register_builtin_exercises() -> None:
    """Register squat and push-up (existing production analyzers)."""
    if _REGISTRY:
        return
    register_exercise(
        ExerciseSpec(
            key="squat",
            display_name="squat",
            aliases=frozenset({"squat"}),
            create_analyzer=_create_squat_analyzer,
            get_landmark_indices=squat_pose_landmark_indices,
            process_frame=_process_squat_frame,
            score_component_keys=tuple(SQUAT_SCORE_COMPONENT_KEYS),
        )
    )
    register_exercise(
        ExerciseSpec(
            key="pushup",
            display_name="push-up",
            aliases=frozenset({"pushup", "push-up", "push_up", "push up"}),
            create_analyzer=_create_pushup_analyzer,
            get_landmark_indices=pushup_pose_landmark_indices,
            process_frame=_process_pushup_frame,
            score_component_keys=tuple(PUSHUP_SCORE_COMPONENT_KEYS),
        )
    )


_register_builtin_exercises()


def _reset_registry_for_tests() -> None:
    """Test helper: clear and re-register builtins."""
    _REGISTRY.clear()
    _ALIAS_TO_KEY.clear()
    _register_builtin_exercises()


__all__ = [
    "ExerciseSpec",
    "UnsupportedExerciseError",
    "cli_exercise_choices",
    "create_analyzer_for_exercise",
    "default_score_components",
    "display_exercise_name",
    "get_exercise_spec",
    "normalize_exercise_type",
    "register_exercise",
    "registered_exercise_keys",
    "validate_exercise_type",
]
