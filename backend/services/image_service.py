import os
import requests
import base64
from PIL import Image
from io import BytesIO
# from dotenv import load_dotenv

# load_dotenv()

HF_TOKEN = os.getenv("HF_API_TOKEN")
print("HF API Token:", HF_TOKEN)
# MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"

API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}


def get_aspect_ratio(platform):
    if platform == "youtube":
        return (1280, 720)
    elif platform == "instagram":
        return (1024, 1024)
    elif platform == "tiktok":
        return (720, 1280)
    else:
        return (1024, 1024)


def generate_image_from_caption(caption_lines, platform):
    caption_text = " ".join(caption_lines)

    prompt = f"""
Cinematic social media thumbnail.
High contrast, dramatic lighting.
Professional quality.
No text overlay.
Scene inspired by: {caption_text}
"""

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            json={"inputs": prompt},
            timeout=120
        )

        if response.status_code != 200:
            print("HF Router Error:", response.text)
            return None

        image_bytes = response.content

        img = Image.open(BytesIO(image_bytes))

        width, height = get_aspect_ratio(platform)
        img = img.resize((width, height))

        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=90)

        return base64.b64encode(buffered.getvalue()).decode()

    except Exception as e:
        print("Image Generation Error:", e)
        return None


def generate_thematic_images(captions, platform):
    results = []

    for caption in captions:
        img_base64 = generate_image_from_caption(caption, platform)

        if img_base64:
            results.append({
                "image": img_base64,
                "caption": caption
            })

    return results