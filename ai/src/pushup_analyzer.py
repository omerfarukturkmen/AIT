"""Push-up exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

import statistics
from collections import deque
from typing import Any

# Hysteresis elbow-angle thresholds (degrees)
UP_POSITION_ANGLE = 155.0
DESCENT_START_ANGLE = 145.0
BOTTOM_POSITION_ANGLE = 95.0
ASCENT_START_ANGLE = 105.0

DIRECTION_DEADZONE = 2.0
MIN_POSE_CONFIDENCE = 0.50
ELBOW_HISTORY_SIZE = 5

# Body-line form thresholds
HIP_SAG_OFFSET_THRESHOLD = 0.055
HIP_HIGH_OFFSET_THRESHOLD = -0.055
BACK_BEND_ANGLE_THRESHOLD = 160.0
ALIGNED_OFFSET_ABS = 0.035
ALIGNED_ANGLE_MIN = 165.0
FORM_CONFIRMATION_FRAMES = 3

FORM_MSG_HIPS_SAGGING = "Raise your hips and keep your body in a straight line"
FORM_MSG_HIPS_TOO_HIGH = "Lower your hips and keep your body in a straight line"
FORM_MSG_BACK_BENT = "Keep your back straight"
FORM_MSG_SHOULDER = "Check shoulder position"
FORM_MSG_GO_LOWER = "Go lower to complete the push-up"
FORM_MSG_COMPLETE_UP = "Complete the upward phase of the push-up"


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class PushupAnalyzer:
    """Robust up → descending → bottom → ascending → up push-up counter."""

    def __init__(self) -> None:
        self.exercise = "pushup"
        self.rep_count = 0
        self.valid_reps = 0
        self.invalid_reps = 0
        self.state = "up"

        self.candidate_state: str | None = None
        self.candidate_state_count = 0
        self.REQUIRED_STATE_FRAMES = 3

        # Backward-compatible alias kept in sync with reached_bottom
        self.had_bottom_position = False
        self.frame_count = 0

        self.feedback: list[str] = []
        self.current_angles: dict[str, float | None] = {
            "avg_elbow": None,
            "raw_avg_elbow": None,
            "smoothed_avg_elbow": None,
            "avg_shoulder": None,
            "avg_hip": None,
            "body_alignment_angle": None,
            "body_line_offset": None,
            "alignment_side": None,
        }

        self.form_errors: dict[str, int] = {
            "not_low_enough": 0,
            "hips_not_aligned": 0,
            "hips_too_high": 0,
            "back_bending": 0,
            "shoulder_position": 0,
            "low_confidence": 0,
            "angle_not_detected": 0,
        }

        # Smoothing / direction
        self._elbow_history: deque[float] = deque(maxlen=ELBOW_HISTORY_SIZE)
        self.previous_smoothed_elbow: float | None = None
        self.movement_direction: str = "unknown"
        self.smoothed_avg_elbow: float | None = None

        # Rep lifecycle
        self.rep_in_progress = False
        self.reached_bottom = False
        self.minimum_elbow_angle: float | None = None
        self.incomplete_rep_recorded = False
        self.session_finalized = False
        self._sticky_feedback: list[str] = []

        # Body-line form tracking
        self.current_form_state: str = "unknown"
        self.candidate_form_state: str | None = None
        self.candidate_form_frames: int = 0
        self.current_rep_hips_sagging: bool = False
        self.current_rep_hips_too_high: bool = False
        self.current_rep_back_bent: bool = False
        self.current_rep_shoulder_bad: bool = False
        self.body_alignment_angle: float | None = None
        self.body_line_offset: float | None = None
        self.alignment_side: str = "unknown"

    def _reset_rep_form_flags(self) -> None:
        self.current_rep_hips_sagging = False
        self.current_rep_hips_too_high = False
        self.current_rep_back_bent = False
        self.current_rep_shoulder_bad = False
        self.candidate_form_state = None
        self.candidate_form_frames = 0

    def _commit_rep_form_errors(self) -> None:
        """Write per-rep form booleans into session counters once."""
        if self.current_rep_hips_sagging:
            self.form_errors["hips_not_aligned"] += 1
        if self.current_rep_hips_too_high:
            self.form_errors["hips_too_high"] += 1
        if self.current_rep_back_bent:
            self.form_errors["back_bending"] += 1
        if self.current_rep_shoulder_bad:
            self.form_errors["shoulder_position"] += 1
        self._reset_rep_form_flags()

    def _reset_rep_temp(self) -> None:
        self.rep_in_progress = False
        self.reached_bottom = False
        self.had_bottom_position = False
        self.minimum_elbow_angle = None
        self.incomplete_rep_recorded = False

    def _update_smoothed(self, raw_elbow: float) -> float:
        self._elbow_history.append(raw_elbow)
        smoothed = float(statistics.median(self._elbow_history))
        self.smoothed_avg_elbow = smoothed
        return smoothed

    def _update_direction(self, smoothed: float) -> str:
        if self.previous_smoothed_elbow is None:
            self.movement_direction = "unknown"
        else:
            delta = smoothed - self.previous_smoothed_elbow
            if delta <= -DIRECTION_DEADZONE:
                self.movement_direction = "descending"
            elif delta >= DIRECTION_DEADZONE:
                self.movement_direction = "ascending"
            else:
                self.movement_direction = "stable"
        return self.movement_direction

    def _predict_state(self, smoothed: float, direction: str) -> str:
        """Propose next state using hysteresis + movement direction."""
        state = self.state
        desc_ok = direction in ("descending", "stable")
        asc_ok = direction in ("ascending", "stable")

        if state == "up":
            # Never skip descending even if angle is already near bottom.
            if smoothed <= DESCENT_START_ANGLE and desc_ok:
                return "descending"
            return "up"

        if state == "descending":
            if smoothed <= BOTTOM_POSITION_ANGLE:
                return "bottom"
            if smoothed >= UP_POSITION_ANGLE:
                return "up"
            return "descending"

        if state == "bottom":
            if smoothed > ASCENT_START_ANGLE and asc_ok:
                return "ascending"
            return "bottom"

        if state == "ascending":
            if smoothed >= UP_POSITION_ANGLE and asc_ok:
                return "up"
            if smoothed <= BOTTOM_POSITION_ANGLE:
                return "bottom"
            return "ascending"

        return state

    def _record_incomplete(self, message: str, *, count_not_low_enough: bool) -> None:
        if self.incomplete_rep_recorded:
            return
        self.invalid_reps += 1
        self.incomplete_rep_recorded = True
        if count_not_low_enough:
            self.form_errors["not_low_enough"] += 1
        if message not in self._sticky_feedback:
            self._sticky_feedback.append(message)
        if message not in self.feedback:
            self.feedback = list(self.feedback) + [message]

    def _apply_confirmed_transition(self, previous_state: str, new_state: str) -> None:
        if previous_state == "up" and new_state == "descending":
            self.rep_in_progress = True
            self.reached_bottom = False
            self.had_bottom_position = False
            self.minimum_elbow_angle = self.smoothed_avg_elbow
            self.incomplete_rep_recorded = False
            self._reset_rep_form_flags()

        if new_state == "bottom":
            self.reached_bottom = True
            self.had_bottom_position = True

        if previous_state == "descending" and new_state == "up":
            # Returned up without a confirmed bottom → incomplete.
            if not self.reached_bottom:
                self._record_incomplete(
                    FORM_MSG_GO_LOWER,
                    count_not_low_enough=True,
                )
            self._commit_rep_form_errors()
            self._reset_rep_temp()
            return

        if previous_state == "ascending" and new_state == "up":
            if self.reached_bottom:
                self.rep_count += 1
                self.valid_reps += 1
                # Successful rep clears sticky incomplete hints.
                self._sticky_feedback = [
                    m
                    for m in self._sticky_feedback
                    if m not in (FORM_MSG_GO_LOWER, FORM_MSG_COMPLETE_UP)
                ]
            self._commit_rep_form_errors()
            self._reset_rep_temp()

    def _confirm_state(self, target_state: str) -> None:
        """Apply candidate-state confirmation over REQUIRED_STATE_FRAMES."""
        if target_state == self.state:
            self.candidate_state = None
            self.candidate_state_count = 0
            return

        if target_state == self.candidate_state:
            self.candidate_state_count += 1
        else:
            self.candidate_state = target_state
            self.candidate_state_count = 1

        if self.candidate_state_count < self.REQUIRED_STATE_FRAMES:
            return

        previous_state = self.state
        self.state = target_state
        self.candidate_state = None
        self.candidate_state_count = 0
        self._apply_confirmed_transition(previous_state, self.state)

    def _classify_form(
        self,
        offset: float | None,
        angle: float | None,
    ) -> str:
        """Return target form label, 'hold' for hysteresis band, or 'unknown'."""
        if offset is None or angle is None:
            return "unknown"

        if offset >= HIP_SAG_OFFSET_THRESHOLD:
            return "hips_sagging"
        if offset <= HIP_HIGH_OFFSET_THRESHOLD:
            return "hips_too_high"
        if abs(offset) <= ALIGNED_OFFSET_ABS and angle >= ALIGNED_ANGLE_MIN:
            return "aligned"
        if angle < BACK_BEND_ANGLE_THRESHOLD:
            return "back_bent"
        return "hold"

    def _mark_confirmed_form(self, form_state: str) -> None:
        self.current_form_state = form_state
        # Per-rep error flags only accumulate during an active push-up cycle.
        if not self.rep_in_progress:
            return
        if form_state == "hips_sagging":
            self.current_rep_hips_sagging = True
        elif form_state == "hips_too_high":
            self.current_rep_hips_too_high = True
        elif form_state == "back_bent":
            self.current_rep_back_bent = True

    def _update_form_state(self, offset: float | None, angle: float | None) -> None:
        classified = self._classify_form(offset, angle)

        if classified == "unknown":
            # Keep current form; do not cancel an in-progress rep.
            return

        if classified == "hold":
            return

        if classified == "aligned":
            self.candidate_form_state = None
            self.candidate_form_frames = 0
            self.current_form_state = "aligned"
            return

        if classified == self.candidate_form_state:
            self.candidate_form_frames += 1
        else:
            self.candidate_form_state = classified
            self.candidate_form_frames = 1

        if self.candidate_form_frames >= FORM_CONFIRMATION_FRAMES:
            self._mark_confirmed_form(classified)
            self.candidate_form_state = None
            self.candidate_form_frames = 0

    def _compose_feedback(self, *, camera_status: str | None) -> None:
        messages: list[str] = []

        # Priority: sticky incomplete hints / go-lower first among motion cues,
        # then camera, then body-line form, then shoulder.
        for sticky in self._sticky_feedback:
            if sticky not in messages:
                messages.append(sticky)

        if camera_status in ("too_far", "too_close", "unknown"):
            cam_msg = {
                "too_far": "Move closer to camera",
                "too_close": "Move away from camera",
                "unknown": "Camera distance unknown",
            }.get(camera_status)
            if cam_msg and cam_msg not in messages:
                messages.append(cam_msg)

        form_msg = {
            "hips_sagging": FORM_MSG_HIPS_SAGGING,
            "hips_too_high": FORM_MSG_HIPS_TOO_HIGH,
            "back_bent": FORM_MSG_BACK_BENT,
        }.get(self.current_form_state)
        if form_msg and form_msg not in messages:
            messages.append(form_msg)

        # Also surface confirmed-but-not-current flags for this rep.
        if self.current_rep_hips_sagging and FORM_MSG_HIPS_SAGGING not in messages:
            if self.current_form_state != "aligned":
                messages.append(FORM_MSG_HIPS_SAGGING)
        if self.current_rep_hips_too_high and FORM_MSG_HIPS_TOO_HIGH not in messages:
            if self.current_form_state != "aligned":
                messages.append(FORM_MSG_HIPS_TOO_HIGH)
        if self.current_rep_back_bent and FORM_MSG_BACK_BENT not in messages:
            if self.current_form_state != "aligned":
                messages.append(FORM_MSG_BACK_BENT)

        avg_shoulder = _as_float(self.current_angles.get("avg_shoulder"))
        if avg_shoulder is not None and avg_shoulder < 30:
            self.current_rep_shoulder_bad = True
            if FORM_MSG_SHOULDER not in messages:
                messages.append(FORM_MSG_SHOULDER)

        if not messages:
            if self.current_form_state == "aligned":
                messages = ["Good push-up form"]
            else:
                messages = ["Good push-up form"]

        # Deduplicate while preserving order.
        deduped: list[str] = []
        for msg in messages:
            if msg not in deduped:
                deduped.append(msg)
        self.feedback = deduped

    def analyze_frame(
        self,
        pushup_angles: dict[str, Any] | None,
        pose_confidence: float | None = None,
        camera_status: str | None = None,
    ) -> dict[str, Any]:
        self.frame_count += 1

        angles = pushup_angles if isinstance(pushup_angles, dict) else {}
        raw_elbow = _as_float(angles.get("avg_elbow"))
        avg_shoulder = _as_float(angles.get("avg_shoulder"))
        avg_hip = _as_float(angles.get("avg_hip"))
        body_alignment_angle = _as_float(angles.get("body_alignment_angle"))
        body_line_offset = _as_float(angles.get("body_line_offset"))
        alignment_side = angles.get("alignment_side")
        if not isinstance(alignment_side, str) or alignment_side not in {
            "left",
            "right",
            "both",
            "unknown",
        }:
            alignment_side = "unknown"

        self.body_alignment_angle = body_alignment_angle
        self.body_line_offset = body_line_offset
        self.alignment_side = alignment_side

        # Preserve raw elbow in current_angles for backward compatibility.
        self.current_angles = {
            "avg_elbow": raw_elbow,
            "raw_avg_elbow": raw_elbow,
            "smoothed_avg_elbow": self.smoothed_avg_elbow,
            "avg_shoulder": avg_shoulder,
            "avg_hip": avg_hip,
            "body_alignment_angle": body_alignment_angle,
            "body_line_offset": body_line_offset,
            "alignment_side": alignment_side,
        }

        if pose_confidence is not None:
            try:
                conf = float(pose_confidence)
            except (TypeError, ValueError):
                conf = 0.0
            if conf < MIN_POSE_CONFIDENCE:
                self.form_errors["low_confidence"] += 1
                self.feedback = ["Low pose confidence"]
                # Do not touch history, direction memory, candidates, form, or counters.
                return self._frame_snapshot()

        if raw_elbow is None:
            self.form_errors["angle_not_detected"] += 1
            self.feedback = ["Elbow angle not detected"]
            return self._frame_snapshot()

        # A new valid analysis frame can reopen a finalized session.
        self.session_finalized = False

        smoothed = self._update_smoothed(raw_elbow)
        self.current_angles["smoothed_avg_elbow"] = smoothed
        direction = self._update_direction(smoothed)

        if self.rep_in_progress:
            if self.minimum_elbow_angle is None or smoothed < self.minimum_elbow_angle:
                self.minimum_elbow_angle = smoothed

        target = self._predict_state(smoothed, direction)
        self._confirm_state(target)
        self._update_form_state(body_line_offset, body_alignment_angle)
        self._compose_feedback(camera_status=camera_status)

        self.previous_smoothed_elbow = smoothed
        return self._frame_snapshot()

    def _current_rep_form_errors(self) -> dict[str, bool]:
        return {
            "hips_sagging": self.current_rep_hips_sagging,
            "hips_too_high": self.current_rep_hips_too_high,
            "back_bent": self.current_rep_back_bent,
        }

    def _frame_snapshot(self) -> dict[str, Any]:
        return {
            "exercise": self.exercise,
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "current_state": self.state,
            "state": self.state,
            "feedback": list(self.feedback),
            "form_errors": dict(self.form_errors),
            "angles": dict(self.current_angles),
            "rep_in_progress": self.rep_in_progress,
            "reached_bottom": self.reached_bottom,
            "movement_direction": self.movement_direction,
            "minimum_elbow_angle": self.minimum_elbow_angle,
            "smoothed_avg_elbow": self.smoothed_avg_elbow,
            "current_form_state": self.current_form_state,
            "body_alignment_angle": self.body_alignment_angle,
            "body_line_offset": self.body_line_offset,
            "alignment_side": self.alignment_side,
            "current_rep_form_errors": self._current_rep_form_errors(),
        }

    def finalize_session(self) -> None:
        if self.session_finalized:
            return
        self.session_finalized = True

        if self.rep_in_progress and self.state != "up":
            if self.reached_bottom:
                self._record_incomplete(
                    FORM_MSG_COMPLETE_UP,
                    count_not_low_enough=False,
                )
            else:
                self._record_incomplete(
                    FORM_MSG_GO_LOWER,
                    count_not_low_enough=True,
                )
            self._commit_rep_form_errors()
            self._reset_rep_temp()

        if self.rep_count == 0:
            msg = "No complete push-up detected"
            if msg not in self.feedback:
                self.feedback = list(self.feedback) + [msg]

    def get_result(self, video_path: str | None = None) -> dict[str, Any]:
        _ = video_path
        self.finalize_session()
        return {
            "exercise": "pushup",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "final_state": self.state,
            "current_state": self.state,
            "state": self.state,
            "form_errors": dict(self.form_errors),
            "feedback": list(self.feedback),
            "angles": {
                "avg_elbow": self.current_angles.get("avg_elbow"),
                "raw_avg_elbow": self.current_angles.get("raw_avg_elbow"),
                "smoothed_avg_elbow": self.current_angles.get("smoothed_avg_elbow"),
                "avg_shoulder": self.current_angles.get("avg_shoulder"),
                "avg_hip": self.current_angles.get("avg_hip"),
                "body_alignment_angle": self.current_angles.get("body_alignment_angle"),
                "body_line_offset": self.current_angles.get("body_line_offset"),
                "alignment_side": self.current_angles.get("alignment_side"),
            },
            "rep_in_progress": self.rep_in_progress,
            "reached_bottom": self.reached_bottom,
            "movement_direction": self.movement_direction,
            "minimum_elbow_angle": self.minimum_elbow_angle,
            "smoothed_avg_elbow": self.smoothed_avg_elbow,
            "current_form_state": self.current_form_state,
            "body_alignment_angle": self.body_alignment_angle,
            "body_line_offset": self.body_line_offset,
            "alignment_side": self.alignment_side,
        }
