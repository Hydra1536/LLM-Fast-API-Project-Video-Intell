import os
import json
from google import genai
from thumbnail_engine import select_best_3_thumbnails
from thumbnail_engine import extract_top_thumbnails
import base64 
# from dotenv import load_dotenv

# load_dotenv()

# IMPORTANT: explicitly set API version
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)
# print("Gemini API Key:", client)
MODEL_NAME = "gemini-2.5-flash-lite"


def generate_platform_captions(platform: str, video_path=None, fps=None):
    tone_map = {
        "youtube": "engaging, curiosity-driven, descriptive",
        "instagram": "emotional, aesthetic, trendy",
        "tiktok": "short, viral, energetic, hook-based",
    }

    tone = tone_map.get(platform.lower(), "engaging")

    if video_path and fps:
        initial_10 = extract_top_thumbnails(video_path, fps, platform)
        best_3 = select_best_3_thumbnails(initial_10)
    else:
        print("No video data provided to Gemini.")
        return None

    all_captions = []

    for idx, thumbnail_base64 in enumerate(best_3):
        print(f"Sending thumbnail {idx+1} to Gemini...")

        prompt = f"""
You are a viral thumbnail copywriter.

Platform: {platform}
Tone: {tone}

Analyze the attached thumbnail image carefully.
Generate 3 DIFFERENT captions.
Each caption must be EXACTLY 3 short lines.
No hashtags.

Return ONLY valid JSON like:

[
  ["line1","line2","line3"],
  ["line1","line2","line3"],
  ["line1","line2","line3"]
]
"""

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    prompt,
                    {
                        "mime_type": "image/jpeg",
                        "data": thumbnail_base64,
                    },
                ],
            )

            raw_text = response.text.strip()
            start = raw_text.find("[")
            end = raw_text.rfind("]") + 1
            json_text = raw_text[start:end]

            captions = json.loads(json_text)

            if isinstance(captions, list) and len(captions) == 3:
                all_captions.append(captions[0])
            else:
                raise ValueError("Invalid structure")

        except Exception as e:
            print("Gemini Error:", e)
            return None

    print("Gemini caption generation complete.")

    return all_captions