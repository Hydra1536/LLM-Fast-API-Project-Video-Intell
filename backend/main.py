# start by uvicorn main:app --reload -> from backend directory
# start by streamlit run app.py -> from frontend directory
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil

# from dotenv import load_dotenv
from fastapi import Form
from services.gemini_service import generate_platform_captions
from utils import (
    generate_temp_path,
    validate_file_extension,
    validate_file_size,
    validate_video_duration,
    cleanup_file,
)

from video_processor import (
    detect_hard_cuts,
    calculate_average_motion,
    calculate_text_presence_ratio,
)
from thumbnail_engine import extract_top_thumbnails
# load_dotenv()

app = FastAPI(title="Video Intelligence API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VALID_PLATFORMS = {"youtube", "instagram", "tiktok"}


@app.post("/analyze")
async def analyze_video(file: UploadFile = File(...), platform: str = Form(...)):
    temp_path = None

    try:
        if platform not in VALID_PLATFORMS:
            raise ValueError("Invalid platform. Choose youtube, instagram, or tiktok.")

        validate_file_extension(file.filename)

        temp_path = generate_temp_path(file.filename)

        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        validate_file_size(temp_path)

        fps, total_frames, duration = validate_video_duration(temp_path)

        hard_cuts = detect_hard_cuts(temp_path, fps)
        avg_motion = calculate_average_motion(temp_path, fps)
        text_ratio = calculate_text_presence_ratio(temp_path, fps)

        thumbnails = extract_top_thumbnails(temp_path, fps, platform)
        captions = generate_platform_captions(platform)
        # ai_results = generate_thematic_images(captions, platform)
        metrics = {
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "duration_seconds": round(duration, 2),
            "hard_cut_count": hard_cuts,
            "avg_motion_magnitude": round(avg_motion, 4),
            "text_present_ratio": round(text_ratio, 4),
        }

        if captions is None:
            return {
                "metrics": metrics,
                "thumbnails": thumbnails,
                "captions": ["Caption generation failed. Please retry."],
            }
        # elif ai_results is None:
        #     return {
        #         "error": "AI image generation failed. Please retry."
        #     }
        else:
            return {
                "metrics": metrics,
                "thumbnails": thumbnails,
                "captions": captions,
                # "ai_results": ai_results
            }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if temp_path:
            cleanup_file(temp_path)
