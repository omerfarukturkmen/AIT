"""Squat exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

import statistics
from collections import deque
from typing import Any

import cv2

from angle_utils import build_squat_frame_metrics, get_landmark_point

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

# Combined biomechanical form thresholds (independent of rep state machine)
STANDING_KNEE_ANGLE = 155.0
STANDING_HIP_ANGLE = 155.0
SQUAT_KNEE_CANDIDATE = 140.0
SQUAT_HIP_CANDIDATE = 145.0
EXCESSIVE_TORSO_LEAN = 45.0
HIP_FLEXION_MISMATCH_KNEE = 120.0
HIP_FLEXION_MISMATCH_HIP = 155.0
FORM_CONFIRMATION_FRAMES = 3

# Rep lifecycle / false-positive guards
STANDING_CONFIRMATION_FRAMES = 3
MOVEMENT_DIRECTION_EPSILON = 2.0
MIN_DESCENT_ANGLE_CHANGE = 15.0
REP_COOLDOWN_FRAMES = 3
MIN_POSE_CONFIDENCE = 0.50

# Depth measurement (knee + hip, independent of rep state machine)
DEEP_KNEE_ANGLE = 100.0
ACCEPTABLE_KNEE_ANGLE = 115.0
DEEP_HIP_ANGLE = 105.0
ACCEPTABLE_HIP_ANGLE = 125.0
DEPTH_CONFIRMATION_FRAMES = 3
DEPTH_RELEASE_KNEE_ANGLE = 125.0
DEPTH_RELEASE_HIP_ANGLE = 135.0
DEPTH_CANDIDATE_HOLD_KNEE = 120.0
DEPTH_CANDIDATE_HOLD_HIP = 130.0
DEPTH_SCORE_KNEE_MAX = 150.0
DEPTH_SCORE_KNEE_MIN = 90.0
DEPTH_SCORE_HIP_MAX = 160.0
DEPTH_SCORE_HIP_MIN = 90.0
DEPTH_SCORE_KNEE_WEIGHT = 0.6
DEPTH_SCORE_HIP_WEIGHT = 0.4

_DEPTH_STATUS_PRIORITY: dict[str, int] = {
    "unknown": 0,
    "metrics_incomplete": 0,
    "shallow": 1,
    "acceptable": 2,
    "deep": 3,
}

ERROR_MESSAGES: dict[str, str] = {
    "insufficient_depth": "Daha derine inmelisin.",
    "squat_depth_reach": "Squat derinligine ulasmak icin daha asagi in.",
    "knee_angle_insufficient": "Diz acin yeterli seviyeye ulasmadi.",
    "too_deep_or_unstable": "Diz acin cok dar, hareketi kontrollu yapmalisin.",
    "too_fast": "Hareketi daha kontrollu yapmalisin.",
    "incomplete_rep": "Squat tekrarin tamamlanmadi.",
    "torso_lean": "Ust govdeni fazla one egme.",
    "excessive_forward_lean": "Keep your chest more upright",
    "hip_flexion_mismatch": "Bend at the hips as you descend",
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
        self._last_left_hip: float | None = None
        self._last_right_hip: float | None = None

        # Biomechanical form layer (separate from rep movement state)
        self.current_form_state: str = "unknown"
        self.candidate_form_state: str | None = None
        self.candidate_form_frames: int = 0
        self.current_form_metrics: dict[str, float | None] = {
            "knee_angle": None,
            "hip_angle": None,
            "torso_lean": None,
        }
        self.form_errors: dict[str, int] = {
            "excessive_forward_lean": 0,
            "hip_flexion_mismatch": 0,
            "insufficient_depth": 0,
        }
        self._form_error_segment_active: str | None = None

        # Depth tracking (knee + hip confirmation, separate from rep state machine)
        self.depth_candidate_frames: int = 0
        self.depth_confirmed: bool = False
        self.depth_status: str = "unknown"
        self.current_rep_min_knee_angle: float | None = None
        self.current_rep_min_hip_angle: float | None = None
        self.current_rep_max_torso_lean: float | None = None
        self.current_rep_depth_score: float | None = None
        self.current_rep_best_depth_status: str = "unknown"
        self._depth_candidate_status: str | None = None
        self._depth_qualifying_streak: int = 0
        self._depth_feedback_given_this_rep: bool = False
        self._last_rep_depth_summary: dict[str, Any] = {
            "last_rep_depth_status": "unknown",
            "last_rep_depth_score": None,
            "last_rep_min_knee_angle": None,
            "last_rep_min_hip_angle": None,
        }

        # Rep lifecycle (false-positive reduction)
        self.rep_in_progress: bool = False
        self.has_seen_valid_standing: bool = False
        self.standing_candidate_frames: int = 0
        self.standing_confirmed: bool = False
        self.rep_start_knee_angle: float | None = None
        self.rep_start_hip_angle: float | None = None
        self.reached_depth: bool = False
        self.reached_bottom: bool = False
        self.entered_ascent: bool = False
        self.previous_smoothed_knee: float | None = None
        self.previous_smoothed_hip: float | None = None
        self.movement_direction: str = "unknown"
        self.rep_counted: bool = False
        self.incomplete_rep_recorded: bool = False
        self._pending_rep_start: bool = False
        self._standing_reference_knee: float | None = None
        self._standing_reference_hip: float | None = None
        self._rep_cooldown_remaining: int = 0
        self._session_finalized: bool = False
        self._incomplete_end_handled: bool = False
        self._smoothed_hip: float | None = None
        self._prev_smoothed_hip: float | None = None
        self._last_standing_knee: float | None = None
        self._last_standing_hip: float | None = None

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
        self.rep_in_progress = False
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
        self.rep_start_knee_angle = None
        self.rep_start_hip_angle = None
        self.reached_depth = False
        self.reached_bottom = False
        self.entered_ascent = False
        self.rep_counted = False
        self.incomplete_rep_recorded = False
        self._reset_depth_tracking()
        self._reset_rep_lifecycle_pending()

    def _reset_depth_tracking(self) -> None:
        self.depth_candidate_frames = 0
        self.depth_confirmed = False
        self.depth_status = "unknown"
        self.current_rep_min_knee_angle = None
        self.current_rep_min_hip_angle = None
        self.current_rep_max_torso_lean = None
        self.current_rep_depth_score = None
        self.current_rep_best_depth_status = "unknown"
        self._depth_candidate_status = None
        self._depth_qualifying_streak = 0
        self._depth_feedback_given_this_rep = False

    def _is_frame_reliable(self, pose_confidence: float | None) -> bool:
        if pose_confidence is None:
            return True
        return float(pose_confidence) >= MIN_POSE_CONFIDENCE

    def _is_standing_posture(
        self,
        knee: float | None,
        hip: float | None,
        smoothed_knee: float | None = None,
    ) -> bool:
        knee_val = knee if knee is not None else smoothed_knee
        if knee_val is None:
            return False
        if hip is not None:
            return (
                float(knee_val) >= STANDING_KNEE_ANGLE
                and float(hip) >= STANDING_HIP_ANGLE
            )
        return float(knee_val) >= STANDING_KNEE_ANGLE

    def _update_standing_confirmation(
        self,
        knee: float | None,
        hip: float | None,
        smoothed_knee: float | None,
        *,
        reliable: bool,
    ) -> None:
        if not reliable:
            return
        if self._is_standing_posture(knee, hip, smoothed_knee):
            self.standing_candidate_frames += 1
        else:
            self.standing_candidate_frames = 0
            self.standing_confirmed = False

        if self.standing_candidate_frames >= STANDING_CONFIRMATION_FRAMES:
            self.has_seen_valid_standing = True
            self.standing_confirmed = True
            if self._is_standing_posture(knee, hip, smoothed_knee):
                self._last_standing_knee = (
                    knee if knee is not None else smoothed_knee
                )
                self._last_standing_hip = hip

    def _update_movement_direction(
        self,
        smoothed_knee: float,
        hip: float | None,
        *,
        reliable: bool,
    ) -> None:
        if not reliable:
            return

        knee_delta: float | None = None
        if self.previous_smoothed_knee is not None:
            knee_delta = float(smoothed_knee) - float(self.previous_smoothed_knee)
            if abs(knee_delta) > MAX_SINGLE_FRAME_JUMP:
                knee_delta = None

        hip_delta: float | None = None
        if hip is not None and self.previous_smoothed_hip is not None:
            hip_delta = float(hip) - float(self.previous_smoothed_hip)
            if abs(hip_delta) > MAX_SINGLE_FRAME_JUMP:
                hip_delta = None

        combined: float | None = knee_delta
        if knee_delta is not None and hip_delta is not None:
            combined = (knee_delta + hip_delta) / 2.0
        elif knee_delta is None and hip_delta is not None:
            combined = hip_delta

        if combined is None:
            self.movement_direction = "unknown"
        elif combined <= -MOVEMENT_DIRECTION_EPSILON:
            self.movement_direction = "descending"
        elif combined >= MOVEMENT_DIRECTION_EPSILON:
            self.movement_direction = "ascending"
        else:
            self.movement_direction = "stable"

        self.previous_smoothed_knee = float(smoothed_knee)
        if hip is not None:
            self._smoothed_hip = float(hip)
            self.previous_smoothed_hip = float(hip)

    def _reset_rep_lifecycle_pending(self) -> None:
        self._pending_rep_start = False
        self._standing_reference_knee = None
        self._standing_reference_hip = None

    def _begin_rep_cycle(self, smoothed: float) -> None:
        self.in_rep_attempt = True
        self.rep_in_progress = True
        self.descent_started = True
        self.min_knee_angle_current_rep = float(smoothed)
        if self.rep_start_knee_angle is None:
            self.rep_start_knee_angle = self._standing_reference_knee or float(smoothed)
        if self.rep_start_hip_angle is None:
            self.rep_start_hip_angle = self._standing_reference_hip
        if self._rep_start_frame is None:
            self._rep_start_frame = self.frame_index
        self._rep_errors = []
        self._reached_valid_depth = False
        self._ascending_after_depth = False
        self._torso_lean_latched = False
        self._too_fast_latched = False
        self.rep_counted = False
        self.incomplete_rep_recorded = False
        self.entered_ascent = False
        self.reached_bottom = False
        self.reached_depth = False
        self._reset_depth_tracking()
        self._pending_rep_start = False

    def _meaningful_descent_amplitude(
        self,
        knee: float | None,
        smoothed: float,
    ) -> bool:
        ref = self.rep_start_knee_angle or self._standing_reference_knee
        if ref is None:
            return False
        if self.min_knee_angle_current_rep is not None:
            return float(ref) - float(self.min_knee_angle_current_rep) >= MIN_DESCENT_ANGLE_CHANGE
        current = knee if knee is not None else smoothed
        return float(ref) - float(current) >= MIN_DESCENT_ANGLE_CHANGE

    def _update_rep_lifecycle_flags(
        self,
        smoothed: float,
        confirmed: str,
    ) -> None:
        self.reached_depth = self.depth_confirmed
        if confirmed == "bottom" or float(smoothed) <= BOTTOM_ENTER:
            self.reached_bottom = True
        if self.depth_confirmed and (
            self.movement_direction == "ascending" or confirmed == "ascending"
        ):
            self.entered_ascent = True
        if self._reached_valid_depth and (
            confirmed == "ascending" or self._direction > DIRECTION_DEADZONE
        ):
            self._ascending_after_depth = True

    def _can_count_valid_rep(self) -> bool:
        if not self.rep_in_progress or self.rep_counted:
            return False
        if not self.has_seen_valid_standing or not self.standing_confirmed:
            return False
        if not self.depth_confirmed or not self.entered_ascent:
            return False
        if not self._meaningful_descent_amplitude(None, self._smoothed_average or 0.0):
            return False
        min_angle = self.min_knee_angle_current_rep
        if min_angle is None or float(min_angle) >= VALID_DEPTH_ANGLE:
            return False
        return True

    def _should_record_incomplete_rep(self) -> bool:
        if not self.rep_in_progress or self.incomplete_rep_recorded or self.rep_counted:
            return False
        if not self.descent_started:
            return False
        if self.depth_confirmed:
            return False
        return self._meaningful_descent_amplitude(
            None, self._smoothed_average or 0.0
        )

    def _rep_lifecycle_snapshot(self) -> dict[str, Any]:
        return {
            "rep_in_progress": self.rep_in_progress,
            "movement_direction": self.movement_direction,
            "has_seen_valid_standing": self.has_seen_valid_standing,
            "standing_confirmed": self.standing_confirmed,
            "reached_depth": self.reached_depth,
            "reached_bottom": self.reached_bottom,
            "entered_ascent": self.entered_ascent,
            "rep_counted": self.rep_counted,
            "pending_rep_start": self._pending_rep_start,
        }

    @staticmethod
    def _linear_depth_component(
        value: float,
        high_angle: float,
        low_angle: float,
    ) -> float:
        if value >= high_angle:
            return 0.0
        if value <= low_angle:
            return 100.0
        span = high_angle - low_angle
        if span <= 0:
            return 0.0
        return (high_angle - value) / span * 100.0

    def _compute_depth_score(
        self,
        knee: float | None,
        hip: float | None,
    ) -> float | None:
        if knee is None or hip is None:
            return None
        knee_part = self._linear_depth_component(
            float(knee), DEPTH_SCORE_KNEE_MAX, DEPTH_SCORE_KNEE_MIN
        )
        hip_part = self._linear_depth_component(
            float(hip), DEPTH_SCORE_HIP_MAX, DEPTH_SCORE_HIP_MIN
        )
        score = (
            DEPTH_SCORE_KNEE_WEIGHT * knee_part + DEPTH_SCORE_HIP_WEIGHT * hip_part
        )
        return max(0.0, min(100.0, score))

    def _compute_depth_status(
        self,
        knee: float | None,
        hip: float | None,
    ) -> str:
        if knee is None or hip is None:
            return "metrics_incomplete"
        if knee <= DEEP_KNEE_ANGLE and hip <= DEEP_HIP_ANGLE:
            return "deep"
        if knee <= ACCEPTABLE_KNEE_ANGLE and hip <= ACCEPTABLE_HIP_ANGLE:
            return "acceptable"
        return "shallow"

    def _update_best_depth_status(self, status: str) -> None:
        if status not in _DEPTH_STATUS_PRIORITY:
            return
        current = self.current_rep_best_depth_status
        if _DEPTH_STATUS_PRIORITY[status] > _DEPTH_STATUS_PRIORITY.get(current, 0):
            self.current_rep_best_depth_status = status

    def _depth_candidate_from_frame(
        self,
        knee: float | None,
        hip: float | None,
        status: str,
    ) -> tuple[bool, bool, str]:
        """Return (qualifies_for_confirmation, hold_without_reset, status)."""
        if status in ("deep", "acceptable"):
            return True, False, status
        if (
            self.depth_candidate_frames > 0
            and knee is not None
            and hip is not None
            and knee <= DEPTH_CANDIDATE_HOLD_KNEE
            and hip <= DEPTH_CANDIDATE_HOLD_HIP
        ):
            hold_status = self._depth_candidate_status or status
            if hold_status in ("deep", "acceptable"):
                return False, True, hold_status
        return False, False, status

    def _update_depth_evaluation(
        self,
        knee_angles: dict[str, Any],
        torso_lean: float | None,
    ) -> None:
        if not self.in_rep_attempt and not self.rep_in_progress:
            return

        knee, hip, torso = self._resolve_squat_metrics(knee_angles, torso_lean)
        status = self._compute_depth_status(knee, hip)
        self.depth_status = status

        if knee is not None:
            self.current_rep_min_knee_angle = (
                knee
                if self.current_rep_min_knee_angle is None
                else min(self.current_rep_min_knee_angle, knee)
            )
        if hip is not None:
            self.current_rep_min_hip_angle = (
                hip
                if self.current_rep_min_hip_angle is None
                else min(self.current_rep_min_hip_angle, hip)
            )
        if torso is not None:
            self.current_rep_max_torso_lean = (
                torso
                if self.current_rep_max_torso_lean is None
                else max(self.current_rep_max_torso_lean, torso)
            )

        score = self._compute_depth_score(
            self.current_rep_min_knee_angle,
            self.current_rep_min_hip_angle,
        )
        if score is not None:
            self.current_rep_depth_score = round(score, 2)

        if status == "metrics_incomplete":
            return

        if self.depth_confirmed:
            if status in ("deep", "acceptable"):
                self._update_best_depth_status(status)
            return

        qualifies, hold, candidate_status = self._depth_candidate_from_frame(
            knee, hip, status
        )
        if qualifies:
            self._depth_qualifying_streak += 1
            self.depth_candidate_frames += 1
            self._depth_candidate_status = candidate_status
            self._update_best_depth_status(candidate_status)
        elif hold:
            self._depth_qualifying_streak = 0
        elif status == "shallow":
            self._depth_qualifying_streak = 0
            self.depth_candidate_frames = 0
            self._depth_candidate_status = None
            self._update_best_depth_status("shallow")

        if self._depth_qualifying_streak >= DEPTH_CONFIRMATION_FRAMES:
            self.depth_confirmed = True
            if self._depth_candidate_status:
                self._update_best_depth_status(self._depth_candidate_status)

    def _depth_snapshot(self) -> dict[str, Any]:
        return {
            "status": self.depth_status,
            "confirmed": self.depth_confirmed,
            "candidate_frames": self.depth_candidate_frames,
            "score": self.current_rep_depth_score,
            "min_knee_angle": self.current_rep_min_knee_angle,
            "min_hip_angle": self.current_rep_min_hip_angle,
            "best_depth_status": self.current_rep_best_depth_status,
        }

    def _apply_depth_rep_completion_feedback(self, messages: list[str]) -> None:
        if not self.descent_started or self.depth_confirmed:
            return
        if self._depth_feedback_given_this_rep:
            return
        self._depth_feedback_given_this_rep = True
        self._register_error("squat_depth_reach")
        self.form_errors["insufficient_depth"] = (
            self.form_errors.get("insufficient_depth", 0) + 1
        )
        msg = ERROR_MESSAGES["squat_depth_reach"]
        if msg not in messages:
            messages.append(msg)

    def _finalize_rep_depth_summary(self) -> None:
        self._last_rep_depth_summary = {
            "last_rep_depth_status": self.current_rep_best_depth_status,
            "last_rep_depth_score": self.current_rep_depth_score,
            "last_rep_min_knee_angle": self.current_rep_min_knee_angle,
            "last_rep_min_hip_angle": self.current_rep_min_hip_angle,
        }

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
                "depth_status": self.current_rep_best_depth_status,
                "depth_score": self.current_rep_depth_score,
                "min_hip_angle": (
                    round(self.current_rep_min_hip_angle, 2)
                    if self.current_rep_min_hip_angle is not None
                    else None
                ),
                "metric_min_knee_angle": (
                    round(self.current_rep_min_knee_angle, 2)
                    if self.current_rep_min_knee_angle is not None
                    else None
                ),
                "max_torso_lean": (
                    round(self.current_rep_max_torso_lean, 2)
                    if self.current_rep_max_torso_lean is not None
                    else None
                ),
                "start_knee_angle": (
                    round(self.rep_start_knee_angle, 2)
                    if self.rep_start_knee_angle is not None
                    else None
                ),
                "completed_full_cycle": valid,
            }
        )

    def _complete_rep(self, *, return_angle: float | None = None) -> list[str]:
        if self.rep_counted:
            return []

        min_angle = self.min_knee_angle_current_rep
        if return_angle is None:
            return_angle = self._smoothed_average
        self._last_return_angle = return_angle
        messages: list[str] = []
        valid = self._can_count_valid_rep()

        self._apply_depth_rep_completion_feedback(messages)
        self._finalize_rep_depth_summary()
        depth_feedback = list(messages)

        if valid:
            self.rep_counted = True
            self.depth_valid = True
            self.last_depth_status = "good_depth"
            if not self._rep_errors:
                messages = ["Squat derinligi iyi."]
        elif self._should_record_incomplete_rep():
            self.incomplete_rep_recorded = True
            self.depth_valid = False
            if min_angle is not None and min_angle < BOTTOM_EXIT:
                self.last_depth_status = "too_shallow"
            else:
                self.last_depth_status = "incomplete"
            self._finalize_rep_errors(min_angle)
            messages = self._errors_to_feedback(self._rep_errors)
            for msg in depth_feedback:
                if msg not in messages:
                    messages.append(msg)
        else:
            self._reset_rep_attempt()
            self._reset_rep_lifecycle_pending()
            return []

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

        if self.rep_in_progress and min_angle is not None:
            self._append_rep_history(
                valid=valid,
                min_angle=min_angle,
                return_angle=return_angle,
                messages=messages,
            )
            self.valid_reps = sum(1 for r in self.rep_history if r.get("valid"))
            self.invalid_reps = len(self.rep_history) - self.valid_reps
            self.rep_count = len(self.rep_history)
            self._rep_cooldown_remaining = REP_COOLDOWN_FRAMES

        self._reset_rep_attempt()
        self.ready_for_squat = False
        self.frames_in_standing = 0
        return messages

    def _finish_rep_cycle(self, *, return_angle: float) -> list[str]:
        if self.rep_counted:
            return []
        return self._complete_rep(return_angle=return_angle)

    def _sync_form_fields(self) -> None:
        self.errors = list(self._session_errors)
        self.form_status = self._compute_form_status(self.errors)

    @staticmethod
    def _as_metric_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            out = float(value)
        except (TypeError, ValueError):
            return None
        if out != out:  # NaN
            return None
        return out

    def _resolve_squat_metrics(
        self,
        knee_angles: dict[str, Any],
        torso_lean: float | None,
    ) -> tuple[float | None, float | None, float | None]:
        knee = self._as_metric_float(
            knee_angles.get("avg_knee", knee_angles.get("average"))
        )
        hip = self._as_metric_float(
            knee_angles.get("avg_hip", knee_angles.get("selected_hip"))
        )
        torso_val = self._as_metric_float(
            knee_angles.get("torso_lean", knee_angles.get("torso_lean_deg"))
        )
        if torso_val is None:
            torso_val = self._as_metric_float(torso_lean)
        return knee, hip, torso_val

    def _classify_form_state(
        self,
        knee: float | None,
        hip: float | None,
        torso: float | None,
    ) -> str:
        if knee is None or hip is None or torso is None:
            return "metrics_incomplete"
        if knee >= STANDING_KNEE_ANGLE and hip >= STANDING_HIP_ANGLE:
            return "standing"
        if torso >= EXCESSIVE_TORSO_LEAN:
            return "excessive_forward_lean"
        if knee <= HIP_FLEXION_MISMATCH_KNEE and hip >= HIP_FLEXION_MISMATCH_HIP:
            return "hip_not_flexed_enough"
        if knee < SQUAT_KNEE_CANDIDATE and hip < SQUAT_HIP_CANDIDATE:
            return "squat_position"
        return "unknown"

    def _reset_form_candidate(self) -> None:
        self.candidate_form_state = None
        self.candidate_form_frames = 0

    def _clear_form_error_segment(self) -> None:
        self._form_error_segment_active = None

    def _record_form_error_segment(self, form_state: str) -> None:
        code_map = {
            "excessive_forward_lean": "excessive_forward_lean",
            "hip_not_flexed_enough": "hip_flexion_mismatch",
        }
        code = code_map.get(form_state)
        if code is None:
            return
        if self._form_error_segment_active == code:
            return
        self._form_error_segment_active = code
        self.form_errors[code] = self.form_errors.get(code, 0) + 1
        self._unique_append(self._session_errors, code)
        msg = ERROR_MESSAGES.get(code)
        if msg and msg not in self._session_feedback:
            self._session_feedback.append(msg)

    def _update_form_evaluation(
        self,
        knee_angles: dict[str, Any],
        torso_lean: float | None,
    ) -> None:
        knee, hip, torso = self._resolve_squat_metrics(knee_angles, torso_lean)
        self.current_form_metrics = {
            "knee_angle": knee,
            "hip_angle": hip,
            "torso_lean": torso,
        }

        left_hip = self._as_metric_float(knee_angles.get("left_hip"))
        right_hip = self._as_metric_float(knee_angles.get("right_hip"))
        if left_hip is not None:
            self._last_left_hip = left_hip
        if right_hip is not None:
            self._last_right_hip = right_hip

        classified = self._classify_form_state(knee, hip, torso)
        if classified == "metrics_incomplete":
            return

        error_states = {"excessive_forward_lean", "hip_not_flexed_enough"}
        if classified not in error_states:
            self._reset_form_candidate()
            self.current_form_state = classified
            if classified == "standing":
                self._clear_form_error_segment()
            return

        if classified == self.candidate_form_state:
            self.candidate_form_frames += 1
        else:
            self.candidate_form_state = classified
            self.candidate_form_frames = 1

        if self.candidate_form_frames >= FORM_CONFIRMATION_FRAMES:
            self.current_form_state = classified
            self._record_form_error_segment(classified)

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
        if not self.rep_in_progress or not self.depth_confirmed or not self.entered_ascent:
            return False
        if self.rep_counted:
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
            or self.movement_direction == "ascending"
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

    def _sync_rep_counters(self) -> None:
        self.rep_count = len(self.rep_history)
        self.valid_reps = sum(1 for r in self.rep_history if r.get("valid"))
        self.invalid_reps = self.rep_count - self.valid_reps

    def get_rep_summary(self) -> dict[str, int]:
        """Successful / failed / total attempt counts from rep_history."""
        from rep_summary import summarize_rep_history

        return summarize_rep_history(self.rep_history).as_dict()

    def finalize_session(self) -> None:
        """Complete a near-finished last rep; never invent mid-ascent reps."""
        if self._session_finalized:
            self._sanitize_session_errors()
            self._sync_form_fields()
            self._sync_rep_counters()
            return

        self._session_finalized = True

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
            self.standing_confirmed = True
            self._finish_rep_cycle(return_angle=return_angle)
            self.current_state = "standing"
            self._confirmed_state = "standing"
        elif self.rep_in_progress and not self._incomplete_end_handled:
            self._incomplete_end_handled = True
            if self.descent_started and self._should_record_incomplete_rep():
                self._complete_rep(return_angle=self._smoothed_average)
            elif self.descent_started:
                self._register_error("incomplete_rep")
                msg = ERROR_MESSAGES["incomplete_rep"]
                if msg not in self._session_feedback:
                    self._session_feedback.append(msg)
                self._reset_rep_attempt()
            else:
                self._reset_rep_attempt()

        if (
            self._smoothed_average is not None
            and self._smoothed_average >= STANDING_ENTER
        ):
            self.current_state = "standing"
            self._confirmed_state = "standing"

        self._sanitize_session_errors()
        self._sync_form_fields()
        self._sync_rep_counters()

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

    def get_score_breakdown(self) -> dict[str, Any]:
        """Internal squat score from rep_history (does not alter result JSON)."""
        from squat_scoring import calculate_squat_score_from_history

        return calculate_squat_score_from_history(self.rep_history).as_dict()

    def get_feedback_items(self) -> list[dict[str, Any]]:
        """Internal prioritized feedback items (deduplicated; public list unchanged)."""
        from feedback_priority import build_feedback_items, feedback_items_as_dicts

        items = build_feedback_items(
            codes=list(self.errors),
            messages=list(self._session_feedback) or list(self.feedback),
            sort=True,
        )
        return feedback_items_as_dicts(items)

    def get_top_feedback_items(self) -> list[dict[str, Any]]:
        """Highest-importance unique feedback (does not alter public feedback list)."""
        from feedback_priority import (
            build_feedback_items,
            feedback_items_as_dicts,
            select_top_feedback,
        )

        items = build_feedback_items(
            codes=list(self.errors),
            messages=list(self._session_feedback) or list(self.feedback),
            sort=True,
        )
        return feedback_items_as_dicts(select_top_feedback(items))

    def get_result(self, video_path: str = "data/input/input.mp4") -> dict[str, Any]:
        from datetime import datetime

        self.finalize_session()
        stats = self._session_knee_stats()
        rep_summary = self.get_rep_summary()
        return {
            "exercise": "squat",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "successful_reps": rep_summary["successful_reps"],
            "failed_reps": rep_summary["failed_reps"],
            "total_reps": rep_summary["total_reps"],
            "form_status": self.form_status,
            "current_state": self.current_state,
            "depth_valid": self.depth_valid,
            "angles": {
                "left_knee_angle": self._last_left_knee,
                "right_knee_angle": self._last_right_knee,
                "smoothed_knee_angle": self._last_smoothed_knee,
                "left_hip_angle": self._last_left_hip,
                "right_hip_angle": self._last_right_hip,
            },
            "form_metrics": dict(self.current_form_metrics),
            "current_form_state": self.current_form_state,
            "form_errors": dict(self.form_errors),
            "depth": self._depth_snapshot(),
            "depth_summary": dict(self._last_rep_depth_summary),
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
        rep_summary = self.get_rep_summary()
        return {
            "exercise": "squat",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "successful_reps": rep_summary["successful_reps"],
            "failed_reps": rep_summary["failed_reps"],
            "total_reps": rep_summary["total_reps"],
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
            "form_metrics": dict(self.current_form_metrics),
            "current_form_state": self.current_form_state,
            "form_errors": dict(self.form_errors),
            "depth": self._depth_snapshot(),
            "depth_summary": dict(self._last_rep_depth_summary),
            "rep_lifecycle": self._rep_lifecycle_snapshot(),
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
        landmark_visibility_ok: bool | None = None,
        landmark_visibility: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if fps is not None and fps > 1e-3:
            self.fps = float(fps)

        self.frame_index += 1

        if landmark_visibility_ok is False:
            try:
                from visibility_utils import visibility_feedback_messages
            except ImportError:
                from src.visibility_utils import visibility_feedback_messages  # type: ignore
            feedback = visibility_feedback_messages()
            self.feedback = feedback
            conf = float(pose_confidence) if pose_confidence is not None else 0.0
            result = self._build_result(
                left=knee_angles.get("left"),
                right=knee_angles.get("right"),
                raw_average=knee_angles.get("average"),
                smoothed=self._smoothed_average,
                feedback=feedback,
                confidence=conf,
                is_valid_pose=False,
            )
            if landmark_visibility is not None:
                result["landmark_visibility"] = dict(landmark_visibility)
            return result

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

        conf = float(pose_confidence) if pose_confidence is not None else 1.0
        reliable = self._is_frame_reliable(pose_confidence)
        metric_knee, metric_hip, _ = self._resolve_squat_metrics(knee_angles, torso_lean)

        if reliable:
            self._update_standing_confirmation(
                metric_knee, metric_hip, float(smoothed), reliable=True
            )
            self._update_movement_direction(float(smoothed), metric_hip, reliable=True)

        if self._rep_cooldown_remaining > 0:
            self._rep_cooldown_remaining -= 1

        prev_confirmed = self._last_frame_confirmed_state
        measured = self._measure_state(float(smoothed))
        if reliable:
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
            reliable
            and self.has_seen_valid_standing
            and not self.rep_in_progress
            and self._rep_cooldown_remaining <= 0
            and confirmed in ("descending", "bottom")
            and self.ready_for_squat
        ):
            if not self._pending_rep_start:
                self._standing_reference_knee = (
                    self._last_standing_knee or metric_knee or float(smoothed)
                )
                self._standing_reference_hip = (
                    self._last_standing_hip or metric_hip
                )
                self.rep_start_knee_angle = self._standing_reference_knee
                self.rep_start_hip_angle = self._standing_reference_hip
            self._pending_rep_start = True

        if (
            reliable
            and self._pending_rep_start
            and not self.rep_in_progress
            and self.has_seen_valid_standing
            and (
                self.movement_direction == "descending"
                or confirmed in ("descending", "bottom")
            )
            and self._meaningful_descent_amplitude(metric_knee, float(smoothed))
        ):
            self._begin_rep_cycle(float(smoothed))

        if self.rep_in_progress:
            self.min_knee_angle_current_rep = min(
                self.min_knee_angle_current_rep or float(smoothed),
                float(smoothed),
            )
            if float(smoothed) < STANDING_EXIT:
                self.descent_started = True
            if float(smoothed) < VALID_DEPTH_ANGLE:
                self._reached_valid_depth = True
                self._rep_bottom_frame = self.frame_index
            self._check_in_rep_form(float(smoothed), torso_lean)

        self._update_form_evaluation(knee_angles, torso_lean)
        self._update_depth_evaluation(knee_angles, torso_lean)

        if self.rep_in_progress:
            self._update_rep_lifecycle_flags(float(smoothed), confirmed)

        if (
            reliable
            and self.rep_in_progress
            and self.standing_confirmed
            and confirmed == "standing"
            and not self.rep_counted
        ):
            rep_feedback = self._finish_rep_cycle(return_angle=float(smoothed))
        elif (
            reliable
            and confirmed == "standing"
            and prev_confirmed != "standing"
            and self._pending_rep_start
            and not self.rep_in_progress
        ):
            self._reset_rep_lifecycle_pending()

        self._prev_smoothed = float(smoothed)
        self.previous_state = prev_confirmed
        self.current_state = confirmed
        self._last_frame_confirmed_state = confirmed

        feedback = list(rep_feedback)
        if not feedback and confirmed == "standing" and self.ready_for_squat:
            feedback = ["Squat icin hazir pozisyondasin."]

        self.feedback = feedback
        self._store_last_angles(left, right, smoothed)
        return self._build_result(
            left=left,
            right=right,
            raw_average=raw_average,
            smoothed=smoothed,
            feedback=feedback,
            confidence=conf,
            is_valid_pose=True,
        )


# ---------------------------------------------------------------------------
# Pipeline helpers (used by video_processor orchestration; no shared globals)
# ---------------------------------------------------------------------------


def create_squat_analyzer(*, fps: float = 30.0) -> SquatAnalyzer:
    """Return a fresh squat analyzer instance (isolated mutable state)."""
    return SquatAnalyzer(fps=fps)


def squat_pose_landmark_indices(pose_landmark_enum: object) -> tuple[Any, ...]:
    """Landmark indices used for squat pose-confidence scoring."""
    L = pose_landmark_enum
    return (
        L.LEFT_HIP,
        L.LEFT_KNEE,
        L.LEFT_ANKLE,
        L.RIGHT_HIP,
        L.RIGHT_KNEE,
        L.RIGHT_ANKLE,
        L.LEFT_SHOULDER,
        L.RIGHT_SHOULDER,
    )


def draw_squat_knee_labels(
    frame: object,
    plm: object,
    pose_landmarks_enum: object,
    image_width: int,
    image_height: int,
    analysis: dict[str, Any],
) -> None:
    """Draw raw (R) and smoothed (S) knee angles beside each knee."""
    L = pose_landmarks_enum
    ka = analysis.get("kneeAngle") or {}
    raw_l, raw_r = ka.get("left"), ka.get("right")
    smooth = ka.get("average")

    lk = get_landmark_point(plm, L.LEFT_KNEE, image_width, image_height)
    rk = get_landmark_point(plm, L.RIGHT_KNEE, image_width, image_height)

    if lk is not None and (raw_l is not None or smooth is not None):
        r_s = f"{raw_l:.0f}" if raw_l is not None else "--"
        s_s = f"{smooth:.0f}" if smooth is not None else "--"
        cv2.putText(
            frame,
            f"R:{r_s} S:{s_s}",
            (lk["x"] + 10, lk["y"] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
    if rk is not None and (raw_r is not None or smooth is not None):
        r_s = f"{raw_r:.0f}" if raw_r is not None else "--"
        s_s = f"{smooth:.0f}" if smooth is not None else "--"
        cv2.putText(
            frame,
            f"R:{r_s} S:{s_s}",
            (rk["x"] + 10, rk["y"] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def draw_squat_hud(frame: object, analysis: dict[str, Any]) -> None:
    """Draw squat rep stats, state, smoothed angle, and latest feedback."""
    y0 = 28
    line_h = 28
    font_scale = 0.68
    ka = analysis.get("kneeAngle") or {}
    smooth = ka.get("average") or ka.get("smoothedAverage")
    fb_list = analysis.get("feedback") or []
    fb = fb_list[0] if fb_list else ""

    lines = [
        f"Rep Count: {analysis.get('rep_count', analysis.get('repCount', 0))}",
        f"Valid Reps: {analysis.get('valid_reps', 0)}",
        f"Invalid Reps: {analysis.get('invalid_reps', 0)}",
        f"State: {analysis.get('current_state', analysis.get('currentPhase', 'unknown'))}",
        f"Smooth Knee: {smooth:.1f}" if smooth is not None else "Smooth Knee: --",
        f"Form: {analysis.get('form_status', 'good')}",
    ]
    if fb:
        lines.append(f"Feedback: {fb}")
    for i, text in enumerate(lines):
        cv2.putText(
            frame,
            text,
            (12, y0 + i * line_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )


def _attach_frame_context(
    analysis: dict[str, Any],
    *,
    visibility_dict: dict[str, Any],
    camera_info: dict[str, Any],
) -> dict[str, Any]:
    analysis["landmark_visibility"] = visibility_dict
    analysis["camera"] = {
        "status": camera_info["status"],
        "body_scale": camera_info.get("body_scale"),
        "bbox_width_ratio": camera_info.get("bbox_width_ratio"),
        "bbox_height_ratio": camera_info.get("bbox_height_ratio"),
        "feedback": camera_info.get("feedback"),
    }
    return analysis


def process_squat_frame(
    analyzer: SquatAnalyzer,
    landmarks: object,
    pose_landmarks_enum: object,
    image_width: int,
    image_height: int,
    *,
    pose_confidence: float,
    effective_fps: float,
    landmark_visibility_usable: bool,
    visibility_dict: dict[str, Any],
    camera_info: dict[str, Any],
    low_confidence: bool,
    show_preview: bool = False,
    frame: object | None = None,
    last_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one squat frame through metrics + analyzer (existing behavior).

    Returns a small result dict for the video orchestration loop:
    selected_side, analysis (optional), counted_analyzed_frame, biomechanics.
    """
    squat_metrics = build_squat_frame_metrics(
        landmarks, pose_landmarks_enum, image_width, image_height
    )
    side = str(squat_metrics.get("selected_side") or "unavailable")
    result: dict[str, Any] = {
        "selected_side": side,
        "analysis": None,
        "counted_analyzed_frame": False,
        "biomechanics": None,
    }

    if (
        landmark_visibility_usable
        and not low_confidence
        and squat_metrics.get("average") is not None
    ):
        if squat_metrics.get("metrics_valid"):
            result["biomechanics"] = {
                "avg_knee": float(squat_metrics["avg_knee"]),
                "avg_hip": float(squat_metrics["avg_hip"]),
                "torso_lean": float(squat_metrics["torso_lean"]),
            }
        analysis = analyzer.analyze_frame(
            squat_metrics,
            pose_confidence=pose_confidence,
            torso_lean=squat_metrics.get("torso_lean"),
            fps=effective_fps,
            landmark_visibility_ok=True,
        )
        analysis = _attach_frame_context(
            analysis,
            visibility_dict=visibility_dict,
            camera_info=camera_info,
        )
        result["analysis"] = analysis
        result["counted_analyzed_frame"] = True
        if show_preview and frame is not None:
            draw_squat_hud(frame, analysis)
            draw_squat_knee_labels(
                frame,
                landmarks,
                pose_landmarks_enum,
                image_width,
                image_height,
                analysis,
            )
        return result

    if not landmark_visibility_usable:
        blocked = analyzer.analyze_frame(
            squat_metrics,
            pose_confidence=pose_confidence,
            torso_lean=squat_metrics.get("torso_lean"),
            fps=effective_fps,
            landmark_visibility_ok=False,
            landmark_visibility=visibility_dict,
        )
        blocked["landmark_visibility"] = visibility_dict
        result["analysis"] = blocked
        return result

    if show_preview and frame is not None and last_analysis is not None:
        draw_squat_hud(frame, last_analysis)
    return result
