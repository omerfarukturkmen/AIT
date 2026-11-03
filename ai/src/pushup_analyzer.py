"""Push-up exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

import statistics
from collections import deque
from typing import Any

import cv2

from angle_utils import calculate_pushup_angles
from visibility_utils import visibility_feedback_messages
from camera_utils import camera_feedback_for_status

# Hysteresis elbow-angle thresholds (degrees)
UP_POSITION_ANGLE = 155.0
DESCENT_START_ANGLE = 145.0
BOTTOM_POSITION_ANGLE = 95.0
ASCENT_START_ANGLE = 105.0

DIRECTION_DEADZONE = 2.0
MIN_POSE_CONFIDENCE = 0.50
ELBOW_HISTORY_SIZE = 5

# Rep lifecycle guards
UP_CONFIRMATION_FRAMES = 3
MIN_DESCENT_ELBOW_CHANGE = 15.0

# Body-line form thresholds
HIP_SAG_OFFSET_THRESHOLD = 0.055
HIP_HIGH_OFFSET_THRESHOLD = -0.055
BACK_BEND_ANGLE_THRESHOLD = 160.0
ALIGNED_OFFSET_ABS = 0.035
ALIGNED_ANGLE_MIN = 165.0
FORM_CONFIRMATION_FRAMES = 3

# Shoulder angle = hip → shoulder → elbow at shoulder vertex (upper arm vs torso).
# Larger angle ≈ elbows flared away from the body.
SHOULDER_ALIGNMENT_MIN = 35.0
SHOULDER_ALIGNMENT_MAX = 95.0

FORM_MSG_HIPS_SAGGING = "Raise your hips and keep your body in a straight line"
FORM_MSG_HIPS_TOO_HIGH = "Lower your hips and keep your body in a straight line"
FORM_MSG_BACK_BENT = "Keep your back straight"
FORM_MSG_SHOULDER = "Check shoulder position"
FORM_MSG_SHOULDER_ALIGN = "Keep your shoulders stable and aligned"
FORM_MSG_ELBOWS_FLARED = "Keep your elbows closer to your body"
FORM_MSG_GO_LOWER = "Go lower to complete the push-up"
FORM_MSG_COMPLETE_UP = "Complete the upward phase of the push-up"
FORM_MSG_LOW_CONFIDENCE = "Low pose confidence"
FORM_MSG_ANGLE_NOT_DETECTED = "Elbow angle not detected"
FORM_MSG_GOOD_FORM = "Good push-up form"
FORM_MSG_NO_COMPLETE = "No complete push-up detected"

# Canonical issue / lifecycle → user-facing feedback (single source of truth).
FORM_FEEDBACK_MESSAGES: dict[str, str] = {
    "hips_sagging": FORM_MSG_HIPS_SAGGING,
    "hips_too_high": FORM_MSG_HIPS_TOO_HIGH,
    "back_bent": FORM_MSG_BACK_BENT,
    "not_low_enough": FORM_MSG_GO_LOWER,
    "incomplete_up": FORM_MSG_COMPLETE_UP,
    "elbows_flared": FORM_MSG_ELBOWS_FLARED,
    "shoulder_alignment_issue": FORM_MSG_SHOULDER_ALIGN,
}

# Deterministic form-issue ordering for feedback output.
FORM_ISSUE_PRIORITY: tuple[str, ...] = (
    "hips_sagging",
    "hips_too_high",
    "back_bent",
    "elbows_flared",
    "shoulder_alignment_issue",
)

_INCOMPLETE_FEEDBACK_KEYS: tuple[str, ...] = ("not_low_enough", "incomplete_up")

_ISSUE_TO_FORM_ERROR: dict[str, str] = {
    "hips_sagging": "hips_not_aligned",
    "hips_too_high": "hips_too_high",
    "back_bent": "back_bending",
    "shoulder_alignment_issue": "shoulder_position",
    "elbows_flared": "elbows_flared",
}

_ISSUE_TO_MESSAGE: dict[str, str] = {
    "hips_sagging": FORM_MSG_HIPS_SAGGING,
    "hips_too_high": FORM_MSG_HIPS_TOO_HIGH,
    "back_bent": FORM_MSG_BACK_BENT,
    "shoulder_alignment_issue": FORM_MSG_SHOULDER_ALIGN,
    "elbows_flared": FORM_MSG_ELBOWS_FLARED,
}


def _dedupe_feedback(messages: list[str]) -> list[str]:
    """Ordered deduplication — preserves first occurrence order."""
    seen: set[str] = set()
    out: list[str] = []
    for msg in messages:
        if msg and msg not in seen:
            seen.add(msg)
            out.append(msg)
    return out


def _message_for_issue(issue: str) -> str | None:
    return FORM_FEEDBACK_MESSAGES.get(issue) or _ISSUE_TO_MESSAGE.get(issue)


def _issues_to_feedback(issues: set[str] | list[str]) -> list[str]:
    issue_set = set(issues)
    messages: list[str] = []
    for issue in FORM_ISSUE_PRIORITY:
        if issue not in issue_set:
            continue
        msg = _message_for_issue(issue)
        if msg:
            messages.append(msg)
    return messages


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out or out in (float("inf"), float("-inf")):
        return None
    return out


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
        self._session_feedback: list[str] = []
        self.last_rep_feedback: list[str] = []
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
            "elbows_flared": 0,
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

        # Rep lifecycle guards (mid-video start, double-count, descent amplitude)
        self.has_seen_valid_up = False
        self._valid_up_frame_count = 0
        self._up_reference_elbow: float | None = None
        self.rep_start_elbow_angle: float | None = None
        self.rep_counted = False
        self._visibility_blocked_during_rep = False

        # Combined form evaluation (independent of movement state machine)
        self.current_form_state: str = "unknown"
        self.active_form_issues: list[str] = []
        self.current_form_metrics: dict[str, float | None] = {
            "elbow_angle": None,
            "shoulder_angle": None,
            "hip_angle": None,
            "body_alignment_angle": None,
            "body_line_offset": None,
        }
        self.candidate_form_issues: set[str] = set()
        self.candidate_form_frames: int = 0
        self.confirmed_form_issues: set[str] = set()
        self.current_rep_form_issues: set[str] = set()
        self.last_rep_form_issues: list[str] = []
        self._issue_segment_active: dict[str, bool] = {
            "elbows_flared": False,
            "shoulder_alignment_issue": False,
        }

        # Per-rep body-line flags (committed once per rep at rep end)
        self.current_rep_hips_sagging: bool = False
        self.current_rep_hips_too_high: bool = False
        self.current_rep_back_bent: bool = False
        self.current_rep_shoulder_bad: bool = False
        self.current_rep_elbows_flared: bool = False

        # Completed-attempt history for scoring (internal; not a backend contract)
        self.rep_history: list[dict[str, Any]] = []
        self._rep_start_frame: int | None = None
        self._rep_bottom_frame: int | None = None
        self._rep_max_abs_body_line_offset: float | None = None
        self._rep_min_body_alignment_angle: float | None = None

        # Legacy single-state debounce aliases (kept for tests that inspect them)
        self.candidate_form_state: str | None = None

        self.body_alignment_angle: float | None = None
        self.body_line_offset: float | None = None
        self.alignment_side: str = "unknown"

    def _reset_rep_form_flags(self) -> None:
        self.current_rep_hips_sagging = False
        self.current_rep_hips_too_high = False
        self.current_rep_back_bent = False
        self.current_rep_shoulder_bad = False
        self.current_rep_elbows_flared = False
        self.candidate_form_issues = set()
        self.candidate_form_frames = 0
        self.candidate_form_state = None

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
        if self.current_rep_form_issues:
            self.last_rep_form_issues = sorted(self.current_rep_form_issues)
            self.last_rep_feedback = _issues_to_feedback(self.current_rep_form_issues)
            self._record_session_feedback(self.last_rep_feedback)
        else:
            self.last_rep_feedback = []
        self._reset_rep_form_flags()

    def _reset_rep_temp(self) -> None:
        self.rep_in_progress = False
        self.reached_bottom = False
        self.had_bottom_position = False
        self.minimum_elbow_angle = None
        self.incomplete_rep_recorded = False
        self.rep_start_elbow_angle = None
        self.rep_counted = False
        self._rep_start_frame = None
        self._rep_bottom_frame = None
        self._rep_max_abs_body_line_offset = None
        self._rep_min_body_alignment_angle = None

    def _reset_rep_metric_tracking(self) -> None:
        self._rep_start_frame = self.frame_count
        self._rep_bottom_frame = None
        self._rep_max_abs_body_line_offset = None
        self._rep_min_body_alignment_angle = None

    def _update_rep_alignment_tracking(
        self,
        offset: float | None,
        angle: float | None,
    ) -> None:
        if not self.rep_in_progress:
            return
        if offset is not None:
            abs_offset = abs(float(offset))
            if (
                self._rep_max_abs_body_line_offset is None
                or abs_offset > self._rep_max_abs_body_line_offset
            ):
                self._rep_max_abs_body_line_offset = abs_offset
        if angle is not None:
            angle_v = float(angle)
            if (
                self._rep_min_body_alignment_angle is None
                or angle_v < self._rep_min_body_alignment_angle
            ):
                self._rep_min_body_alignment_angle = angle_v

    def _append_rep_history(
        self,
        *,
        valid: bool,
        incomplete_reason: str | None = None,
    ) -> None:
        """Record a finished attempt for scoring. Does not change counters."""
        end_frame = self.frame_count
        start_frame = self._rep_start_frame
        if start_frame is None:
            start_frame = end_frame
        duration = max(0, end_frame - start_frame + 1)
        issues = sorted(self.current_rep_form_issues)
        errors = list(issues)
        if incomplete_reason and incomplete_reason not in errors:
            errors.append(incomplete_reason)
        min_elbow = self.minimum_elbow_angle
        start_elbow = self.rep_start_elbow_angle
        self.rep_history.append(
            {
                "rep_index": len(self.rep_history) + 1,
                "start_frame": start_frame,
                "bottom_frame": self._rep_bottom_frame,
                "end_frame": end_frame,
                "duration_frames": duration,
                "min_elbow_angle": (
                    round(float(min_elbow), 2) if min_elbow is not None else None
                ),
                "rep_start_elbow_angle": (
                    round(float(start_elbow), 2) if start_elbow is not None else None
                ),
                "reached_bottom": bool(self.reached_bottom or self.had_bottom_position),
                "valid": valid,
                "completed_full_cycle": valid,
                "form_issues": issues,
                "errors": errors,
                "max_abs_body_line_offset": (
                    round(float(self._rep_max_abs_body_line_offset), 4)
                    if self._rep_max_abs_body_line_offset is not None
                    else None
                ),
                "min_body_alignment_angle": (
                    round(float(self._rep_min_body_alignment_angle), 2)
                    if self._rep_min_body_alignment_angle is not None
                    else None
                ),
                "usable": not self._visibility_blocked_during_rep,
                "visibility_blocked": self._visibility_blocked_during_rep,
            }
        )

    def _update_valid_up_tracking(self, smoothed: float) -> None:
        """Track consecutive confirmed-UP frames before allowing a new rep."""
        if self.state == "up" and smoothed >= UP_POSITION_ANGLE:
            self._valid_up_frame_count += 1
            self._up_reference_elbow = smoothed
            if self._valid_up_frame_count >= UP_CONFIRMATION_FRAMES:
                self.has_seen_valid_up = True
        elif self.state == "up":
            self._valid_up_frame_count = 0

    def _descent_amplitude_met(self, smoothed: float) -> bool:
        reference = self._up_reference_elbow
        if reference is None:
            return True
        return reference - smoothed >= MIN_DESCENT_ELBOW_CHANGE

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
            if not self.has_seen_valid_up:
                return "up"
            if (
                smoothed <= DESCENT_START_ANGLE
                and desc_ok
                and self._descent_amplitude_met(smoothed)
            ):
                return "descending"
            return "up"

        if state == "descending":
            if smoothed <= BOTTOM_POSITION_ANGLE and desc_ok:
                return "bottom"
            if smoothed >= UP_POSITION_ANGLE and asc_ok:
                return "up"
            return "descending"

        if state == "bottom":
            if smoothed > ASCENT_START_ANGLE and asc_ok:
                return "ascending"
            return "bottom"

        if state == "ascending":
            if smoothed >= UP_POSITION_ANGLE and asc_ok:
                return "up"
            if smoothed <= BOTTOM_POSITION_ANGLE and desc_ok:
                return "bottom"
            return "ascending"

        return state

    def _record_session_feedback(self, messages: list[str]) -> None:
        for msg in messages:
            if msg and msg not in self._session_feedback:
                self._session_feedback.append(msg)

    def _record_incomplete(self, message: str, *, count_not_low_enough: bool) -> None:
        if self.incomplete_rep_recorded:
            return
        self.invalid_reps += 1
        self.incomplete_rep_recorded = True
        if count_not_low_enough:
            self.form_errors["not_low_enough"] += 1
        if message not in self._sticky_feedback:
            self._sticky_feedback.append(message)
        self._record_session_feedback([message])

    def _apply_confirmed_transition(self, previous_state: str, new_state: str) -> None:
        if previous_state == "up" and new_state == "descending":
            self.rep_in_progress = True
            self.reached_bottom = False
            self.had_bottom_position = False
            self.rep_counted = False
            self._visibility_blocked_during_rep = False
            self.rep_start_elbow_angle = self._up_reference_elbow or self.smoothed_avg_elbow
            self.minimum_elbow_angle = self.smoothed_avg_elbow
            self.incomplete_rep_recorded = False
            self._reset_rep_form_flags()
            self._reset_rep_metric_tracking()
            if self.confirmed_form_issues:
                self._mark_rep_form_flags(set(self.confirmed_form_issues))

        if new_state == "bottom":
            self.reached_bottom = True
            self.had_bottom_position = True
            if self._rep_bottom_frame is None:
                self._rep_bottom_frame = self.frame_count

        if previous_state == "descending" and new_state == "up":
            # Returned up without a confirmed bottom → incomplete.
            if not self.reached_bottom:
                self._record_incomplete(
                    FORM_MSG_GO_LOWER,
                    count_not_low_enough=True,
                )
                self._append_rep_history(
                    valid=False,
                    incomplete_reason="not_low_enough",
                )
            self._commit_rep_form_errors()
            self._reset_rep_temp()
            return

        if previous_state == "ascending" and new_state == "up":
            if self.reached_bottom and not self.rep_counted:
                self.rep_count += 1
                self.valid_reps += 1
                self.rep_counted = True
                self._append_rep_history(valid=True)
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

    def _is_active_pushup_phase(self) -> bool:
        return self.state in ("descending", "bottom", "ascending")

    def _classify_body_issues(
        self,
        offset: float | None,
        angle: float | None,
    ) -> set[str] | None:
        """Return issue codes, empty set if aligned, None if metrics missing/hold."""
        if offset is None or angle is None:
            return None

        if offset >= HIP_SAG_OFFSET_THRESHOLD:
            return {"hips_sagging"}
        if offset <= HIP_HIGH_OFFSET_THRESHOLD:
            return {"hips_too_high"}
        if abs(offset) <= ALIGNED_OFFSET_ABS and angle >= ALIGNED_ANGLE_MIN:
            return set()
        if angle < BACK_BEND_ANGLE_THRESHOLD:
            return {"back_bent"}
        return None  # hysteresis hold — freeze debounce

    def _shoulder_issues(self, shoulder: float | None) -> set[str]:
        if shoulder is None or not self._is_active_pushup_phase():
            return set()
        if shoulder > SHOULDER_ALIGNMENT_MAX:
            return {"elbows_flared"}
        if shoulder < SHOULDER_ALIGNMENT_MIN:
            return {"shoulder_alignment_issue"}
        return set()

    def _detect_frame_form_issues(
        self,
        shoulder: float | None,
        offset: float | None,
        angle: float | None,
    ) -> set[str] | None:
        """Combined elbow/shoulder/body form issues for one frame."""
        if offset is None or angle is None or shoulder is None:
            return None
        body = self._classify_body_issues(offset, angle)
        if body is None:
            return None
        return body | self._shoulder_issues(shoulder)

    def _form_state_from_issues(self, issues: set[str]) -> str:
        if not issues:
            return "aligned"
        if len(issues) > 1:
            return "multiple_form_issues"
        return next(iter(issues))

    def _sync_legacy_candidate_form_state(self, issues: set[str]) -> None:
        if not issues:
            self.candidate_form_state = None
        elif len(issues) == 1:
            self.candidate_form_state = next(iter(issues))
        else:
            self.candidate_form_state = "multiple_form_issues"

    def _mark_rep_form_flags(self, issues: set[str]) -> None:
        if not self.rep_in_progress:
            return
        if "hips_sagging" in issues:
            self.current_rep_hips_sagging = True
        if "hips_too_high" in issues:
            self.current_rep_hips_too_high = True
        if "back_bent" in issues:
            self.current_rep_back_bent = True
        if "shoulder_alignment_issue" in issues:
            self.current_rep_shoulder_bad = True
        if "elbows_flared" in issues:
            self.current_rep_elbows_flared = True
        self.current_rep_form_issues.update(issues)

    def _apply_confirmed_form_issues(self, issues: set[str]) -> None:
        prev = set(self.confirmed_form_issues)
        cleared = prev - issues
        new_issues = issues - prev

        self.confirmed_form_issues = set(issues)
        self.active_form_issues = sorted(issues)
        self.current_form_state = self._form_state_from_issues(issues)
        self._mark_rep_form_flags(issues)

        for issue in new_issues:
            if issue not in _ISSUE_TO_FORM_ERROR:
                continue
            if issue in ("elbows_flared", "shoulder_alignment_issue"):
                if not self._issue_segment_active.get(issue, False):
                    self._issue_segment_active[issue] = True
                    self.form_errors[_ISSUE_TO_FORM_ERROR[issue]] += 1

        if new_issues:
            self._record_session_feedback(_issues_to_feedback(new_issues))

        for issue in cleared:
            if issue in self._issue_segment_active:
                self._issue_segment_active[issue] = False

    def _update_form_evaluation(
        self,
        shoulder: float | None,
        offset: float | None,
        angle: float | None,
    ) -> None:
        frame_issues = self._detect_frame_form_issues(shoulder, offset, angle)
        if frame_issues is None:
            if offset is None or angle is None or shoulder is None:
                self.current_form_state = "metrics_incomplete"
                self.active_form_issues = []
            return

        if frame_issues == self.candidate_form_issues:
            self.candidate_form_frames += 1
        else:
            self.candidate_form_issues = set(frame_issues)
            self.candidate_form_frames = 1

        self._sync_legacy_candidate_form_state(self.candidate_form_issues)

        if self.candidate_form_frames < FORM_CONFIRMATION_FRAMES:
            return

        self._apply_confirmed_form_issues(set(frame_issues))

    def _update_form_metrics(
        self,
        *,
        smoothed_elbow: float | None,
        shoulder: float | None,
        hip: float | None,
        body_alignment_angle: float | None,
        body_line_offset: float | None,
    ) -> None:
        self.current_form_metrics = {
            "elbow_angle": smoothed_elbow,
            "shoulder_angle": shoulder,
            "hip_angle": hip,
            "body_alignment_angle": body_alignment_angle,
            "body_line_offset": body_line_offset,
        }

    def _compose_feedback(
        self,
        *,
        camera_status: str | None,
        metrics_reliable: bool = True,
    ) -> None:
        messages: list[str] = []

        # 4. Confirmed incomplete movement feedback (never while still descending).
        for key in _INCOMPLETE_FEEDBACK_KEYS:
            msg = FORM_FEEDBACK_MESSAGES[key]
            if msg in self._sticky_feedback:
                messages.append(msg)

        # 3. Camera framing warnings (confirmed status passed from pipeline).
        if camera_status in ("too_far", "too_close"):
            cam_msg = camera_feedback_for_status(camera_status)
            if cam_msg:
                messages.append(cam_msg)

        if metrics_reliable:
            # 5–9. Frame-level confirmed form issues (debounced).
            for issue in FORM_ISSUE_PRIORITY:
                if issue not in self.confirmed_form_issues:
                    continue
                msg = _message_for_issue(issue)
                if msg:
                    messages.append(msg)

            # Rep-level confirmed issues persist for the active rep.
            if self.rep_in_progress:
                for issue in FORM_ISSUE_PRIORITY:
                    if issue not in self.current_rep_form_issues:
                        continue
                    msg = _message_for_issue(issue)
                    if msg:
                        messages.append(msg)

        if not messages:
            messages = [FORM_MSG_GOOD_FORM]

        self.feedback = _dedupe_feedback(messages)

    def _build_session_feedback_summary(self) -> list[str]:
        """Deterministic session-wide feedback summary for final result."""
        messages: list[str] = []

        for key in _INCOMPLETE_FEEDBACK_KEYS:
            msg = FORM_FEEDBACK_MESSAGES[key]
            if msg in self._session_feedback:
                messages.append(msg)

        for issue in FORM_ISSUE_PRIORITY:
            msg = _message_for_issue(issue)
            if msg and msg in self._session_feedback:
                messages.append(msg)

        for msg in self._session_feedback:
            if msg not in messages:
                messages.append(msg)

        if self.rep_count == 0 and FORM_MSG_NO_COMPLETE not in messages:
            if FORM_MSG_NO_COMPLETE in self._session_feedback or self.session_finalized:
                messages.append(FORM_MSG_NO_COMPLETE)

        return _dedupe_feedback(messages)

    def analyze_frame(
        self,
        pushup_angles: dict[str, Any] | None,
        pose_confidence: float | None = None,
        camera_status: str | None = None,
        landmark_visibility_ok: bool | None = None,
        landmark_visibility: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.frame_count += 1

        if landmark_visibility_ok is False:
            if self.rep_in_progress:
                self._visibility_blocked_during_rep = True
            self.feedback = visibility_feedback_messages()
            snap = self._frame_snapshot()
            if landmark_visibility is not None:
                snap["landmark_visibility"] = dict(landmark_visibility)
            return snap

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

        left_elbow = _as_float(angles.get("left_elbow"))
        right_elbow = _as_float(angles.get("right_elbow"))
        left_shoulder = _as_float(angles.get("left_shoulder"))
        right_shoulder = _as_float(angles.get("right_shoulder"))
        left_hip = _as_float(angles.get("left_hip"))
        right_hip = _as_float(angles.get("right_hip"))

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
            "left_elbow": left_elbow,
            "right_elbow": right_elbow,
            "left_shoulder": left_shoulder,
            "right_shoulder": right_shoulder,
            "left_hip": left_hip,
            "right_hip": right_hip,
        }

        if pose_confidence is not None:
            try:
                conf = float(pose_confidence)
            except (TypeError, ValueError):
                conf = 0.0
            if conf < MIN_POSE_CONFIDENCE:
                self.form_errors["low_confidence"] += 1
                self.feedback = [FORM_MSG_LOW_CONFIDENCE]
                return self._frame_snapshot()

        if raw_elbow is None:
            self.form_errors["angle_not_detected"] += 1
            self.feedback = [FORM_MSG_ANGLE_NOT_DETECTED]
            return self._frame_snapshot()

        # A new valid analysis frame can reopen a finalized session.
        self.session_finalized = False

        smoothed = self._update_smoothed(raw_elbow)
        self.current_angles["smoothed_avg_elbow"] = smoothed
        direction = self._update_direction(smoothed)

        if self.rep_in_progress:
            if self.minimum_elbow_angle is None or smoothed < self.minimum_elbow_angle:
                self.minimum_elbow_angle = smoothed
            self._update_rep_alignment_tracking(body_line_offset, body_alignment_angle)

        target = self._predict_state(smoothed, direction)
        self._confirm_state(target)
        self._update_valid_up_tracking(smoothed)
        self._update_form_metrics(
            smoothed_elbow=smoothed,
            shoulder=avg_shoulder,
            hip=avg_hip,
            body_alignment_angle=body_alignment_angle,
            body_line_offset=body_line_offset,
        )
        self._update_form_evaluation(avg_shoulder, body_line_offset, body_alignment_angle)
        metrics_reliable = self.current_form_state != "metrics_incomplete"
        self._compose_feedback(camera_status=camera_status, metrics_reliable=metrics_reliable)

        self.previous_smoothed_elbow = smoothed
        return self._frame_snapshot()

    def _current_rep_form_errors(self) -> dict[str, bool]:
        return {
            "hips_sagging": self.current_rep_hips_sagging,
            "hips_too_high": self.current_rep_hips_too_high,
            "back_bent": self.current_rep_back_bent,
            "elbows_flared": self.current_rep_elbows_flared,
            "shoulder_alignment_issue": self.current_rep_shoulder_bad,
        }

    def _frame_snapshot(self) -> dict[str, Any]:
        rep_summary = self.get_rep_summary()
        return {
            "exercise": self.exercise,
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "successful_reps": rep_summary["successful_reps"],
            "failed_reps": rep_summary["failed_reps"],
            "total_reps": rep_summary["total_reps"],
            "current_state": self.state,
            "state": self.state,
            "feedback": list(self.feedback),
            "form_errors": dict(self.form_errors),
            "angles": dict(self.current_angles),
            "rep_in_progress": self.rep_in_progress,
            "has_seen_valid_up": self.has_seen_valid_up,
            "reached_bottom": self.reached_bottom,
            "movement_direction": self.movement_direction,
            "minimum_elbow_angle": self.minimum_elbow_angle,
            "rep_counted": self.rep_counted,
            "rep_start_elbow_angle": self.rep_start_elbow_angle,
            "candidate_state": self.candidate_state,
            "candidate_state_frames": self.candidate_state_count,
            "smoothed_avg_elbow": self.smoothed_avg_elbow,
            "current_form_state": self.current_form_state,
            "body_alignment_angle": self.body_alignment_angle,
            "body_line_offset": self.body_line_offset,
            "alignment_side": self.alignment_side,
            "form_metrics": dict(self.current_form_metrics),
            "active_form_issues": list(self.active_form_issues),
            "current_rep_form_issues": sorted(self.current_rep_form_issues),
            "current_rep_form_errors": self._current_rep_form_errors(),
            "last_rep_feedback": list(self.last_rep_feedback),
        }

    def finalize_session(self) -> None:
        if self.session_finalized:
            return
        self.session_finalized = True

        if self.rep_in_progress and self.state != "up":
            if self._visibility_blocked_during_rep and not self.reached_bottom:
                self._commit_rep_form_errors()
                self._reset_rep_temp()
            elif self.reached_bottom:
                self._record_incomplete(
                    FORM_MSG_COMPLETE_UP,
                    count_not_low_enough=False,
                )
                self._append_rep_history(
                    valid=False,
                    incomplete_reason="incomplete_up",
                )
                self._commit_rep_form_errors()
                self._reset_rep_temp()
            else:
                self._record_incomplete(
                    FORM_MSG_GO_LOWER,
                    count_not_low_enough=True,
                )
                self._append_rep_history(
                    valid=False,
                    incomplete_reason="not_low_enough",
                )
                self._commit_rep_form_errors()
                self._reset_rep_temp()

        if self.rep_count == 0:
            self._record_session_feedback([FORM_MSG_NO_COMPLETE])

        self.feedback = self._build_session_feedback_summary()

    def get_score_breakdown(self) -> dict[str, Any]:
        """Internal push-up score from rep_history (does not alter result JSON)."""
        from pushup_scoring import calculate_pushup_score_from_history

        return calculate_pushup_score_from_history(self.rep_history).as_dict()

    def get_rep_summary(self) -> dict[str, int]:
        """Successful / failed / total attempt counts from rep_history."""
        from rep_summary import summarize_rep_history

        return summarize_rep_history(self.rep_history).as_dict()

    def get_feedback_items(self) -> list[dict[str, Any]]:
        """Internal prioritized feedback items (deduplicated; public list unchanged)."""
        from feedback_priority import build_feedback_items, feedback_items_as_dicts

        items = build_feedback_items(
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
            messages=list(self._session_feedback) or list(self.feedback),
            sort=True,
        )
        return feedback_items_as_dicts(select_top_feedback(items))

    def session_error_codes(self) -> list[str]:
        """Unique form-issue codes seen in finished reps, most important first.

        Same role as SquatAnalyzer.errors: the backend scores with them and the
        app turns them into localized corrections.
        """
        seen: set[str] = set()
        for rep in self.rep_history:
            seen.update(str(code) for code in rep.get("errors") or [])
        order = FORM_ISSUE_PRIORITY + _INCOMPLETE_FEEDBACK_KEYS
        ranked = [code for code in order if code in seen]
        return ranked + sorted(seen.difference(order))

    def get_result(self, video_path: str | None = None) -> dict[str, Any]:
        _ = video_path
        self.finalize_session()
        final_feedback = self._build_session_feedback_summary()
        self.feedback = final_feedback
        rep_summary = self.get_rep_summary()
        return {
            "exercise": "pushup",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "successful_reps": rep_summary["successful_reps"],
            "failed_reps": rep_summary["failed_reps"],
            "total_reps": rep_summary["total_reps"],
            "final_state": self.state,
            "current_state": self.state,
            "state": self.state,
            "form_errors": dict(self.form_errors),
            "errors": self.session_error_codes(),
            "rep_history": [dict(rep) for rep in self.rep_history],
            "feedback": list(final_feedback),
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
            "has_seen_valid_up": self.has_seen_valid_up,
            "reached_bottom": self.reached_bottom,
            "movement_direction": self.movement_direction,
            "minimum_elbow_angle": self.minimum_elbow_angle,
            "rep_counted": self.rep_counted,
            "rep_start_elbow_angle": self.rep_start_elbow_angle,
            "smoothed_avg_elbow": self.smoothed_avg_elbow,
            "current_form_state": self.current_form_state,
            "body_alignment_angle": self.body_alignment_angle,
            "body_line_offset": self.body_line_offset,
            "alignment_side": self.alignment_side,
            "form_metrics": dict(self.current_form_metrics),
            "active_form_issues": list(self.active_form_issues),
            "last_rep_form_issues": list(self.last_rep_form_issues),
            "last_rep_feedback": list(self.last_rep_feedback),
        }


# ---------------------------------------------------------------------------
# Pipeline helpers (used by video_processor orchestration; no shared globals)
# ---------------------------------------------------------------------------


def create_pushup_analyzer() -> PushupAnalyzer:
    """Return a fresh push-up analyzer instance (isolated mutable state)."""
    return PushupAnalyzer()


def pushup_pose_landmark_indices(pose_landmark_enum: object) -> tuple[Any, ...]:
    """Landmark indices used for push-up pose-confidence scoring."""
    L = pose_landmark_enum
    return (
        L.LEFT_SHOULDER,
        L.LEFT_ELBOW,
        L.LEFT_WRIST,
        L.RIGHT_SHOULDER,
        L.RIGHT_ELBOW,
        L.RIGHT_WRIST,
        L.LEFT_HIP,
        L.RIGHT_HIP,
        L.LEFT_ANKLE,
        L.RIGHT_ANKLE,
    )


def elbow_angles_from_pushup(
    pushup_angles: dict[str, float | None],
) -> dict[str, float | None]:
    """Map push-up angle dict into left/right/average elbow view."""
    return {
        "left": pushup_angles.get("left_elbow"),
        "right": pushup_angles.get("right_elbow"),
        "average": pushup_angles.get("avg_elbow"),
    }


def draw_pushup_hud(
    frame: object,
    analyzer: PushupAnalyzer,
    pose_confidence: float | None,
    camera_distance: dict[str, Any] | None,
) -> None:
    """Draw push-up HUD with safe formatting for None values."""
    y0 = 28
    line_h = 28
    font_scale = 0.65
    angles = getattr(analyzer, "current_angles", {}) or {}
    fb_list = getattr(analyzer, "feedback", None) or []
    fb = fb_list[0] if fb_list else ""

    def _fmt_angle(value: Any) -> str:
        if value is None:
            return "N/A"
        try:
            return f"{float(value):.1f}"
        except (TypeError, ValueError):
            return "N/A"

    cam_status = (camera_distance or {}).get("status", "unknown")
    if cam_status == "good":
        cam_label = "OK"
    elif cam_status == "too_far":
        cam_label = "Too far"
    elif cam_status == "too_close":
        cam_label = "Too close"
    else:
        cam_label = "Unknown"

    conf_label = (
        f"{float(pose_confidence):.2f}" if pose_confidence is not None else "N/A"
    )

    lines = [
        "Exercise: Push-up",
        f"Reps: {getattr(analyzer, 'rep_count', 0)}",
        f"State: {getattr(analyzer, 'state', 'up')}",
        f"Elbow: {_fmt_angle(angles.get('avg_elbow'))}",
        f"Shoulder: {_fmt_angle(angles.get('avg_shoulder'))}",
        f"Hip: {_fmt_angle(angles.get('avg_hip'))}",
        f"Pose Conf: {conf_label}",
        f"Camera: {cam_label}",
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


def process_pushup_frame(
    analyzer: PushupAnalyzer,
    landmarks: object,
    image_width: int,
    image_height: int,
    *,
    pose_confidence: float,
    landmark_visibility_usable: bool,
    visibility_dict: dict[str, Any],
    camera_info: dict[str, Any],
    low_confidence: bool,
    show_preview: bool = False,
    frame: object | None = None,
) -> dict[str, Any]:
    """Run one push-up frame through angles + analyzer (existing behavior)."""
    pushup_angles = calculate_pushup_angles(landmarks, image_width, image_height)
    if not landmark_visibility_usable:
        analysis = analyzer.analyze_frame(
            pushup_angles,
            pose_confidence=pose_confidence,
            camera_status=camera_info["status"],
            landmark_visibility_ok=False,
            landmark_visibility=visibility_dict,
        )
        counted = False
    else:
        analysis = analyzer.analyze_frame(
            pushup_angles,
            pose_confidence=pose_confidence,
            camera_status=camera_info["status"],
            landmark_visibility_ok=True,
        )
        counted = not low_confidence

    analysis["landmark_visibility"] = visibility_dict
    analysis["camera"] = {
        "status": camera_info["status"],
        "body_scale": camera_info.get("body_scale"),
        "bbox_width_ratio": camera_info.get("bbox_width_ratio"),
        "bbox_height_ratio": camera_info.get("bbox_height_ratio"),
        "feedback": camera_info.get("feedback"),
    }

    if show_preview and frame is not None:
        draw_pushup_hud(frame, analyzer, pose_confidence, camera_info)

    return {
        "analysis": analysis,
        "counted_analyzed_frame": counted,
    }
