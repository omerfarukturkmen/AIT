"""Squat exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

import statistics
from collections import deque
from typing import Any

# --- Hysteresis knee-angle thresholds (degrees) ---
STANDING_ENTER = 155.0
STANDING_EXIT = 145.0
BOTTOM_ENTER = 100.0
BOTTOM_EXIT = 115.0
VALID_DEPTH_ANGLE = 100.0
INSUFFICIENT_DEPTH_ANGLE = 100.0
TOO_DEEP_KNEE_ANGLE = 55.0

# End-of-video completion (finished ascent without full state confirm)
FINALIZE_RETURN_ANGLE = 150.0
FINALIZE_MIN_RISE_FROM_BOTTOM = 25.0

# Filter: short median + EMA (lower lag than 7-frame MA)
MEDIAN_WINDOW = 3
EMA_ALPHA = 0.42
DIRECTION_DEADZONE = 0.8  # deg / frame on smoothed signal

# State confirmation
CONFIRM_FRAMES = 2
STANDING_FRAMES_TO_ARM = 3

# Form errors
TORSO_LEAN_THRESHOLD = 38.0
TORSO_LEAN_CONFIRM_FRAMES = 4
FAST_DEG_PER_SEC = 220.0
FAST_CONFIRM_FRAMES = 3
MAX_SINGLE_FRAME_JUMP = 35.0  # ignore landmark spikes

ERROR_MESSAGES: dict[str, str] = {
    "insufficient_depth": "Daha derine inmelisin.",
    "knee_angle_insufficient": "Diz acin yeterli seviyeye ulasmadi.",
    "too_deep_or_unstable": "Diz acin cok dar, hareketi kontrollu yapmalisin.",
    "too_fast": "Hareketi daha kontrollu yapmalisin.",
    "incomplete_rep": "Squat tekrarin tamamlanmadi.",
    "torso_lean": "Ust govdeni fazla one egme.",
}


class SquatAnalyzer:
    """Rep counter with hysteresis states and low-lag knee filtering."""

    def __init__(self, fps: float = 30.0) -> None:
        self.fps: float = fps if fps and fps > 1e-3 else 30.0

        self.rep_count: int = 0
        self.valid_reps: int = 0
        self.invalid_reps: int = 0
        self.current_state: str = "unknown"
        self.depth_valid: bool = False
        self.previous_state: str = "unknown"
        self.frame_index: int = 0
        self.feedback: list[str] = []
        self.errors: list[str] = []
        self.form_status: str = "good"

        self.min_knee_angle_current_rep: float | None = None
        self.last_rep: dict[str, Any] = {
            "depthStatus": None,
            "minKneeAngle": None,
            "depthValid": None,
            "errors": [],
            "feedback": [],
        }
        self.last_depth_status: str = "unknown"
        self.rep_history: list[dict[str, Any]] = []

        self._median_buf: deque[float] = deque(maxlen=MEDIAN_WINDOW)
        self._angle_history: deque[float] = deque(maxlen=12)
        self._raw_history: deque[float] = deque(maxlen=8)
        self._smoothed_average: float | None = None
        self._prev_smoothed: float | None = None
        self._direction: float = 0.0
        self._last_raw_knee: float | None = None
        self._last_return_angle: float | None = None

        self._candidate_state: str = "unknown"
        self._candidate_state_count: int = 0
        self._confirmed_state: str = "unknown"
        self._last_frame_confirmed_state: str = "unknown"

        self.frames_in_standing: int = 0
        self.ready_for_squat: bool = False
        self.in_rep_attempt: bool = False
        self.descent_started: bool = False
        self._reached_valid_depth: bool = False
        self._ascending_after_depth: bool = False

        self._rep_start_frame: int | None = None
        self._rep_bottom_frame: int | None = None
        self._session_max_knee: float | None = None
        self._session_min_knee: float | None = None
        self._selected_side: str = "unavailable"

        self._session_errors: list[str] = []
        self._rep_errors: list[str] = []
        self._session_feedback: list[str] = []

        self._torso_lean_streak: int = 0
        self._too_fast_streak: int = 0
        self._torso_lean_latched: bool = False
        self._too_fast_latched: bool = False

        self._last_left_knee: float | None = None
        self._last_right_knee: float | None = None
        self._last_smoothed_knee: float | None = None

    def _update_smoothed(self, raw_average: float | None) -> float | None:
        if raw_average is None:
            return self._smoothed_average

        raw = float(raw_average)
        self._last_raw_knee = raw
        self._raw_history.append(raw)
        self._median_buf.append(raw)
        median = float(statistics.median(self._median_buf))

        if self._smoothed_average is None:
            self._smoothed_average = median
        else:
            self._smoothed_average = (
                EMA_ALPHA * median + (1.0 - EMA_ALPHA) * self._smoothed_average
            )

        self._angle_history.append(self._smoothed_average)

        if self._prev_smoothed is not None:
            delta = self._smoothed_average - self._prev_smoothed
            if abs(delta) >= DIRECTION_DEADZONE:
                self._direction = delta
        return self._smoothed_average

    def _short_median(self) -> float | None:
        if not self._raw_history:
            return None
        window = list(self._raw_history)[-3:]
        return float(statistics.median(window))

    def _measure_state(self, angle: float) -> str:
        """Propose next state using hysteresis + movement direction."""
        direction = self._direction
        state = self._confirmed_state

        if state == "unknown":
            if angle >= STANDING_ENTER:
                return "standing"
            if angle <= BOTTOM_ENTER:
                return "bottom"
            if direction < -DIRECTION_DEADZONE:
                return "descending"
            if direction > DIRECTION_DEADZONE:
                return "ascending"
            return "unknown"

        if state == "standing":
            if angle < STANDING_EXIT:
                if angle <= BOTTOM_ENTER:
                    return "bottom"
                return "descending"
            return "standing"

        if state == "descending":
            if angle <= BOTTOM_ENTER:
                return "bottom"
            if angle >= STANDING_ENTER and direction >= 0:
                return "standing"
            if direction > DIRECTION_DEADZONE and angle > BOTTOM_EXIT:
                return "ascending"
            return "descending"

        if state == "bottom":
            if angle > BOTTOM_EXIT and direction > DIRECTION_DEADZONE:
                return "ascending"
            if angle <= BOTTOM_ENTER:
                return "bottom"
            if direction > DIRECTION_DEADZONE:
                return "ascending"
            if direction < -DIRECTION_DEADZONE:
                return "descending"
            return "bottom"

        if state == "ascending":
            if angle >= STANDING_ENTER:
                return "standing"
            if angle <= BOTTOM_ENTER:
                return "bottom"
            if direction < -DIRECTION_DEADZONE and angle < STANDING_EXIT:
                return "descending"
            return "ascending"

        return state

    def _run_state_confirmation(self, measured: str) -> None:
        if measured == self._candidate_state:
            self._candidate_state_count += 1
        else:
            self._candidate_state = measured
            self._candidate_state_count = 1
        if self._candidate_state_count >= CONFIRM_FRAMES:
            self._confirmed_state = self._candidate_state

    def _reset_rep_attempt(self) -> None:
        self.in_rep_attempt = False
        self.descent_started = False
        self.min_knee_angle_current_rep = None
        self._reached_valid_depth = False
        self._ascending_after_depth = False
        self._rep_start_frame = None
        self._rep_bottom_frame = None
        self._rep_errors = []
        self._torso_lean_streak = 0
        self._too_fast_streak = 0
        self._torso_lean_latched = False
        self._too_fast_latched = False

    def _unique_append(self, bucket: list[str], code: str) -> None:
        if code not in bucket:
            bucket.append(code)

    def _register_error(self, code: str, *, rep_scope: bool = True) -> None:
        self._unique_append(self._session_errors, code)
        if rep_scope:
            self._unique_append(self._rep_errors, code)

    def _errors_to_feedback(self, codes: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for code in codes:
            msg = ERROR_MESSAGES.get(code)
            if msg and msg not in seen:
                seen.add(msg)
                out.append(msg)
        return out

    def _compute_form_status(self, error_codes: list[str]) -> str:
        if self.invalid_reps > self.valid_reps:
            return "poor"
        if not error_codes:
            return "good"
        if len(error_codes) >= 3:
            return "poor"
        return "needs_improvement"

    def _check_in_rep_form(
        self,
        smoothed: float,
        torso_lean: float | None,
    ) -> None:
        if not self.in_rep_attempt:
            return

        if self._prev_smoothed is not None:
            frame_delta = abs(float(smoothed) - self._prev_smoothed)
            if frame_delta <= MAX_SINGLE_FRAME_JUMP:
                deg_per_sec = frame_delta * self.fps
                if deg_per_sec >= FAST_DEG_PER_SEC:
                    self._too_fast_streak += 1
                else:
                    self._too_fast_streak = 0
                if (
                    self._too_fast_streak >= FAST_CONFIRM_FRAMES
                    and not self._too_fast_latched
                ):
                    self._register_error("too_fast")
                    self._too_fast_latched = True
            else:
                self._too_fast_streak = 0

        if float(smoothed) < TOO_DEEP_KNEE_ANGLE and self._confirmed_state == "bottom":
            self._register_error("too_deep_or_unstable")

        if torso_lean is not None and torso_lean >= TORSO_LEAN_THRESHOLD:
            self._torso_lean_streak += 1
        else:
            self._torso_lean_streak = 0
        if (
            self._torso_lean_streak >= TORSO_LEAN_CONFIRM_FRAMES
            and not self._torso_lean_latched
        ):
            self._register_error("torso_lean")
            self._torso_lean_latched = True

    def _finalize_rep_errors(self, min_angle: float | None) -> None:
        if min_angle is None:
            if self.descent_started:
                self._register_error("incomplete_rep")
            return
        if min_angle >= INSUFFICIENT_DEPTH_ANGLE:
            self._register_error("insufficient_depth")
            self._register_error("knee_angle_insufficient")
        if min_angle < TOO_DEEP_KNEE_ANGLE:
            self._register_error("too_deep_or_unstable")

    def _append_rep_history(
        self,
        *,
        valid: bool,
        min_angle: float | None,
        return_angle: float | None,
        messages: list[str],
    ) -> None:
        start = self._rep_start_frame or self.frame_index
        end = self.frame_index
        duration = (end - start + 1) / self.fps if self.fps > 0 else 0.0
        self.rep_history.append(
            {
                "rep_index": len(self.rep_history) + 1,
                "start_frame": start,
                "bottom_frame": self._rep_bottom_frame,
                "end_frame": end,
                "min_knee_angle": round(min_angle, 2) if min_angle is not None else None,
                "return_knee_angle": (
                    round(return_angle, 2) if return_angle is not None else None
                ),
                "valid": valid,
                "errors": list(self._rep_errors),
                "feedback": list(messages),
                "duration_seconds": round(duration, 3),
            }
        )

    def _complete_rep(self, *, return_angle: float | None = None) -> list[str]:
        min_angle = self.min_knee_angle_current_rep
        if return_angle is None:
            return_angle = self._smoothed_average
        self._last_return_angle = return_angle
        messages: list[str] = []
        valid = False

        if min_angle is not None and min_angle < VALID_DEPTH_ANGLE:
            valid = True
            self.depth_valid = True
            self.last_depth_status = "good_depth"
            if not self._rep_errors:
                messages = ["Squat derinligi iyi."]
        elif self.descent_started and min_angle is not None and min_angle < BOTTOM_EXIT:
            self.depth_valid = False
            self.last_depth_status = "too_shallow"
            self._finalize_rep_errors(min_angle)
            messages = self._errors_to_feedback(self._rep_errors)
        elif self.descent_started:
            self.depth_valid = False
            self.last_depth_status = "incomplete"
            self._register_error("incomplete_rep")
            messages = self._errors_to_feedback(self._rep_errors)
        else:
            self.depth_valid = False
            self._finalize_rep_errors(min_angle)

        if not messages and self._rep_errors:
            messages = self._errors_to_feedback(self._rep_errors)

        for msg in messages:
            if msg not in self._session_feedback:
                self._session_feedback.append(msg)

        self.last_rep = {
            "depthStatus": self.last_depth_status,
            "minKneeAngle": min_angle,
            "depthValid": self.depth_valid,
            "errors": list(self._rep_errors),
            "feedback": list(messages),
        }

        if self.descent_started and min_angle is not None:
            self._append_rep_history(
                valid=valid,
                min_angle=min_angle,
                return_angle=return_angle,
                messages=messages,
            )
            self.valid_reps = sum(1 for r in self.rep_history if r.get("valid"))
            self.invalid_reps = len(self.rep_history) - self.valid_reps
            self.rep_count = len(self.rep_history)

        self._reset_rep_attempt()
        self.ready_for_squat = False
        self.frames_in_standing = 0
        return messages

    def _sync_form_fields(self) -> None:
        self.errors = list(self._session_errors)
        self.form_status = self._compute_form_status(self.errors)

    def _sanitize_session_errors(self) -> None:
        if "too_deep_or_unstable" not in self._session_errors:
            return
        mins = [
            r.get("min_knee_angle")
            for r in self.rep_history
            if r.get("min_knee_angle") is not None
        ]
        ever_too_deep = any(float(m) < TOO_DEEP_KNEE_ANGLE for m in mins)
        if not ever_too_deep:
            self._session_errors = [
                e for e in self._session_errors if e != "too_deep_or_unstable"
            ]
            too_deep_msg = ERROR_MESSAGES.get("too_deep_or_unstable")
            if too_deep_msg:
                self._session_feedback = [
                    m for m in self._session_feedback if m != too_deep_msg
                ]

    def _can_finalize_active_rep(self) -> bool:
        if not self.in_rep_attempt or not self._reached_valid_depth:
            return False
        if self.min_knee_angle_current_rep is None:
            return False

        smoothed = self._smoothed_average
        if smoothed is None:
            return False

        rise = float(smoothed) - float(self.min_knee_angle_current_rep)
        if rise < FINALIZE_MIN_RISE_FROM_BOTTOM:
            return False

        ascending = (
            self._confirmed_state in ("ascending", "standing")
            or self._direction > DIRECTION_DEADZONE
            or self._ascending_after_depth
        )
        if not ascending:
            return False

        candidates = [
            v
            for v in (smoothed, self._last_raw_knee, self._short_median())
            if v is not None
        ]
        if not candidates:
            return False
        return max(float(v) for v in candidates) >= FINALIZE_RETURN_ANGLE

    def finalize_session(self) -> None:
        """Complete a near-finished last rep; never invent mid-ascent reps."""
        if self._can_finalize_active_rep():
            return_angle = max(
                float(v)
                for v in (
                    self._smoothed_average,
                    self._last_raw_knee,
                    self._short_median(),
                )
                if v is not None
            )
            self._complete_rep(return_angle=return_angle)
            self.current_state = "standing"
            self._confirmed_state = "standing"
        elif self.in_rep_attempt:
            if self.descent_started:
                self._register_error("incomplete_rep")
                msg = ERROR_MESSAGES["incomplete_rep"]
                if msg not in self._session_feedback:
                    self._session_feedback.append(msg)
            self._reset_rep_attempt()

        if (
            self._smoothed_average is not None
            and self._smoothed_average >= STANDING_ENTER
        ):
            self.current_state = "standing"
            self._confirmed_state = "standing"

        self._sanitize_session_errors()
        self._sync_form_fields()
        self.rep_count = len(self.rep_history)
        self.valid_reps = sum(1 for r in self.rep_history if r.get("valid"))
        self.invalid_reps = self.rep_count - self.valid_reps

    def _session_knee_stats(self) -> dict[str, float | None]:
        mins = [
            float(r["min_knee_angle"])
            for r in self.rep_history
            if r.get("min_knee_angle") is not None
        ]
        min_knee = min(mins) if mins else self._session_min_knee
        avg_min = (sum(mins) / len(mins)) if mins else None
        rom = None
        if self._session_max_knee is not None and min_knee is not None:
            rom = float(self._session_max_knee) - float(min_knee)
        return {
            "min_knee_angle": round(min_knee, 2) if min_knee is not None else None,
            "average_min_knee_angle": round(avg_min, 2) if avg_min is not None else None,
            "knee_range_of_motion": round(rom, 2) if rom is not None else None,
        }

    def get_result(self, video_path: str = "data/input/input.mp4") -> dict[str, Any]:
        from datetime import datetime

        self.finalize_session()
        stats = self._session_knee_stats()
        return {
            "exercise": "squat",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "form_status": self.form_status,
            "current_state": self.current_state,
            "depth_valid": self.depth_valid,
            "angles": {
                "left_knee_angle": self._last_left_knee,
                "right_knee_angle": self._last_right_knee,
                "smoothed_knee_angle": self._last_smoothed_knee,
            },
            "errors": list(self.errors),
            "feedback": list(self._session_feedback),
            "video_path": video_path,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rep_history": list(self.rep_history),
            "min_knee_angle": stats["min_knee_angle"],
            "average_min_knee_angle": stats["average_min_knee_angle"],
            "knee_range_of_motion": stats["knee_range_of_motion"],
            "selected_side": self._selected_side,
        }

    def _store_last_angles(
        self,
        left: float | None,
        right: float | None,
        smoothed: float | None,
    ) -> None:
        if left is not None:
            self._last_left_knee = float(left)
        if right is not None:
            self._last_right_knee = float(right)
        if smoothed is not None:
            self._last_smoothed_knee = float(smoothed)

    def _build_result(
        self,
        *,
        left: float | None,
        right: float | None,
        raw_average: float | None,
        smoothed: float | None,
        feedback: list[str],
        confidence: float,
        is_valid_pose: bool,
    ) -> dict[str, Any]:
        self._sync_form_fields()
        return {
            "exercise": "squat",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "total_reps": self.valid_reps + self.invalid_reps,
            "current_state": self.current_state,
            "depth_valid": self.depth_valid,
            "form_status": self.form_status,
            "errors": list(self.errors),
            "feedback": feedback,
            "angles": {
                "left_knee_angle": left,
                "right_knee_angle": right,
                "smoothed_knee_angle": smoothed,
            },
            "repCount": self.rep_count,
            "currentPhase": self.current_state,
            "kneeAngle": {
                "left": left,
                "right": right,
                "average": smoothed,
                "rawAverage": raw_average,
                "smoothedAverage": smoothed,
            },
            "depthStatus": self.last_depth_status,
            "confidence": confidence,
            "isValidPose": is_valid_pose,
            "selected_side": self._selected_side,
            "lastRep": {
                "depthStatus": self.last_rep.get("depthStatus"),
                "minKneeAngle": self.last_rep.get("minKneeAngle"),
                "depthValid": self.last_rep.get("depthValid"),
                "errors": list(self.last_rep.get("errors") or []),
                "feedback": list(self.last_rep.get("feedback") or []),
            },
        }

    def analyze_frame(
        self,
        knee_angles: dict[str, Any],
        pose_confidence: float | None = None,
        torso_lean: float | None = None,
        fps: float | None = None,
    ) -> dict[str, Any]:
        if fps is not None and fps > 1e-3:
            self.fps = float(fps)

        self.frame_index += 1

        left = knee_angles.get("left")
        right = knee_angles.get("right")
        raw_average = knee_angles.get("average")
        if knee_angles.get("selected_side"):
            self._selected_side = str(knee_angles["selected_side"])

        if raw_average is None and knee_angles.get("smoothedAverage") is not None:
            raw_average = knee_angles.get("rawAverage")
        smoothed_input = knee_angles.get("smoothedAverage")

        if raw_average is None and smoothed_input is None:
            self.previous_state = self._last_frame_confirmed_state
            self.current_state = self._confirmed_state
            feedback = [
                "Kamera acisini duzelt, vucut noktalari net gorunmuyor."
            ]
            self.feedback = feedback
            conf = float(pose_confidence) if pose_confidence is not None else 0.0
            return self._build_result(
                left=left,
                right=right,
                raw_average=None,
                smoothed=self._smoothed_average,
                feedback=feedback,
                confidence=conf,
                is_valid_pose=False,
            )

        if smoothed_input is not None:
            if raw_average is not None:
                self._update_smoothed(float(raw_average))
            smoothed = self._smoothed_average or float(smoothed_input)
        else:
            smoothed = self._update_smoothed(raw_average)

        if smoothed is None:
            feedback = [
                "Kamera acisini duzelt, vucut noktalari net gorunmuyor."
            ]
            self.feedback = feedback
            conf = float(pose_confidence) if pose_confidence is not None else 0.0
            return self._build_result(
                left=left,
                right=right,
                raw_average=raw_average,
                smoothed=None,
                feedback=feedback,
                confidence=conf,
                is_valid_pose=False,
            )

        if self._session_max_knee is None or smoothed > self._session_max_knee:
            self._session_max_knee = float(smoothed)
        if self._session_min_knee is None or smoothed < self._session_min_knee:
            self._session_min_knee = float(smoothed)

        prev_confirmed = self._last_frame_confirmed_state
        measured = self._measure_state(float(smoothed))
        self._run_state_confirmation(measured)
        confirmed = self._confirmed_state

        if confirmed == "standing":
            self.frames_in_standing += 1
            if self.frames_in_standing >= STANDING_FRAMES_TO_ARM:
                self.ready_for_squat = True
        else:
            self.frames_in_standing = 0

        rep_feedback: list[str] = []

        if (
            prev_confirmed == "standing"
            and confirmed in ("descending", "bottom")
            and self.ready_for_squat
            and not self.in_rep_attempt
        ):
            self.in_rep_attempt = True
            self.descent_started = True
            self.min_knee_angle_current_rep = float(smoothed)
            self._rep_start_frame = self.frame_index
            self._rep_errors = []
            self._reached_valid_depth = float(smoothed) < VALID_DEPTH_ANGLE
            self._torso_lean_latched = False
            self._too_fast_latched = False

        if self.in_rep_attempt:
            self.min_knee_angle_current_rep = min(
                self.min_knee_angle_current_rep or float(smoothed),
                float(smoothed),
            )
            if float(smoothed) < STANDING_EXIT:
                self.descent_started = True
            if float(smoothed) < VALID_DEPTH_ANGLE:
                self._reached_valid_depth = True
                self.depth_valid = True
                self._rep_bottom_frame = self.frame_index
            if self._reached_valid_depth and (
                confirmed == "ascending" or self._direction > DIRECTION_DEADZONE
            ):
                self._ascending_after_depth = True
            self._check_in_rep_form(float(smoothed), torso_lean)

        if (
            confirmed == "standing"
            and prev_confirmed != "standing"
            and self.in_rep_attempt
        ):
            rep_feedback = self._complete_rep(return_angle=float(smoothed))
        elif confirmed == "standing" and prev_confirmed != "standing":
            self._reset_rep_attempt()

        self._prev_smoothed = float(smoothed)
        self.previous_state = prev_confirmed
        self.current_state = confirmed
        self._last_frame_confirmed_state = confirmed

        feedback = list(rep_feedback)
        if not feedback and confirmed == "standing" and self.ready_for_squat:
            feedback = ["Squat icin hazir pozisyondasin."]

        self.feedback = feedback
        confidence = float(pose_confidence) if pose_confidence is not None else 1.0
        self._store_last_angles(left, right, smoothed)
        return self._build_result(
            left=left,
            right=right,
            raw_average=raw_average,
            smoothed=smoothed,
            feedback=feedback,
            confidence=confidence,
            is_valid_pose=True,
        )
