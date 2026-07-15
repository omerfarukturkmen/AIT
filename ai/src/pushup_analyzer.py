"""Push-up exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

from collections import deque
from typing import Any

# Elbow-angle thresholds (degrees)
TOP_THRESHOLD = 155.0
DOWN_THRESHOLD = 120.0
DEPTH_THRESHOLD = 95.0

INSUFFICIENT_DEPTH_ANGLE = 95.0
TOO_DEEP_ELBOW_ANGLE = 50.0
FAST_ANGLE_DELTA = 20.0
HIP_SAG_THRESHOLD = 25.0  # deviation from ~180° plank line

ERROR_MESSAGES: dict[str, str] = {
    "insufficient_depth": "Daha derine inmelisin.",
    "elbow_angle_insufficient": "Dirsek acin yeterli seviyeye ulasmadi.",
    "too_deep_or_unstable": "Dirsek acin cok dar, hareketi kontrollu yapmalisin.",
    "too_fast": "Hareketi daha kontrollu yapmalisin.",
    "incomplete_rep": "Push-up tekrarin tamamlanmadi.",
    "hip_sag": "Kalcani dusurme, govdeyi duz tut.",
}


class PushupAnalyzer:
    """Rep counter with confirmed states and rule-based form checks."""

    CONFIRM_FRAMES = 3
    TOP_FRAMES_TO_ARM = 3

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

        self.min_elbow_angle_current_rep: float | None = None
        self.last_rep: dict[str, Any] = {
            "depthStatus": None,
            "minElbowAngle": None,
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

        self.frames_in_top: int = 0
        self.ready_for_pushup: bool = False
        self.in_rep_attempt: bool = False
        self.descent_started: bool = False

        self._session_errors: list[str] = []
        self._rep_errors: list[str] = []
        self._session_feedback: list[str] = []

        self._last_left_elbow: float | None = None
        self._last_right_elbow: float | None = None
        self._last_smoothed_elbow: float | None = None

    def _update_smoothed(self, raw_average: float | None) -> float | None:
        if raw_average is not None:
            self._angle_history.append(float(raw_average))
        if not self._angle_history:
            self._smoothed_average = None
            return None
        self._smoothed_average = sum(self._angle_history) / len(self._angle_history)
        return self._smoothed_average

    def _measure_state(self, angle: float) -> str:
        if angle >= TOP_THRESHOLD:
            return "top"
        if angle < DEPTH_THRESHOLD:
            return "bottom"
        if angle < DOWN_THRESHOLD:
            return "descending"
        if self.in_rep_attempt:
            return "ascending"
        return "top"

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
        self.min_elbow_angle_current_rep = None
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
        hip_alignment: float | None,
    ) -> None:
        if not self.in_rep_attempt:
            return

        if self._prev_smoothed is not None:
            delta = abs(float(smoothed) - self._prev_smoothed)
            if delta >= FAST_ANGLE_DELTA:
                self._register_error("too_fast")

        if float(smoothed) < TOO_DEEP_ELBOW_ANGLE and self._confirmed_state == "bottom":
            self._register_error("too_deep_or_unstable")

        if hip_alignment is not None:
            # avg_hip near 180 means straight plank; large deviation => sag/pike
            sag = abs(180.0 - float(hip_alignment))
            if sag >= HIP_SAG_THRESHOLD:
                self._register_error("hip_sag")

    def _finalize_rep_errors(self, min_angle: float | None) -> None:
        if min_angle is None:
            if self.descent_started:
                self._register_error("incomplete_rep")
            return

        if min_angle >= INSUFFICIENT_DEPTH_ANGLE:
            self._register_error("insufficient_depth")
            self._register_error("elbow_angle_insufficient")
        if min_angle < TOO_DEEP_ELBOW_ANGLE:
            self._register_error("too_deep_or_unstable")

    def _complete_rep(self) -> list[str]:
        min_angle = self.min_elbow_angle_current_rep
        messages: list[str] = []

        if min_angle is not None and min_angle < DEPTH_THRESHOLD:
            self.valid_reps += 1
            self.rep_count = self.valid_reps
            self.depth_valid = True
            self.last_depth_status = "good_depth"
            if not self._rep_errors:
                messages = ["Push-up derinligi iyi."]
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
            "minElbowAngle": min_angle,
            "depthValid": self.depth_valid,
            "errors": list(self._rep_errors),
            "feedback": list(messages),
        }
        self._reset_rep_attempt()
        self.ready_for_pushup = False
        return messages

    def _sync_form_fields(self) -> None:
        self.errors = list(self._session_errors)
        self.form_status = self._compute_form_status(self.errors)

    def finalize_session(self) -> None:
        if (
            self._last_smoothed_elbow is not None
            and self._last_smoothed_elbow >= TOP_THRESHOLD
        ):
            self.current_state = "top"
            self._confirmed_state = "top"
        self._sync_form_fields()

    def get_result(self, video_path: str = "data/input/input.mp4") -> dict[str, Any]:
        from datetime import datetime

        self.finalize_session()
        return {
            "exercise": "push-up",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "form_status": self.form_status,
            "current_state": self.current_state,
            "depth_valid": self.depth_valid,
            "angles": {
                "left_elbow_angle": self._last_left_elbow,
                "right_elbow_angle": self._last_right_elbow,
                "smoothed_elbow_angle": self._last_smoothed_elbow,
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
            self._last_left_elbow = float(left)
        if right is not None:
            self._last_right_elbow = float(right)
        if smoothed is not None:
            self._last_smoothed_elbow = float(smoothed)

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
            "exercise": "push-up",
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
                "left_elbow_angle": left,
                "right_elbow_angle": right,
                "smoothed_elbow_angle": smoothed,
            },
            "repCount": self.rep_count,
            "currentPhase": self.current_state,
            "elbowAngle": {
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
                "minElbowAngle": self.last_rep.get("minElbowAngle"),
                "depthValid": self.last_rep.get("depthValid"),
                "errors": list(self.last_rep.get("errors") or []),
                "feedback": list(self.last_rep.get("feedback") or []),
            },
        }

    def analyze_frame(
        self,
        elbow_angles: dict[str, float | None],
        pose_confidence: float | None = None,
        hip_alignment: float | None = None,
    ) -> dict[str, Any]:
        self.frame_index += 1

        left = elbow_angles.get("left")
        right = elbow_angles.get("right")
        raw_average = elbow_angles.get("average")

        if raw_average is None:
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

        if confirmed == "top":
            self.frames_in_top += 1
            if self.frames_in_top >= self.TOP_FRAMES_TO_ARM:
                self.ready_for_pushup = True
        else:
            self.frames_in_top = 0

        rep_feedback: list[str] = []

        if (
            prev_confirmed == "top"
            and confirmed in ("descending", "bottom")
            and self.ready_for_pushup
            and not self.in_rep_attempt
        ):
            self.in_rep_attempt = True
            self.descent_started = True
            self.min_elbow_angle_current_rep = float(smoothed)
            self._rep_errors = []

        if self.in_rep_attempt:
            self.min_elbow_angle_current_rep = min(
                self.min_elbow_angle_current_rep or float(smoothed),
                float(smoothed),
            )
            if float(smoothed) < DOWN_THRESHOLD:
                self.descent_started = True
            if float(smoothed) < DEPTH_THRESHOLD:
                self.depth_valid = True
            self._check_in_rep_form(float(smoothed), hip_alignment)

        if (
            confirmed == "top"
            and prev_confirmed != "top"
            and self.in_rep_attempt
        ):
            rep_feedback = self._complete_rep()
        elif confirmed == "top" and prev_confirmed != "top":
            self._reset_rep_attempt()

        self._prev_smoothed = float(smoothed)
        self.previous_state = prev_confirmed
        self.current_state = confirmed
        self._last_frame_confirmed_state = confirmed

        feedback = list(rep_feedback)
        if not feedback and confirmed == "top" and self.ready_for_pushup:
            feedback = ["Push-up icin hazir pozisyondasin."]

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
