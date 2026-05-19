import cv2
import os


def analyze_video(video_path: str):
    if not os.path.exists(video_path):
        return {"status": "error", "message": "Video dosyası bulunamadı"}

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        return {"status": "error", "message": "Video açılamadı"}

    total_frames = 0
    motion_score = 0

    ret, previous_frame = cap.read()

    if not ret:
        return {"status": "error", "message": "Video okunamadı"}

    previous_gray = cv2.cvtColor(previous_frame, cv2.COLOR_BGR2GRAY)

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        total_frames += 1

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(previous_gray, gray)
        motion_score += diff.mean()

        previous_gray = gray

    cap.release()

    average_motion = motion_score / total_frames if total_frames > 0 else 0

    if average_motion > 15:
        accuracy = 85
        feedback = "Videoda belirgin egzersiz hareketi algılandı."
    elif average_motion > 5:
        accuracy = 65
        feedback = "Videoda hareket var ancak egzersiz hareketi sınırlı görünüyor."
    else:
        accuracy = 40
        feedback = "Videoda yeterli hareket algılanamadı."

    return {
        "status": "success",
        "exercise": "general_exercise_motion",
        "accuracy": accuracy,
        "feedback": feedback,
        "average_motion": round(average_motion, 2),
        "total_frames": total_frames,
        "video_path": video_path
    }