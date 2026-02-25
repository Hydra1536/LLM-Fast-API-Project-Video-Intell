# Video Intelligence Studio

Video Intelligence Studio is a full-stack Python app that analyzes short videos and returns:
- technical video metrics,
- platform-aware thumbnail candidates,
- AI-generated 3-line social captions.

The project contains:
- a **FastAPI backend** for video processing and caption generation,
- a **Streamlit frontend** for upload, analysis, preview, and download.

## Live Frontend

- Streamlit app: https://video-intelligence-studio.streamlit.app/

## Features

- Upload `.mp4`, `.mov`, or `.avi` files
- Validation guardrails:
  - max duration: **120 seconds**
  - max size: **200 MB**
- Video metrics:
  - FPS
  - total frame count
  - hard cut count
  - average optical-flow motion magnitude
  - text presence ratio (OCR-based)
- Top thumbnail extraction:
  - backend generates **top 10 best frames** per video (`max_thumbnails=10`)
  - sharpness scoring (Laplacian variance)
  - duplicate suppression
  - platform-specific crop ratios:
    - YouTube `16:9`
    - Instagram `1:1`
    - TikTok `9:16`
- AI caption generation with Gemini using **best 3 thumbnails selected from initial top 10**

## Project Structure

```text
video-intel/
|- backend/
|  |- main.py
|  |- utils.py
|  |- video_processor.py
|  |- thumbnail_engine.py
|  |- services/
|  |  |- gemini_service.py
|  |  |- image_service.py
|  |- requirements.txt
|  |- runtime.txt
|- frontend/
|  |- app.py
|  |- requirements.txt
```

## How It Works

1. Frontend uploads a video + platform (`youtube | instagram | tiktok`) to backend `/analyze`.
2. Backend stores the file in a temporary folder.
3. Backend validates extension, size, and duration.
4. Processing pipeline computes metrics and selects the top 10 best frames as thumbnails.
5. Caption pipeline re-scores those 10 thumbnails, selects the best 3, and sends those 3 images to Gemini.
6. API returns JSON with `metrics`, `thumbnails` (top 10, base64 JPGs), and `captions`.
7. Frontend renders metrics, previews thumbnails, and enables downloads.

## Detailed Pipeline (How Initial 10 Thumbnails Are Processed)

Source: `backend/thumbnail_engine.py`

1. Video is sampled every `0.5s` (`FRAME_SAMPLE_INTERVAL_SECONDS`).
2. Each sampled frame is resized to width `<= 640` (`RESIZE_WIDTH`) for faster scoring.
3. Each sampled frame gets a sharpness score:
   - `sharpness = var(Laplacian(gray_frame))`
4. Frames are sorted by sharpness in descending order.
5. Duplicate-like frames are removed using a lightweight hash (`hash(frame.tobytes()[:1000])`).
6. Remaining frames are center-cropped by platform ratio:
   - YouTube `16:9`
   - Instagram `1:1`
   - TikTok `9:16`
7. Top 10 cropped frames are encoded to base64 and returned as `thumbnails`.

## Caption Generation Flow 

Source: `backend/services/gemini_service.py` and `backend/thumbnail_engine.py`

1. Backend maps platform to tone:
   - YouTube: engaging, curiosity-driven, descriptive
   - Instagram: emotional, aesthetic, trendy
   - TikTok: short, viral, energetic, hook-based
2. Backend gets initial 10 thumbnails from `extract_top_thumbnails(...)`.
3. It re-scores the 10 thumbnails with quality scoring:
   - `quality = 0.6 * sharpness + 0.3 * contrast + 0.1 * brightness`
   - `sharpness = var(Laplacian(gray))`
   - `contrast = std(gray)`
   - `brightness = mean(gray)`
4. Top 3 thumbnails by quality score are selected (`select_best_3_thumbnails`).
5. Each selected thumbnail is sent to Gemini (`gemini-2.5-flash-lite`) with an image + prompt.
6. For each image, Gemini is asked for 3 caption concepts (3 lines each, JSON only, no hashtags).
7. Backend parses Gemini output and currently takes the first concept from each image result.
8. Final API output is 3 caption blocks, each block containing 3 lines.

## Metrics: How Every Metric Is Calculated

Source: `backend/video_processor.py` and `backend/utils.py`

- `fps`:
  - Extracted from OpenCV metadata (`cv2.CAP_PROP_FPS`).
- `total_frames`:
  - Extracted from OpenCV metadata (`cv2.CAP_PROP_FRAME_COUNT`).
- `duration_seconds`:
  - `duration = total_frames / fps`.
- `hard_cut_count`:
  - Sample every `0.5s`.
  - Convert frame to grayscale.
  - Compute normalized 256-bin histogram.
  - Compare current histogram with previous histogram using chi-square (`cv2.HISTCMP_CHISQR`).
  - If difference `> 35`, increment hard-cut count.
- `avg_motion_magnitude`:
  - Sample every `0.5s`.
  - Compute dense optical flow using Farneback (`cv2.calcOpticalFlowFarneback`).
  - Convert flow vectors to magnitude and take mean magnitude per sampled step.
  - Final value = mean of all sampled-step mean magnitudes.
- `text_present_ratio`:
  - Sample every `0.5s`.
  - Run OCR with Tesseract (`pytesseract.image_to_string`) on grayscale frame.
  - Mark frame as text-present if trimmed OCR output length is `> 5`.
  - Ratio = `text_frames / sampled_frames`.

## Prerequisites

- Python **3.11** (see `backend/runtime.txt`)
- Tesseract OCR installed locally
- Gemini API key

### Tesseract requirement

`backend/video_processor.py` currently sets:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

If Tesseract is installed elsewhere, update this path.

## Local Setup

### 1. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend runs at `http://127.0.0.1:8000`.

### 2. Frontend

Open a second terminal:

```powershell
cd frontend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Tech Stack

- Backend API: FastAPI, Uvicorn, python-multipart
- Video processing: OpenCV, NumPy
- OCR: pytesseract + local Tesseract binary
- LLM integration: Google GenAI SDK
- Frontend: Streamlit, Requests, Pillow
- AI models and purpose:
  - `gemini-2.5-flash-lite`: image-aware caption generation
  - `stabilityai/stable-diffusion-xl-base-1.0` (via `image_service.py`, optional): image generation from captions (currently not active in UI flow)

## Current Limitations

- OCR path is hardcoded to a Windows location.
- `image_service.py` based AI-image feature is currently not shown in the app because the free tier for image generation is exhausted.
- Gemini caption feature is present in code, but caption output may be missing when Gemini free-tier quota is exhausted.
- Caption flow recomputes thumbnail extraction inside Gemini service, so extraction currently happens twice.
- Frontend uses a fixed backend URL by default.

## Deployment Notes

- Backend includes `runtime.txt` for Python version pinning (`python-3.11.9`).
- Ensure runtime has:
  - OpenCV system dependencies,
  - Tesseract binary and configured path,
  - environment variables for API keys.
