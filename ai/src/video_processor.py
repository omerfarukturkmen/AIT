"""Video read/write and frame iteration (to be implemented)."""

import json
from copy import deepcopy
from pathlib import Path

import cv2
import mediapipe as mp

from angle_utils import calculate_knee_angles, get_landmark_point
from squat_analyzer import SquatAnalyzer

SOURCE_VIDEO_REL = "data/input/input.mp4"
OUTPUT_JSON_REL = "data/output/squat_analysis_result.json"

_DEFAULT_LAST_ANALYSIS: dict = {
    "exercise": "squat",
    "repCount": 0,
    "currentPhase": "unknown",
    "kneeAngle": {"left": None, "right": None, "average": None},
    "depthStatus": "unknown",
    "feedback": [],
    "confidence": 0.0,
    "isValidPose": False,
    "lastRep": {
        "depthStatus": None,
        "minKneeAngle": None,
        "feedback": [],
    },
}


class VideoProcessor:
    """Handles input/output video paths."""

    def __init__(self, input_path: str, output_path: str) -> None:
        self.input_path = input_path
        self.output_path = output_path


def _chain_visibility_mean(
    landmarks: object,
    pose_landmarks_enum: object,
    image_width: int,
    image_height: int,
) -> float | None:
    """Mean visibility of left/right hip–knee–ankle points."""
    L = pose_landmarks_enum
    chain = (
        L.LEFT_HIP,
        L.LEFT_KNEE,
        L.LEFT_ANKLE,
        L.RIGHT_HIP,
        L.RIGHT_KNEE,
        L.RIGHT_ANKLE,
    )
    vis: list[float] = []
    for idx in chain:
        pt = get_landmark_point(landmarks, idx, image_width, image_height)
        vis.append(float(pt["visibility"]))
    return sum(vis) / len(vis) if vis else None


def _draw_squat_hud(frame: object, analysis: dict) -> None:
    """Draw rep / phase / knee avg / first feedback in top-left."""
    y0 = 32
    line_h = 34
    font_scale = 0.75
    reps = analysis["repCount"]
    phase = analysis["currentPhase"]
    avg = analysis["kneeAngle"]["average"]
    fb_list = analysis.get("feedback") or []
    fb = fb_list[0] if fb_list else ""

    lines = [
        f"Reps: {reps}",
        f"Phase: {phase}",
        f"Knee Avg: {avg:.1f}" if avg is not None else "Knee Avg: —",
        f"Feedback: {fb}",
    ]
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


def _compact_frame_row(analysis: dict, frame_index: int) -> dict:
    """Per-frame export row (subset of fields)."""
    return {
        "frameIndex": frame_index,
        "repCount": analysis["repCount"],
        "currentPhase": analysis["currentPhase"],
        "kneeAngle": analysis["kneeAngle"],
        "depthStatus": analysis["depthStatus"],
        "feedback": analysis["feedback"],
        "confidence": analysis["confidence"],
        "isValidPose": analysis["isValidPose"],
        "lastRep": analysis["lastRep"],
    }


def _last_analysis_for_export(analysis: dict | None) -> dict:
    """Full last frame dict; kneeAngle without rawAverage for schema stability."""
    if analysis is None:
        return deepcopy(_DEFAULT_LAST_ANALYSIS)
    out = deepcopy(analysis)
    ka = out.get("kneeAngle")
    if isinstance(ka, dict):
        ka.pop("rawAverage", None)
        out["kneeAngle"] = ka
    return out


def _build_summary(
    frame_rows: list[dict],
    last_analysis: dict | None,
) -> dict:
    last = last_analysis or _DEFAULT_LAST_ANALYSIS
    valid_n = sum(1 for r in frame_rows if r.get("isValidPose"))
    invalid_n = len(frame_rows) - valid_n
    return {
        "totalReps": last.get("repCount", 0),
        "lastPhase": last.get("currentPhase", "unknown"),
        "lastFeedback": list(last.get("feedback") or []),
        "validFrameCount": valid_n,
        "invalidFrameCount": invalid_n,
    }


def _write_squat_analysis_json(
    project_root: Path,
    frame_rows: list[dict],
    last_analysis: dict | None,
) -> None:
    output_dir = project_root / "data" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "squat_analysis_result.json"

    last_exp = _last_analysis_for_export(last_analysis)
    payload = {
        "exercise": "squat",
        "sourceVideo": SOURCE_VIDEO_REL,
        "summary": _build_summary(frame_rows, last_analysis),
        "lastAnalysis": last_exp,
        "frames": frame_rows,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    rel = OUTPUT_JSON_REL
    print(f"Analysis JSON saved to: {rel}")


def run_video_test_pipeline() -> None:
    """Open data/input/input.mp4, show frames; press q to quit."""
    project_root = Path(__file__).resolve().parent.parent
    video_path = project_root / "data" / "input" / "input.mp4"

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Video acilamadi: {video_path}")

    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    analyzer = SquatAnalyzer()
    frame_rows: list[dict] = []
    last_full_analysis: dict | None = None

    window = "AIT video test"
    try:
        with mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as pose:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = pose.process(rgb)
                rgb.flags.writeable = True

                if results.pose_landmarks:
                    plm = results.pose_landmarks
                    L = mp_pose.PoseLandmark
                    h, w = frame.shape[:2]

                    knee_angles = calculate_knee_angles(plm, L, w, h)
                    vis_mean = _chain_visibility_mean(plm, L, w, h)
                    analysis = analyzer.analyze_frame(
                        knee_angles,
                        pose_confidence=vis_mean,
                    )
                    last_full_analysis = analysis
                    frame_rows.append(
                        _compact_frame_row(analysis, analyzer.frame_index)
                    )

                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS,
                    )

                    _draw_squat_hud(frame, analysis)

                    lk = get_landmark_point(plm, L.LEFT_KNEE, w, h)
                    rk = get_landmark_point(plm, L.RIGHT_KNEE, w, h)
                    if knee_angles["left"] is not None:
                        cv2.putText(
                            frame,
                            f"{knee_angles['left']:.0f}",
                            (lk["x"] + 10, lk["y"] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )
                    if knee_angles["right"] is not None:
                        cv2.putText(
                            frame,
                            f"{knee_angles['right']:.0f}",
                            (rk["x"] + 10, rk["y"] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.65,
                            (255, 255, 255),
                            2,
                            cv2.LINE_AA,
                        )
                else:
                    analysis = analyzer.analyze_frame(
                        {"left": None, "right": None, "average": None},
                        pose_confidence=None,
                    )
                    last_full_analysis = analysis
                    frame_rows.append(
                        _compact_frame_row(analysis, analyzer.frame_index)
                    )
                    _draw_squat_hud(frame, analysis)

                cv2.imshow(window, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        cap.release()
        cv2.destroyAllWindows()
        _write_squat_analysis_json(project_root, frame_rows, last_full_analysis)
