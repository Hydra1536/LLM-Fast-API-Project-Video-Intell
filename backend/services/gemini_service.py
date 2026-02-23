import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# IMPORTANT: explicitly set API version
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
)
# print("Gemini API Key:", client)
MODEL_NAME = "gemini-2.5-flash-lite"

def generate_platform_captions(platform: str):

    tone_map = {
        "youtube": "engaging, curiosity-driven, descriptive",
        "instagram": "emotional, aesthetic, trendy",
        "tiktok": "short, viral, energetic, hook-based"
    }

    tone = tone_map.get(platform.lower(), "engaging")

    prompt = f"""
Generate 3 DIFFERENT social media captions for {platform}.
Tone must be: {tone}.
Each caption must be EXACTLY 3 short lines.
No hashtags.
Return ONLY valid JSON like:

[
  ["line1", "line2", "line3"],
  ["line1", "line2", "line3"],
  ["line1", "line2", "line3"]
]
"""

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        raw_text = response.text.strip()

        start = raw_text.find("[")
        end = raw_text.rfind("]") + 1
        json_text = raw_text[start:end]

        captions = json.loads(json_text)

        if (
            isinstance(captions, list)
            and len(captions) == 3
            and all(len(c) == 3 for c in captions)
        ):
            return captions
        else:
            raise ValueError("Invalid structure")

    except Exception as e:
        print("Gemini Error:", e)
        return None
