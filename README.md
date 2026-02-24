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
- AI caption generation with Gemini (`3 concepts x 3 lines`)

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
5. Backend calls Gemini for 3 structured caption concepts.
6. API returns JSON with `metrics`, `thumbnails` (base64 JPGs), and `captions`.
7. Frontend renders metrics, previews thumbnails, and enables downloads.

## Caption Generation Flow (Gemini)

1. Backend receives the selected platform (`youtube`, `instagram`, or `tiktok`).
2. It maps platform to a tone style:
   - YouTube: engaging, curiosity-driven, descriptive
   - Instagram: emotional, aesthetic, trendy
   - TikTok: short, viral, energetic, hook-based
3. Backend builds a strict prompt asking Gemini for:
   - exactly 3 different caption concepts
   - exactly 3 short lines per concept
   - no hashtags
   - JSON-only output format
4. Gemini returns text; backend extracts the JSON block and parses it.
5. Backend validates structure (`3 concepts x 3 lines`) and returns captions.

Current behavior note:
- The top 10 selected thumbnail frames are used for display/download.
- These selected frames are **not passed to Gemini** in the current implementation; caption generation is platform/tone-driven only.

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

## Environment Variables

Set these before running backend:

- `GEMINI_API_KEY` (required for caption generation)
- `HF_API_TOKEN` (only needed if you re-enable image generation from `image_service.py`)

Windows PowerShell example:

```powershell
$env:GEMINI_API_KEY = "your_gemini_key"
$env:HF_API_TOKEN = "your_hf_token"
```

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

- Backend: FastAPI, OpenCV, NumPy, pytesseract, Google GenAI SDK
- Frontend: Streamlit, Requests, Pillow
- AI Services:
  - Gemini caption generation (active)
  - Hugging Face image generation service (`image_service.py`) is available in code but currently not shown in app flow

## Current Limitations

- OCR path is hardcoded to a Windows location.
- CORS is fully open (`*`) for ease of integration.
- `image_service.py` based AI-image feature is currently not shown in the app because the free tier for image generation is exhausted.
- Gemini caption feature is present in code, but caption output may be missing when Gemini free-tier quota is exhausted.
- Captions are generating based on selected platform tones, not by selected thumbnails.
- Frontend uses a fixed backend URL by default.

## Deployment Notes

- Backend includes `runtime.txt` for Python version pinning (`python-3.11.9`).
- Ensure runtime has:
  - OpenCV system dependencies,
  - Tesseract binary and configured path,
  - environment variables for API keys.


