# AIT AI Module

Python **3.12** is the target development version for this team.

## Setup

```bash
cd ai
python3.12 -m venv venv
source venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Download Pose Model

MediaPipe Tasks PoseLandmarker requires a local `.task` model:

```bash
python scripts/download_pose_model.py --variant full
```

Other variants: `--variant lite` or `--variant heavy`. Use `--force` to re-download.

Default model path: `ai/models/pose_landmarker_full.task`

Override with:

```bash
export AIT_POSE_MODEL_PATH=/absolute/path/to/model.task
```

## Tests

```bash
python -m pytest -q
```

## Run Video Analysis

```bash
python src/main.py
```

Optional preview HUD:

```bash
export AIT_SHOW_PREVIEW=1
python src/main.py
```
