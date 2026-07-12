"""Squat exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

from collections import deque
from typing import Any

# --- Rep / phase knee-angle thresholds (degrees) ---
STANDING_THRESHOLD = 160.0
DOWN_THRESHOLD = 120.0
DEPTH_THRESHOLD = 100.0

# --- Form error thresholds ---
INSUFFICIENT_DEPTH_ANGLE = 100.0   # min knee above this => not deep enough
TOO_DEEP_KNEE_ANGLE = 55.0         # min knee below this => too narrow / risky
FAST_ANGLE_DELTA = 18.0            # max smoothed change per frame (deg)
TORSO_LEAN_THRESHOLD = 28.0        # forward lean degrees from vertical

ERROR_MESSAGES: dict[str, str] = {
    "insufficient_depth": "Daha derine inmelisin.",
    "knee_angle_insufficient": "Diz acin yeterli seviyeye ulasmadi.",
    "too_deep_or_unstable": "Diz acin cok dar, hareketi kontrollu yapmalisin.",
    "too_fast": "Hareketi daha kontrollu yapmalisin.",
    "incomplete_rep": "Squat tekrarin tamamlanmadi.",
    "torso_lean": "Ust govdeni fazla one egme.",
}

class SquatAnalyzer:
    """Rep counter with confirmed states and rule-based form checks."""

    CONFIRM_FRAMES = 3
    STANDING_FRAMES_TO_ARM = 3

    def __init__(self) -> None:
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

        self._angle_history: deque[float] = deque(maxlen=7)
        self._smoothed_average: float | None = None
        self._prev_smoothed: float | None = None

        self._candidate_state: str = "unknown"
        self._candidate_state_count: int = 0
        self._confirmed_state: str = "unknown"
        self._last_frame_confirmed_state: str = "unknown"

        self.frames_in_standing: int = 0
        self.ready_for_squat: bool = False
        self.in_rep_attempt: bool = False
        self.descent_started: bool = False

        self._session_errors: list[str] = []
        self._rep_errors: list[str] = []
        self._session_feedback: list[str] = []

        self._last_left_knee: float | None = None
        self._last_right_knee: float | None = None
        self._last_smoothed_knee: float | None = None

    def _update_smoothed(self, raw_average: float | None) -> float | None:
        if raw_average is not None:
            self._angle_history.append(float(raw_average))
        if not self._angle_history:
            self._smoothed_average = None
            return None
        self._smoothed_average = sum(self._angle_history) / len(self._angle_history)
        return self._smoothed_average

    def _measure_state(self, angle: float) -> str:
        if angle >= STANDING_THRESHOLD:
            return "standing"
        if angle < DEPTH_THRESHOLD:
            return "bottom"
        if angle < DOWN_THRESHOLD:
            return "descending"
        if self.in_rep_attempt:
            return "ascending"
        return "standing"

    def _run_state_confirmation(self, measured: str) -> None:
        if measured == self._candidate_state:
            self._candidate_state_count += 1
        else:
            self._candidate_state = measured
            self._candidate_state_count = 1
        if self._candidate_state_count >= self.CONFIRM_FRAMES:
            self._confirmed_state = self._candidate_state

    def _reset_rep_attempt(self) -> None:
        self.in_rep_attempt = False
        self.descent_started = False
        self.min_knee_angle_current_rep = None
        self._rep_errors = []

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
        """Detect form issues once per rep (no per-frame feedback spam)."""
        if not self.in_rep_attempt:
            return

        if self._prev_smoothed is not None:
            delta = abs(float(smoothed) - self._prev_smoothed)
            if delta >= FAST_ANGLE_DELTA:
                self._register_error("too_fast")

        angle = float(smoothed)
        if angle < TOO_DEEP_KNEE_ANGLE and self._confirmed_state == "bottom":
            self._register_error("too_deep_or_unstable")

        if torso_lean is not None and torso_lean >= TORSO_LEAN_THRESHOLD:
            self._register_error("torso_lean")

    def _finalize_rep_errors(self, min_angle: float | None) -> None:
        """Map completed rep outcome to error codes (added once per rep)."""
        if min_angle is None:
            if self.descent_started:
                self._register_error("incomplete_rep")
            return

        if min_angle >= INSUFFICIENT_DEPTH_ANGLE:
            self._register_error("insufficient_depth")
            self._register_error("knee_angle_insufficient")
        if min_angle < TOO_DEEP_KNEE_ANGLE:
            self._register_error("too_deep_or_unstable")

    def _complete_rep(self) -> list[str]:
        min_angle = self.min_knee_angle_current_rep
        messages: list[str] = []

        if min_angle is not None and min_angle < DEPTH_THRESHOLD:
            self.valid_reps += 1
            self.rep_count = self.valid_reps
            self.depth_valid = True
            self.last_depth_status = "good_depth"
            if not self._rep_errors:
                messages = ["Squat derinligi iyi."]
        elif self.descent_started and min_angle is not None and min_angle < DOWN_THRESHOLD:
            self.invalid_reps += 1
            self.depth_valid = False
            self.last_depth_status = "too_shallow"
            self._finalize_rep_errors(min_angle)
            messages = self._errors_to_feedback(self._rep_errors)
        elif self.descent_started:
            self.invalid_reps += 1
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
        self._reset_rep_attempt()
        self.ready_for_squat = False
        return messages

    def _sync_form_fields(self) -> None:
        self.errors = list(self._session_errors)
        self.form_status = self._compute_form_status(self.errors)

    def _sanitize_session_errors(self) -> None:
        """Drop too_deep if the session never had a truly narrow knee angle."""
        if "too_deep_or_unstable" not in self._session_errors:
            return
        last_rep_min = self.last_rep.get("minKneeAngle")
        standing_now = (
            self._last_smoothed_knee is not None
            and self._last_smoothed_knee >= STANDING_THRESHOLD
        )
        rep_not_too_deep = last_rep_min is None or last_rep_min >= TOO_DEEP_KNEE_ANGLE
        if standing_now and rep_not_too_deep:
            self._session_errors = [
                e for e in self._session_errors if e != "too_deep_or_unstable"
            ]
            too_deep_msg = ERROR_MESSAGES.get("too_deep_or_unstable")
            if too_deep_msg:
                self._session_feedback = [
                    m for m in self._session_feedback if m != too_deep_msg
                ]

    def finalize_session(self) -> None:
        """End-of-video adjustments for export (state + error cleanup)."""
        if (
            self._last_smoothed_knee is not None
            and self._last_smoothed_knee >= STANDING_THRESHOLD
        ):
            self.current_state = "standing"
            self._confirmed_state = "standing"
        self._sanitize_session_errors()
        self._sync_form_fields()

    def get_result(self, video_path: str = "data/input/input.mp4") -> dict[str, Any]:
        """Return the fixed backend JSON schema for the current session."""
        from datetime import datetime

        self.finalize_session()
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
        knee_angles: dict[str, float | None],
        pose_confidence: float | None = None,
        torso_lean: float | None = None,
    ) -> dict[str, Any]:
        self.frame_index += 1

        left = knee_angles.get("left")
        right = knee_angles.get("right")
        raw_average = knee_angles.get("average")
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
            smoothed = float(smoothed_input)
            if raw_average is not None:
                self._angle_history.append(float(raw_average))
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

        prev_confirmed = self._last_frame_confirmed_state
        measured = self._measure_state(float(smoothed))
        self._run_state_confirmation(measured)
        confirmed = self._confirmed_state

        if confirmed == "standing":
            self.frames_in_standing += 1
            if self.frames_in_standing >= self.STANDING_FRAMES_TO_ARM:
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
            self._rep_errors = []

        if self.in_rep_attempt:
            self.min_knee_angle_current_rep = min(
                self.min_knee_angle_current_rep or float(smoothed),
                float(smoothed),
            )
            if float(smoothed) < DOWN_THRESHOLD:
                self.descent_started = True
            if float(smoothed) < DEPTH_THRESHOLD:
                self.depth_valid = True
            self._check_in_rep_form(float(smoothed), torso_lean)

        if (
            confirmed == "standing"
            and prev_confirmed != "standing"
            and self.in_rep_attempt
        ):
            rep_feedback = self._complete_rep()
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
