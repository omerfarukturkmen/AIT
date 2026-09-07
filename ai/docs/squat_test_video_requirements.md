# Squat Multi-Angle Test Video Requirements

This document defines the **real test videos** needed to baseline squat analysis
across camera angles. Do not substitute copies of the same file or synthetic
angles.

## Purpose

Measure how the current squat pipeline behaves at different camera angles
without changing SquatAnalyzer thresholds or state machine logic.

## Required Camera Angles

Supported manifest values:

- `front`
- `front_45`
- `side`
- `rear_45`
- `rear`
- `unknown` (only when angle is not documented)

## Minimum Recommended Test Set

### SIDE

- 2 correct full squat videos
- 1 partial / incomplete squat video

### FRONT

- 2 correct full squat videos
- 1 visibly incorrect form squat video

### FRONT_45

- 2 correct full squat videos

### REAR_45

- 1 squat video

### REAR

- 1 squat video

## Per-Video Requirements

Each video should ideally have:

- Resolution: 1080p or 720p
- Full body visible for the entire clip
- Fixed camera (no handheld drift)
- At least 3 squat repetitions (when testing rep counting)
- Adequate lighting
- Subject stays in frame
- **Expected rep count recorded manually** in the manifest
- **Camera angle recorded honestly** (do not guess from filename)

## Manifest Entry Template

Add each video to `tests/fixtures/squat_video_manifest.json`:

```json
{
  "id": "squat_side_02",
  "path": "../../path/to/video.mp4",
  "camera_angle": "side",
  "expected_reps": 3,
  "expected_analyzable": true,
  "notes": "Manual label: side view, 3 full reps"
}
```

Use `null` for `expected_reps` or `expected_analyzable` when unknown.

## Current Repository Status (baseline)

As of this task, the repository contains only a small set of videos and **does
not** include a complete multi-angle squat dataset:

| File | Notes |
|------|-------|
| `backend/uploaded_videos/IMG_5512.mp4` | Verified integration squat video (`rep_count=2`); camera angle **not documented** |
| `backend/uploaded_videos/IMG_5512 kopyası.mp4` | Duplicate copy; not independently verified |
| `ai/data/input/input.mp4` | Default AI input; angle/reps not documented |
| `backend/uploaded_videos/pushup_smoke.mp4` | Push-up smoke test, not squat |
| `backend/uploaded_videos/Ekran Kaydı 2026-07-12 20.18.32.mov` | Screen recording; squat metadata unknown |

### Missing Test Data

The following angle groups have **no dedicated squat test videos** in the repo:

- `front` — missing
- `front_45` — missing
- `side` — missing (IMG_5512 angle not proven)
- `rear_45` — missing
- `rear` — missing

## Evaluation Workflow

1. Add real labeled videos to the manifest.
2. Run:

```bash
cd ai
python scripts/evaluate_squat_angles.py
```

3. Review per-angle summary before changing squat algorithms.

## Out of Scope for This Document

- Downloading random internet videos
- Renaming/copying one video to simulate multiple angles
- Changing SquatAnalyzer rep counting or angle thresholds

Those belong to later improvement tasks after baseline measurement.
