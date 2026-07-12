"""AI Trainer entry point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from video_processor import run_video_test_pipeline


def main() -> None:
    run_video_test_pipeline()


if __name__ == "__main__":
    main()
