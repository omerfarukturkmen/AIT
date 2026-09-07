"""AI Trainer entry point."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from video_processor import SOURCE_VIDEO_REL, analyze_video
from exercise_registry import cli_exercise_choices


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Trainer video analysis")
    parser.add_argument(
        "--video",
        default=SOURCE_VIDEO_REL,
        help=f"Input video path (default: {SOURCE_VIDEO_REL})",
    )
    parser.add_argument(
        "--exercise",
        default="squat",
        choices=cli_exercise_choices(),
        help="Exercise type to analyze (default: squat)",
    )
    args = parser.parse_args()
    result = analyze_video(video_path=args.video, exercise_type=args.exercise)
    metrics = result.get("metrics") or {}
    ai = result.get("ai_result") or {}
    domain = result.get("domain_result") or {}
    reps = ai.get("reps") or {}
    print(
        f"exercise={ai.get('exercise_type', domain.get('exercise'))} "
        f"reps={reps.get('successful', domain.get('rep_count'))} "
        f"state={domain.get('final_state', domain.get('current_state'))} "
        f"frames={metrics.get('total_frames')} "
        f"processed={metrics.get('processed_frames')}"
    )


if __name__ == "__main__":
    main()
