import cv2
import numpy as np
import base64

FRAME_SAMPLE_INTERVAL_SECONDS = 0.5
RESIZE_WIDTH = 640


def resize_frame(frame):
    h, w = frame.shape[:2]
    if w > RESIZE_WIDTH:
        scale = RESIZE_WIDTH / w
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    return frame


def crop_to_aspect_ratio(frame, platform: str):
    h, w = frame.shape[:2]

    if platform == "youtube":
        target_ratio = 16 / 9
    elif platform == "instagram":
        target_ratio = 1 / 1
    elif platform == "tiktok":
        target_ratio = 9 / 16
    else:
        target_ratio = w / h

    current_ratio = w / h

    if current_ratio > target_ratio:
        # Too wide → crop width
        new_width = int(h * target_ratio)
        x1 = (w - new_width) // 2
        frame = frame[:, x1:x1 + new_width]
    else:
        # Too tall → crop height
        new_height = int(w / target_ratio)
        y1 = (h - new_height) // 2
        frame = frame[y1:y1 + new_height, :]

    return frame


def frame_sharpness_score(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()


def encode_image_to_base64(frame):
    _, buffer = cv2.imencode(".jpg", frame)
    jpg_as_text = base64.b64encode(buffer).decode("utf-8")
    return jpg_as_text


def extract_top_thumbnails(video_path, fps, platform, max_thumbnails=10):
    cap = cv2.VideoCapture(video_path)

    frame_interval = int(fps * FRAME_SAMPLE_INTERVAL_SECONDS)
    frame_index = 0

    scored_frames = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            frame = resize_frame(frame)
            score = frame_sharpness_score(frame)
            scored_frames.append((score, frame.copy()))

        frame_index += 1

    cap.release()

    # Sort by sharpness (descending)
    scored_frames.sort(key=lambda x: x[0], reverse=True)

    selected_frames = []
    used_hashes = set()

    for score, frame in scored_frames:
        # Simple duplicate prevention via mean hash
        frame_hash = hash(frame.tobytes()[:1000])

        if frame_hash not in used_hashes:
            used_hashes.add(frame_hash)
            cropped = crop_to_aspect_ratio(frame, platform)
            selected_frames.append(cropped)

        if len(selected_frames) >= max_thumbnails:
            break

    # Encode all selected frames
    encoded_images = [encode_image_to_base64(f) for f in selected_frames]

    return encoded_images
