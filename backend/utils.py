import os
import cv2
import uuid
import shutil

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi"}
MAX_DURATION_SECONDS = 120
MAX_FILE_SIZE_MB = 200


def generate_temp_path(filename: str) -> str:
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4()}_{filename}"
    return os.path.join(temp_dir, unique_name)


def validate_file_extension(filename: str):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file format. Allowed: mp4, mov, avi.")


def validate_file_size(file_path: str):
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError("File size exceeds 200MB limit.")


def validate_video_duration(file_path: str):
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        raise ValueError("Unable to read video file.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()

    duration = total_frames / fps if fps > 0 else 0

    if duration > MAX_DURATION_SECONDS:
        raise ValueError("Video exceeds maximum allowed duration of 2 minutes.")

    return fps, int(total_frames), duration


def cleanup_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
