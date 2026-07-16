"""Push-up exercise phase detection, rep counting, and form feedback."""

from __future__ import annotations

from typing import Any

# Elbow-angle thresholds (degrees)
UP_ELBOW_ANGLE = 155.0
DOWN_ELBOW_ANGLE = 95.0
BOTTOM_ELBOW_ANGLE = 85.0

MIN_POSE_CONFIDENCE = 0.50


class PushupAnalyzer:
    """Simple up → descending → bottom → ascending → up push-up counter."""

    def __init__(self) -> None:
        self.exercise = "pushup"
        self.rep_count = 0
        self.valid_reps = 0
        self.invalid_reps = 0
        self.state = "up"

        self.candidate_state: str | None = None
        self.candidate_state_count = 0
        self.REQUIRED_STATE_FRAMES = 3

        self.had_bottom_position = False
        self.frame_count = 0

        self.feedback: list[str] = []
        self.current_angles: dict[str, float | None] = {
            "avg_elbow": None,
            "avg_shoulder": None,
            "avg_hip": None,
        }

        self.form_errors: dict[str, int] = {
            "not_low_enough": 0,
            "hips_not_aligned": 0,
            "hips_too_high": 0,
            "shoulder_position": 0,
            "low_confidence": 0,
            "angle_not_detected": 0,
        }

    def _predict_state(self, avg_elbow: float) -> str:
        """Return the target state for the current elbow angle."""
        state = self.state

        if state == "up":
            if avg_elbow < 140:
                return "descending"
            return "up"

        if state == "descending":
            if avg_elbow <= DOWN_ELBOW_ANGLE:
                return "bottom"
            if avg_elbow >= UP_ELBOW_ANGLE:
                return "up"
            return "descending"

        if state == "bottom":
            if avg_elbow > DOWN_ELBOW_ANGLE + 10:
                return "ascending"
            return "bottom"

        if state == "ascending":
            if avg_elbow >= UP_ELBOW_ANGLE:
                return "up"
            if avg_elbow <= DOWN_ELBOW_ANGLE:
                return "bottom"
            return "ascending"

        return state

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

        if self.state == "bottom":
            self.had_bottom_position = True

        if (
            previous_state == "ascending"
            and self.state == "up"
            and self.had_bottom_position
        ):
            self.rep_count += 1
            self.valid_reps += 1
            self.had_bottom_position = False

    def _update_form_feedback(self, avg_elbow: float) -> None:
        messages: list[str] = []

        if self.state in ("descending", "bottom") and avg_elbow > 110:
            messages.append("Go lower")
            self.form_errors["not_low_enough"] += 1

        avg_hip = self.current_angles.get("avg_hip")
        if avg_hip is not None and avg_hip < 150:
            messages.append("Keep your hips aligned")
            self.form_errors["hips_not_aligned"] += 1
        if avg_hip is not None and avg_hip > 190:
            messages.append("Do not raise your hips too high")
            self.form_errors["hips_too_high"] += 1

        avg_shoulder = self.current_angles.get("avg_shoulder")
        if avg_shoulder is not None and avg_shoulder < 30:
            messages.append("Check shoulder position")
            self.form_errors["shoulder_position"] += 1

        if not messages:
            messages = ["Good push-up form"]

        self.feedback = messages

    def analyze_frame(
        self,
        pushup_angles: dict[str, Any] | None,
        pose_confidence: float | None = None,
        camera_status: str | None = None,
    ) -> dict[str, Any]:
        self.frame_count += 1
        _ = camera_status  # reserved for future HUD / quality hooks

        angles = pushup_angles if isinstance(pushup_angles, dict) else {}
        avg_elbow = angles.get("avg_elbow")
        avg_shoulder = angles.get("avg_shoulder")
        avg_hip = angles.get("avg_hip")

        self.current_angles = {
            "avg_elbow": avg_elbow,
            "avg_shoulder": avg_shoulder,
            "avg_hip": avg_hip,
        }

        if pose_confidence is not None and float(pose_confidence) < MIN_POSE_CONFIDENCE:
            self.form_errors["low_confidence"] += 1
            self.feedback = ["Low pose confidence"]
            return self._frame_snapshot()

        if avg_elbow is None:
            self.form_errors["angle_not_detected"] += 1
            self.feedback = ["Elbow angle not detected"]
            return self._frame_snapshot()

        target = self._predict_state(float(avg_elbow))
        self._confirm_state(target)
        self._update_form_feedback(float(avg_elbow))
        return self._frame_snapshot()

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
        }

    def finalize_session(self) -> None:
        if self.rep_count == 0:
            msg = "No complete push-up detected"
            if msg not in self.feedback:
                self.feedback = list(self.feedback) + [msg]

        if self.had_bottom_position and self.state != "up":
            self.invalid_reps += 1
            self.had_bottom_position = False

    def get_result(self, video_path: str | None = None) -> dict[str, Any]:
        _ = video_path
        self.finalize_session()
        return {
            "exercise": "pushup",
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "final_state": self.state,
            "form_errors": dict(self.form_errors),
            "feedback": list(self.feedback),
            "angles": {
                "avg_elbow": self.current_angles.get("avg_elbow"),
                "avg_shoulder": self.current_angles.get("avg_shoulder"),
                "avg_hip": self.current_angles.get("avg_hip"),
            },
        }
