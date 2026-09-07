"""Shared feedback priority infrastructure for squat and push-up analysis.

Provides stable feedback codes, human-readable messages, an internal 0–100
importance rank, semantic severity (CRITICAL / MEDIUM / SUGGESTION) derived
from importance, code-based deduplication, and top-N selection of unique
correction feedback.

Does not change when feedback is produced — only how produced feedback can be
ranked, classified, deduplicated, and prioritized.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from camera_utils import CAMERA_FEEDBACK_MESSAGES
from pushup_analyzer import (
    FORM_FEEDBACK_MESSAGES,
    FORM_MSG_ANGLE_NOT_DETECTED,
    FORM_MSG_GOOD_FORM,
    FORM_MSG_LOW_CONFIDENCE,
    FORM_MSG_NO_COMPLETE,
)
from squat_analyzer import ERROR_MESSAGES
from visibility_utils import VISIBILITY_WARNING, VISIBILITY_WARNING_HINT

IMPORTANCE_MIN = 0
IMPORTANCE_MAX = 100

# Unknown / unmapped codes must not silently become high-priority.
DEFAULT_UNKNOWN_IMPORTANCE = 40

# Importance → severity thresholds (inclusive lower bounds).
# Chosen from FEEDBACK_IMPORTANCE distribution:
#   ≥80: analysis reliability + incomplete/invalid movement
#   ≥50: notable form issues while movement may still complete
#   <50: positive / ready / unknown-default suggestions
CRITICAL_MIN_IMPORTANCE = 80
MEDIUM_MIN_IMPORTANCE = 50


class FeedbackSeverity(str, Enum):
    """Semantic feedback priority levels (not medical risk claims)."""

    CRITICAL = "critical"
    MEDIUM = "medium"
    SUGGESTION = "suggestion"


# Positive / ready messages used by analyzers (keep exact text).
SQUAT_MSG_GOOD_DEPTH = "Squat derinligi iyi."
SQUAT_MSG_READY = "Squat icin hazir pozisyondasin."
SQUAT_MSG_LANDMARKS_UNCLEAR = (
    "Kamera acisini duzelt, vucut noktalari net gorunmuyor."
)


# ---------------------------------------------------------------------------
# Stable feedback codes (machine-readable)
# ---------------------------------------------------------------------------
class FeedbackCode:
    """Stable string codes for feedback types across exercises."""

    # Analysis reliability
    LOW_VISIBILITY = "LOW_VISIBILITY"
    LOW_VISIBILITY_HINT = "LOW_VISIBILITY_HINT"
    CAMERA_TOO_CLOSE = "CAMERA_TOO_CLOSE"
    CAMERA_TOO_FAR = "CAMERA_TOO_FAR"
    SQUAT_LANDMARKS_UNCLEAR = "SQUAT_LANDMARKS_UNCLEAR"
    PUSHUP_LOW_CONFIDENCE = "PUSHUP_LOW_CONFIDENCE"
    PUSHUP_ANGLE_NOT_DETECTED = "PUSHUP_ANGLE_NOT_DETECTED"

    # Squat form / lifecycle
    SQUAT_INSUFFICIENT_DEPTH = "SQUAT_INSUFFICIENT_DEPTH"
    SQUAT_DEPTH_REACH = "SQUAT_DEPTH_REACH"
    SQUAT_KNEE_ANGLE_INSUFFICIENT = "SQUAT_KNEE_ANGLE_INSUFFICIENT"
    SQUAT_TOO_DEEP_OR_UNSTABLE = "SQUAT_TOO_DEEP_OR_UNSTABLE"
    SQUAT_TOO_FAST = "SQUAT_TOO_FAST"
    SQUAT_INCOMPLETE_REP = "SQUAT_INCOMPLETE_REP"
    SQUAT_TORSO_LEAN = "SQUAT_TORSO_LEAN"
    SQUAT_EXCESSIVE_FORWARD_LEAN = "SQUAT_EXCESSIVE_FORWARD_LEAN"
    SQUAT_HIP_FLEXION_MISMATCH = "SQUAT_HIP_FLEXION_MISMATCH"
    SQUAT_GOOD_DEPTH = "SQUAT_GOOD_DEPTH"
    SQUAT_READY = "SQUAT_READY"

    # Push-up form / lifecycle
    PUSHUP_HIPS_SAGGING = "PUSHUP_HIPS_SAGGING"
    PUSHUP_HIPS_TOO_HIGH = "PUSHUP_HIPS_TOO_HIGH"
    PUSHUP_BACK_BENT = "PUSHUP_BACK_BENT"
    PUSHUP_NOT_LOW_ENOUGH = "PUSHUP_NOT_LOW_ENOUGH"
    PUSHUP_INCOMPLETE_UP = "PUSHUP_INCOMPLETE_UP"
    PUSHUP_ELBOWS_FLARED = "PUSHUP_ELBOWS_FLARED"
    PUSHUP_SHOULDER_ALIGNMENT = "PUSHUP_SHOULDER_ALIGNMENT"
    PUSHUP_NO_COMPLETE = "PUSHUP_NO_COMPLETE"
    PUSHUP_GOOD_FORM = "PUSHUP_GOOD_FORM"


# Analyzer-native error/issue keys → stable FeedbackCode
ANALYZER_KEY_TO_CODE: dict[str, str] = {
    # Squat ERROR_MESSAGES keys
    "insufficient_depth": FeedbackCode.SQUAT_INSUFFICIENT_DEPTH,
    "squat_depth_reach": FeedbackCode.SQUAT_DEPTH_REACH,
    "knee_angle_insufficient": FeedbackCode.SQUAT_KNEE_ANGLE_INSUFFICIENT,
    "too_deep_or_unstable": FeedbackCode.SQUAT_TOO_DEEP_OR_UNSTABLE,
    "too_fast": FeedbackCode.SQUAT_TOO_FAST,
    "incomplete_rep": FeedbackCode.SQUAT_INCOMPLETE_REP,
    "torso_lean": FeedbackCode.SQUAT_TORSO_LEAN,
    "excessive_forward_lean": FeedbackCode.SQUAT_EXCESSIVE_FORWARD_LEAN,
    "hip_flexion_mismatch": FeedbackCode.SQUAT_HIP_FLEXION_MISMATCH,
    # Push-up issue / incomplete keys
    "hips_sagging": FeedbackCode.PUSHUP_HIPS_SAGGING,
    "hips_too_high": FeedbackCode.PUSHUP_HIPS_TOO_HIGH,
    "back_bent": FeedbackCode.PUSHUP_BACK_BENT,
    "not_low_enough": FeedbackCode.PUSHUP_NOT_LOW_ENOUGH,
    "incomplete_up": FeedbackCode.PUSHUP_INCOMPLETE_UP,
    "elbows_flared": FeedbackCode.PUSHUP_ELBOWS_FLARED,
    "shoulder_alignment_issue": FeedbackCode.PUSHUP_SHOULDER_ALIGNMENT,
    # Camera status keys
    "too_close": FeedbackCode.CAMERA_TOO_CLOSE,
    "too_far": FeedbackCode.CAMERA_TOO_FAR,
}

# Central importance source-of-truth (0–100). Higher = more serious.
FEEDBACK_IMPORTANCE: dict[str, int] = {
    # Reliability blockers — analysis may be unusable
    FeedbackCode.LOW_VISIBILITY: 95,
    FeedbackCode.LOW_VISIBILITY_HINT: 90,
    FeedbackCode.SQUAT_LANDMARKS_UNCLEAR: 93,
    FeedbackCode.CAMERA_TOO_CLOSE: 92,
    FeedbackCode.CAMERA_TOO_FAR: 92,
    FeedbackCode.PUSHUP_ANGLE_NOT_DETECTED: 88,
    FeedbackCode.PUSHUP_LOW_CONFIDENCE: 86,
    # Incomplete / validity-breaking movement
    FeedbackCode.SQUAT_INCOMPLETE_REP: 85,
    FeedbackCode.PUSHUP_NOT_LOW_ENOUGH: 85,
    FeedbackCode.PUSHUP_INCOMPLETE_UP: 84,
    FeedbackCode.PUSHUP_NO_COMPLETE: 83,
    FeedbackCode.SQUAT_INSUFFICIENT_DEPTH: 82,
    FeedbackCode.SQUAT_DEPTH_REACH: 82,
    FeedbackCode.SQUAT_KNEE_ANGLE_INSUFFICIENT: 80,
    # Serious form issues
    FeedbackCode.SQUAT_TOO_DEEP_OR_UNSTABLE: 78,
    FeedbackCode.PUSHUP_HIPS_SAGGING: 78,
    FeedbackCode.PUSHUP_BACK_BENT: 76,
    FeedbackCode.SQUAT_TORSO_LEAN: 75,
    FeedbackCode.SQUAT_EXCESSIVE_FORWARD_LEAN: 75,
    FeedbackCode.PUSHUP_HIPS_TOO_HIGH: 74,
    FeedbackCode.SQUAT_HIP_FLEXION_MISMATCH: 68,
    FeedbackCode.SQUAT_TOO_FAST: 65,
    FeedbackCode.PUSHUP_ELBOWS_FLARED: 62,
    FeedbackCode.PUSHUP_SHOULDER_ALIGNMENT: 60,
    # Positive / ready (low priority)
    FeedbackCode.SQUAT_GOOD_DEPTH: 20,
    FeedbackCode.PUSHUP_GOOD_FORM: 20,
    FeedbackCode.SQUAT_READY: 15,
}


def _build_code_messages() -> dict[str, str]:
    """Canonical code → existing analyzer message text."""
    messages: dict[str, str] = {
        FeedbackCode.LOW_VISIBILITY: VISIBILITY_WARNING,
        FeedbackCode.LOW_VISIBILITY_HINT: VISIBILITY_WARNING_HINT,
        FeedbackCode.CAMERA_TOO_CLOSE: CAMERA_FEEDBACK_MESSAGES["too_close"],
        FeedbackCode.CAMERA_TOO_FAR: CAMERA_FEEDBACK_MESSAGES["too_far"],
        FeedbackCode.SQUAT_LANDMARKS_UNCLEAR: SQUAT_MSG_LANDMARKS_UNCLEAR,
        FeedbackCode.SQUAT_GOOD_DEPTH: SQUAT_MSG_GOOD_DEPTH,
        FeedbackCode.SQUAT_READY: SQUAT_MSG_READY,
        FeedbackCode.PUSHUP_GOOD_FORM: FORM_MSG_GOOD_FORM,
        FeedbackCode.PUSHUP_NO_COMPLETE: FORM_MSG_NO_COMPLETE,
        FeedbackCode.PUSHUP_LOW_CONFIDENCE: FORM_MSG_LOW_CONFIDENCE,
        FeedbackCode.PUSHUP_ANGLE_NOT_DETECTED: FORM_MSG_ANGLE_NOT_DETECTED,
    }
    for analyzer_key, code in ANALYZER_KEY_TO_CODE.items():
        if analyzer_key in ERROR_MESSAGES:
            messages[code] = ERROR_MESSAGES[analyzer_key]
        elif analyzer_key in FORM_FEEDBACK_MESSAGES:
            messages[code] = FORM_FEEDBACK_MESSAGES[analyzer_key]
        elif analyzer_key in CAMERA_FEEDBACK_MESSAGES:
            messages[code] = CAMERA_FEEDBACK_MESSAGES[analyzer_key]
    return messages


FEEDBACK_MESSAGES: dict[str, str] = _build_code_messages()

_MESSAGE_TO_CODE: dict[str, str] = {
    message: code for code, message in FEEDBACK_MESSAGES.items()
}


def _validate_importance_value(value: int, *, context: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{context} must be an int in [{IMPORTANCE_MIN}, {IMPORTANCE_MAX}]")
    if value < IMPORTANCE_MIN or value > IMPORTANCE_MAX:
        raise ValueError(
            f"{context} must be in [{IMPORTANCE_MIN}, {IMPORTANCE_MAX}], got {value}"
        )
    return value


def _assert_mapping_valid() -> None:
    for code, importance in FEEDBACK_IMPORTANCE.items():
        _validate_importance_value(importance, context=f"FEEDBACK_IMPORTANCE['{code}']")
        if code not in FEEDBACK_MESSAGES:
            raise ValueError(f"FEEDBACK_IMPORTANCE has unknown code without message: {code}")


_assert_mapping_valid()


def severity_from_importance(importance: int) -> FeedbackSeverity:
    """Map a validated 0–100 importance value to semantic severity.

    Rules (inclusive lower bounds):
      importance >= CRITICAL_MIN_IMPORTANCE → CRITICAL
      importance >= MEDIUM_MIN_IMPORTANCE   → MEDIUM
      otherwise                            → SUGGESTION
    """
    value = _validate_importance_value(importance, context="importance")
    if value >= CRITICAL_MIN_IMPORTANCE:
        return FeedbackSeverity.CRITICAL
    if value >= MEDIUM_MIN_IMPORTANCE:
        return FeedbackSeverity.MEDIUM
    return FeedbackSeverity.SUGGESTION


@dataclass(frozen=True)
class FeedbackItem:
    """Structured feedback with code, message, importance, and derived severity."""

    code: str
    message: str
    importance: int

    def __post_init__(self) -> None:
        _validate_importance_value(self.importance, context="importance")

    @property
    def severity(self) -> FeedbackSeverity:
        return severity_from_importance(self.importance)

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "importance": self.importance,
            "severity": self.severity.value,
        }


def normalize_feedback_code(code_or_key: str) -> str:
    """Map analyzer-native keys or stable codes to a stable FeedbackCode string."""
    raw = str(code_or_key or "").strip()
    if not raw:
        raise ValueError("feedback code must be a non-empty string")
    if raw in FEEDBACK_IMPORTANCE or raw in FEEDBACK_MESSAGES:
        return raw
    mapped = ANALYZER_KEY_TO_CODE.get(raw)
    if mapped is not None:
        return mapped
    return raw


def importance_for_code(code_or_key: str) -> int:
    """Return mapped importance, or DEFAULT_UNKNOWN_IMPORTANCE for unknowns."""
    code = normalize_feedback_code(code_or_key)
    return int(FEEDBACK_IMPORTANCE.get(code, DEFAULT_UNKNOWN_IMPORTANCE))


def message_for_code(code_or_key: str, *, fallback_message: str | None = None) -> str:
    code = normalize_feedback_code(code_or_key)
    if code in FEEDBACK_MESSAGES:
        return FEEDBACK_MESSAGES[code]
    if fallback_message:
        return str(fallback_message)
    return code


def resolve_code_from_message(message: str) -> str | None:
    """Reverse-lookup stable code from an exact existing message string."""
    if not message:
        return None
    return _MESSAGE_TO_CODE.get(str(message))


def make_feedback_item(
    code_or_key: str,
    *,
    message: str | None = None,
    importance: int | None = None,
) -> FeedbackItem:
    """Build a FeedbackItem from an analyzer key or stable code."""
    code = normalize_feedback_code(code_or_key)
    resolved_message = message if message is not None else message_for_code(code)
    if importance is None:
        resolved_importance = importance_for_code(code)
    else:
        resolved_importance = _validate_importance_value(
            importance, context="importance"
        )
    return FeedbackItem(
        code=code,
        message=str(resolved_message),
        importance=resolved_importance,
    )


def feedback_item_from_message(message: str) -> FeedbackItem:
    """Build an item from a human message, resolving code when known."""
    text = str(message or "")
    code = resolve_code_from_message(text)
    if code is None:
        return FeedbackItem(
            code="UNKNOWN_FEEDBACK",
            message=text,
            importance=DEFAULT_UNKNOWN_IMPORTANCE,
        )
    return make_feedback_item(code, message=text)


def sort_feedback_items(
    items: Sequence[FeedbackItem],
) -> list[FeedbackItem]:
    """Sort by importance descending, then code ascending (deterministic)."""
    return sorted(
        items,
        key=lambda item: (-int(item.importance), str(item.code), str(item.message)),
    )


def deduplicate_feedback(
    items: Sequence[FeedbackItem],
    *,
    sort: bool = True,
) -> list[FeedbackItem]:
    """Collapse items sharing the same feedback code.

    Rules:
      - Primary key: FeedbackItem.code
      - Higher importance wins
      - Equal importance: first occurrence wins (stable)
      - Different codes are never merged (even with identical messages)
      - Optional importance-based sort after dedupe (default True)

    Does not mutate the input sequence.
    """
    if not items:
        return []

    best_by_code: dict[str, FeedbackItem] = {}
    first_seen_order: list[str] = []

    for item in items:
        code = str(item.code)
        existing = best_by_code.get(code)
        if existing is None:
            best_by_code[code] = item
            first_seen_order.append(code)
            continue
        if int(item.importance) > int(existing.importance):
            best_by_code[code] = item

    unique = [best_by_code[code] for code in first_seen_order]
    if sort:
        return sort_feedback_items(unique)
    return unique


# Default number of highest-priority unique feedback items for user focus.
DEFAULT_TOP_FEEDBACK_LIMIT = 3

# Positive / ready messages are not technical correction targets for top-N.
POSITIVE_FEEDBACK_CODES: frozenset[str] = frozenset(
    {
        FeedbackCode.SQUAT_GOOD_DEPTH,
        FeedbackCode.SQUAT_READY,
        FeedbackCode.PUSHUP_GOOD_FORM,
    }
)


def select_top_feedback(
    items: Sequence[FeedbackItem],
    limit: int = DEFAULT_TOP_FEEDBACK_LIMIT,
    *,
    deduplicate: bool = True,
    exclude_positive: bool = True,
) -> list[FeedbackItem]:
    """Select the highest-importance unique feedback items.

    Pipeline assumptions:
      - Prefer calling after structured conversion
      - Deduplicates by feedback code when ``deduplicate`` is True (default)
      - Orders via existing ``sort_feedback_items`` (importance desc, code asc)
      - Does not mutate ``items``
      - Does not invent placeholder items when fewer than ``limit`` exist

    Raises ValueError when ``limit`` is negative or not an int.
    """
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError("limit must be a non-negative int")
    if limit < 0:
        raise ValueError(f"limit must be >= 0, got {limit}")
    if limit == 0 or not items:
        return []

    working: list[FeedbackItem]
    if deduplicate:
        working = deduplicate_feedback(items, sort=False)
    else:
        working = list(items)

    if exclude_positive:
        working = [item for item in working if item.code not in POSITIVE_FEEDBACK_CODES]

    ordered = sort_feedback_items(working)
    return ordered[:limit]


def messages_from_items(items: Sequence[FeedbackItem]) -> list[str]:
    """Legacy/public list[str] representation derived from structured items."""
    return [item.message for item in items if item.message]


def build_feedback_items(
    *,
    codes: Iterable[str] | None = None,
    messages: Iterable[str] | None = None,
    sort: bool = True,
) -> list[FeedbackItem]:
    """Build structured items from analyzer codes and/or message strings.

    Collects candidates then applies code-based deduplication. When ``sort`` is
    True (default), result is importance-descending after dedupe.
    """
    items: list[FeedbackItem] = []

    for raw_code in codes or ():
        if not raw_code:
            continue
        items.append(make_feedback_item(str(raw_code)))

    for raw_message in messages or ():
        if not raw_message:
            continue
        items.append(feedback_item_from_message(str(raw_message)))

    return deduplicate_feedback(items, sort=sort)


def feedback_items_as_dicts(items: Sequence[FeedbackItem]) -> list[dict[str, Any]]:
    return [item.as_dict() for item in items]


def build_feedback_payload(
    *,
    codes: Iterable[str] | None = None,
    messages: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Internal payload: full unique items, top-N, and legacy message list."""
    items = build_feedback_items(codes=codes, messages=messages, sort=True)
    top = select_top_feedback(items, DEFAULT_TOP_FEEDBACK_LIMIT)
    return {
        "feedback_items": feedback_items_as_dicts(items),
        "top_feedback": feedback_items_as_dicts(top),
        "feedback": messages_from_items(items),
    }
