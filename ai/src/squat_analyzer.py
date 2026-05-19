"""Squat exercise phase detection, rep counting, and feedback."""

from __future__ import annotations

from collections import deque
from typing import Any


class SquatAnalyzer:
    """State machine for squat reps with smoothing and confirmed phases."""

    CONFIRM_FRAMES = 3
    STANDING_FRAMES_TO_ARM = 3

    def __init__(self) -> None:
        self.rep_count: int = 0
        self.current_phase: str = "unknown"
        self.previous_phase: str = "unknown"
        self.min_knee_angle_current_rep: float | None = None
        self.last_rep: dict[str, Any] = {
            "depthStatus": None,
            "minKneeAngle": None,
            "feedback": [],
        }
        self.feedback: list[str] = []
        self.frame_index: int = 0
        self.last_depth_status: str = "unknown"

        self._angle_history: deque[float] = deque(maxlen=5)
        self._smoothed_average: float | None = None

        self.candidate_phase: str = "unknown"
        self.candidate_phase_count: int = 0
        self.confirmed_phase: str = "unknown"
        self._last_frame_confirmed_phase: str = "unknown"

        self.movement_state: str = "idle"
        self.has_reached_bottom: bool = False
        self.frames_in_standing: int = 0
        self.frames_in_bottom: int = 0

        self.ready_for_squat: bool = False
        self.in_squat_attempt: bool = False

    def _phase_from_average(self, average: float | None) -> str:
        if average is None:
            return "unknown"
        if average >= 160:
            return "standing"
        if average >= 125:
            return "transition"
        if average >= 85:
            return "bottom"
        return "too_deep"

    def _depth_from_min(self, min_angle: float | None) -> str:
        if min_angle is None:
            return "unknown"
        if min_angle < 85:
            return "too_deep"
        if min_angle <= 125:
            return "good_depth"
        return "too_shallow"

    def _rep_depth_feedback_list(self, depth_status: str) -> list[str]:
        if depth_status == "too_shallow":
            return ["Daha derine inmeyi dene."]
        if depth_status == "good_depth":
            return ["Squat derinligi iyi."]
        if depth_status == "too_deep":
            return ["Fazla derine indin, kontrollu kal."]
        return []

    def _update_smoothed(self, raw_average: float | None) -> float | None:
        if raw_average is not None:
            self._angle_history.append(float(raw_average))
        if not self._angle_history:
            self._smoothed_average = None
            return None
        self._smoothed_average = sum(self._angle_history) / len(self._angle_history)
        return self._smoothed_average

    def _run_confirmation(self, measured_phase: str) -> None:
        if measured_phase == self.candidate_phase:
            self.candidate_phase_count += 1
        else:
            self.candidate_phase = measured_phase
            self.candidate_phase_count = 1
        if self.candidate_phase_count >= self.CONFIRM_FRAMES:
            self.confirmed_phase = self.candidate_phase

    def _update_movement_state(self) -> None:
        cp = self.confirmed_phase
        if cp == "unknown":
            self.movement_state = "idle"
        elif cp == "standing" and self.ready_for_squat:
            self.movement_state = "ready"
        elif cp == "standing":
            self.movement_state = "idle"
        elif cp == "transition":
            self.movement_state = "transition"
        elif cp in ("bottom", "too_deep"):
            self.movement_state = "squatting"
        else:
            self.movement_state = "idle"

    def analyze_frame(
        self,
        knee_angles: dict[str, float | None],
        pose_confidence: float | None = None,
    ) -> dict[str, Any]:
        self.frame_index += 1

        left = knee_angles.get("left")
        right = knee_angles.get("right")
        raw_average = knee_angles.get("average")

        if raw_average is None:
            self.previous_phase = self._last_frame_confirmed_phase
            self.current_phase = self.confirmed_phase
            self._update_movement_state()
            feedback = [
                "Kamera acisini duzelt, vucut noktalari net gorunmuyor."
            ]
            self.feedback = feedback
            conf = float(pose_confidence) if pose_confidence is not None else 0.0
            return {
                "exercise": "squat",
                "repCount": self.rep_count,
                "currentPhase": self.confirmed_phase,
                "kneeAngle": {
                    "left": left,
                    "right": right,
                    "average": None,
                    "rawAverage": None,
                },
                "depthStatus": self.last_depth_status,
                "feedback": feedback,
                "confidence": conf,
                "isValidPose": False,
                "lastRep": {
                    "depthStatus": self.last_rep.get("depthStatus"),
                    "minKneeAngle": self.last_rep.get("minKneeAngle"),
                    "feedback": list(self.last_rep.get("feedback") or []),
                },
            }

        prev_conf = self._last_frame_confirmed_phase
        smoothed = self._update_smoothed(raw_average)
        measured_phase = self._phase_from_average(smoothed)

        self._run_confirmation(measured_phase)
        conf_phase = self.confirmed_phase

        if conf_phase == "standing":
            self.frames_in_standing += 1
            self.frames_in_bottom = 0
            if self.frames_in_standing >= self.STANDING_FRAMES_TO_ARM:
                self.ready_for_squat = True
        else:
            self.frames_in_standing = 0

        if conf_phase in ("bottom", "too_deep"):
            self.frames_in_bottom += 1
        else:
            self.frames_in_bottom = 0

        if conf_phase in ("bottom", "too_deep") and smoothed is not None:
            if self.min_knee_angle_current_rep is None:
                self.min_knee_angle_current_rep = smoothed
            else:
                self.min_knee_angle_current_rep = min(
                    self.min_knee_angle_current_rep,
                    smoothed,
                )

        if (
            prev_conf == "standing"
            and conf_phase in ("transition", "bottom", "too_deep")
            and self.ready_for_squat
        ):
            self.in_squat_attempt = True

        if conf_phase in ("bottom", "too_deep") and self.in_squat_attempt:
            self.has_reached_bottom = True

        rep_completed = False
        completed_depth: str | None = None

        if conf_phase == "standing" and prev_conf != "standing":
            if self.has_reached_bottom and self.in_squat_attempt:
                rep_completed = True
                self.rep_count += 1
                completed_depth = self._depth_from_min(self.min_knee_angle_current_rep)
                self.last_depth_status = completed_depth
                rep_fb = self._rep_depth_feedback_list(completed_depth)
                self.last_rep = {
                    "depthStatus": completed_depth,
                    "minKneeAngle": self.min_knee_angle_current_rep,
                    "feedback": list(rep_fb),
                }
                self.has_reached_bottom = False
                self.in_squat_attempt = False
                self.ready_for_squat = False
                self.min_knee_angle_current_rep = None
            else:
                self.in_squat_attempt = False
                self.min_knee_angle_current_rep = None

        self.previous_phase = prev_conf
        self.current_phase = conf_phase
        self._last_frame_confirmed_phase = conf_phase
        self._update_movement_state()

        feedback: list[str] = []
        if rep_completed and completed_depth is not None:
            feedback.extend(self._rep_depth_feedback_list(completed_depth))
        if conf_phase == "too_deep":
            feedback.append("Cok fazla asagi iniyorsun, kontrolu koru.")
        if conf_phase == "bottom":
            feedback.append("Alt pozisyon iyi, kontrollu yuksel.")
        elif conf_phase == "transition":
            feedback.append("Hareket devam ediyor.")
        elif (
            conf_phase == "standing"
            and smoothed is not None
            and not rep_completed
        ):
            feedback.append("Squat icin hazir pozisyondasin.")

        self.feedback = feedback

        if pose_confidence is not None:
            confidence = float(pose_confidence)
        else:
            confidence = 1.0

        return {
            "exercise": "squat",
            "repCount": self.rep_count,
            "currentPhase": self.confirmed_phase,
            "kneeAngle": {
                "left": left,
                "right": right,
                "average": smoothed,
                "rawAverage": raw_average,
            },
            "depthStatus": self.last_depth_status,
            "feedback": feedback,
            "confidence": confidence,
            "isValidPose": True,
            "lastRep": {
                "depthStatus": self.last_rep.get("depthStatus"),
                "minKneeAngle": self.last_rep.get("minKneeAngle"),
                "feedback": list(self.last_rep.get("feedback") or []),
            },
        }
