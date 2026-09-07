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
./venv312/bin/python src/main.py
```

Optional preview HUD:

```bash
export AIT_SHOW_PREVIEW=1
./venv312/bin/python src/main.py
```

## Final Analysis Response Contract (schema 1.0)

`data/output/result.json` uses a single versioned contract for squat and push-up.

Top-level keys (exact):

- `schema_version` — currently `"1.0"` (`ANALYSIS_SCHEMA_VERSION`)
- `exercise_type` — `"squat"` | `"pushup"`
- `analysis` — `{status, frames, processed_frames, duration_seconds}`
- `reps` — `{successful, failed, total}` with `total == successful + failed` (≥ 0)
- `score` — `{overall, components}` integers 0–100
- `feedback` — `{top, all}` structured items
- `warnings` — list of technical session warnings (may be empty)

`analysis.status` values include at least:

- `completed`
- `insufficient_landmark_visibility`

Feedback item fields: `code`, `message`, `importance` (0–100), `severity` (`critical` | `medium` | `suggestion`).

`feedback.top` contains at most 3 unique correction items.

Squat score components: `depth`, `knee_control`, `torso_posture`, `rep_quality`.

Push-up score components: `elbow_angle`, `body_alignment`, `rep_depth`, `tempo_control`.

Legacy analyzer fields such as `rep_count` remain on the domain result API; they are not top-level fields of the schema 1.0 backend contract.

## Extensible exercise registry

Exercise routing lives in `src/exercise_registry.py`.

Built-in keys: `squat`, `pushup` (aliases include `push-up` / `push_up`).

To add a future exercise without editing the video loop:

1. Implement analyzer module helpers (`create_*`, landmark indices, `process_*_frame`).
2. Call `register_exercise(ExerciseSpec(...))` (typically next to builtins in `exercise_registry.py`).
3. Keep `analyze_video(video_path, exercise_type)` unchanged for callers.

Do **not** implement lunge (or other new movements) until their dedicated task.
