"""Shared successful / failed / total rep summary helpers.

Derives counters from canonical rep_history entries (``valid`` flag).
Does not redefine movement validity — analyzers remain the source of attempt
recording. Counters are always non-negative and satisfy:

    total_reps == successful_reps + failed_reps
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RepSummary:
    """Video-level rep attempt statistics."""

    successful_reps: int = 0
    failed_reps: int = 0
    total_reps: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("successful_reps", self.successful_reps),
            ("failed_reps", self.failed_reps),
            ("total_reps", self.total_reps),
        ):
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name} must be a non-negative int, got {value!r}")
        if self.total_reps != self.successful_reps + self.failed_reps:
            raise ValueError(
                "total_reps must equal successful_reps + failed_reps "
                f"({self.total_reps} != {self.successful_reps} + {self.failed_reps})"
            )

    def as_dict(self) -> dict[str, int]:
        return {
            "successful_reps": self.successful_reps,
            "failed_reps": self.failed_reps,
            "total_reps": self.total_reps,
        }


def summarize_rep_history(
    rep_history: Sequence[Mapping[str, Any]] | None,
) -> RepSummary:
    """Build summary from recorded attempts in rep_history.

    Each history entry is one physical attempt finalized by the analyzer.
    ``valid=True`` → successful; otherwise → failed.
    """
    if not rep_history:
        return RepSummary(successful_reps=0, failed_reps=0, total_reps=0)

    successful = 0
    failed = 0
    for entry in rep_history:
        if bool(entry.get("valid")):
            successful += 1
        else:
            failed += 1
    return RepSummary(
        successful_reps=successful,
        failed_reps=failed,
        total_reps=successful + failed,
    )


def summarize_rep_counters(
    *,
    successful_reps: int,
    failed_reps: int,
) -> RepSummary:
    """Build summary from explicit successful/failed counters."""
    return RepSummary(
        successful_reps=int(successful_reps),
        failed_reps=int(failed_reps),
        total_reps=int(successful_reps) + int(failed_reps),
    )
