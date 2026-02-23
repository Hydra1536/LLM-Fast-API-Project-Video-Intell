import cv2
import numpy as np
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

FRAME_SAMPLE_INTERVAL_SECONDS = 0.5
RESIZE_WIDTH = 640


def resize_frame(frame):
    h, w = frame.shape[:2]
    if w > RESIZE_WIDTH:
        scale = RESIZE_WIDTH / w
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    return frame


def detect_hard_cuts(video_path, fps):
    cap = cv2.VideoCapture(video_path)
    prev_hist = None
    hard_cuts = 0

    frame_interval = int(fps * FRAME_SAMPLE_INTERVAL_SECONDS)
    frame_index = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            frame = resize_frame(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            if prev_hist is not None:
                diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR)
                # print("Histogram diff:", diff)
                if diff > 35:
                    hard_cuts += 1

            prev_hist = hist

        frame_index += 1

    cap.release()
    return hard_cuts


def calculate_average_motion(video_path, fps):
    cap = cv2.VideoCapture(video_path)
    ret, prev_frame = cap.read()
    if not ret:
        return 0.0

    prev_frame = resize_frame(prev_frame)
    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    frame_interval = int(fps * FRAME_SAMPLE_INTERVAL_SECONDS)
    frame_index = 0
    motion_values = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            frame = resize_frame(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray,
                None,
                0.5, 3, 15, 3, 5, 1.2, 0
            )

            magnitude, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            motion_values.append(np.mean(magnitude))

            prev_gray = gray

        frame_index += 1

    cap.release()
    return float(np.mean(motion_values)) if motion_values else 0.0


def calculate_text_presence_ratio(video_path, fps):
    cap = cv2.VideoCapture(video_path)

    frame_interval = int(fps * FRAME_SAMPLE_INTERVAL_SECONDS)
    frame_index = 0

    sampled = 0
    text_frames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_interval == 0:
            frame = resize_frame(frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            try:
                text = pytesseract.image_to_string(gray)
                if len(text.strip()) > 5:
                    text_frames += 1
            except:
                pass

            sampled += 1

        frame_index += 1

    cap.release()
    return text_frames / sampled if sampled > 0 else 0.0
