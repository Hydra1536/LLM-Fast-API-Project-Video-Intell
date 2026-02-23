import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO

BACKEND_URL = "https://llm-fast-api-project-video-intell.onrender.com/analyze"

st.set_page_config(page_title="Video Intelligence Studio", layout="wide")

# ---------------------------
# Helper Functions
# ---------------------------


def decode_base64_image(base64_string):
    image_bytes = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_bytes))


def download_button(image_base64, filename):
    image_bytes = base64.b64decode(image_base64)
    st.download_button(
        label="Download JPG",
        data=image_bytes,
        file_name=filename,
        mime="image/jpeg",
        use_container_width=True,
    )


# ---------------------------
# Title Section
# ---------------------------

st.title("🎬 Video Intelligence Studio")
st.markdown("---")

# ---------------------------
# Upload Section
# ---------------------------

col1, col2 = st.columns([1, 1])

with col1:
    platform = st.selectbox("Select Platform", ["youtube", "instagram", "tiktok"])

with col2:
    uploaded_file = st.file_uploader(
        "Upload Video (Max 2 minutes)", type=["mp4", "mov", "avi"]
    )

analyze = st.button("Analyze Video", use_container_width=True)

st.markdown("---")

# ---------------------------
# Analysis Logic
# ---------------------------

if analyze and uploaded_file:
    with st.spinner("Analyzing video... This may take 10–20 seconds."):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}

        data = {"platform": platform}

        response = requests.post(BACKEND_URL, files=files, data=data)

    if response.status_code != 200:
        error_msg = response.json().get("detail", "An unknown error occurred.")
        st.error(f"🚫 {error_msg}")
    else:
        result = response.json()

        # ---------------------------
        # Metrics Section
        # ---------------------------

        st.subheader("📊 Video Metrics")
        m = result["metrics"]

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("FPS", m["fps"])
        col2.metric("Frames", m["total_frames"])
        col3.metric("Cuts", m["hard_cut_count"])
        col4.metric("Motion", round(m["avg_motion_magnitude"], 2))
        col5.metric("Text %", round(m["text_present_ratio"] * 100, 1))

        st.markdown("---")

        # ---------------------------
        # Top Thumbnails Section
        # ---------------------------

        st.subheader("🖼 Top 10 Thumbnails")

        thumbs = result["thumbnails"]

        thumb_cols = st.columns(5)

        for i, thumb in enumerate(thumbs):
            img = decode_base64_image(thumb)
            with thumb_cols[i % 5]:
                st.image(img, use_container_width=True)
                download_button(thumb, f"thumbnail_{i + 1}.jpg")

        st.markdown("---")

        # # ---------------------------
        # # AI Thematic Thumbnails
        # # ---------------------------

        # st.subheader("🤖 AI Thematic Thumbnails")

        # ai_blocks = result.get("ai_results", [])

        # for idx, block in enumerate(ai_blocks):
        #     st.markdown(f"### Concept {idx + 1}")

        #     image_base64 = block.get("image")
        #     caption = block.get("caption")

        #     if image_base64:
        #         img = decode_base64_image(image_base64)
        #         st.image(img, use_container_width=True)
        #         download_button(image_base64, f"ai_thumbnail_{idx+1}.jpg")

        #     if caption:
        #         lines = caption.split("\n")
        #         for line in lines:
        #             st.write(line)

        #     st.markdown("---")
        # ---------------------------
        # AI Captions (Thematic)
        # ---------------------------

        st.subheader("🤖 AI Generated Captions")

        captions = result.get("captions", [])

        if not captions:
            st.warning("No captions were generated.")
        else:
            for idx, caption_lines in enumerate(captions[:3]):
                st.markdown(f"### Concept {idx + 1}")

                # Ensure it's a list of 3 lines
                if isinstance(caption_lines, list):
                    lines = [str(line).strip() for line in caption_lines]

                    # Safety: ensure exactly 3
                    while len(lines) < 3:
                        lines.append("")

                    lines = lines[:3]

                    caption_text = "\n".join(lines)

                    # # Styled caption card
                    # st.markdown(
                    #     f"""
                    #     <div style="
                    #         background-color:#161B22;
                    #         padding:20px;
                    #         border-radius:12px;
                    #         margin-bottom:15px;
                    #         border:1px solid #2A2F3A;
                    #     ">
                    #         <p style="font-size:16px; line-height:1.6; margin:0;">
                    #             {lines[0]}<br><br>
                    #             {lines[1]}<br><br>
                    #             {lines[2]}
                    #         </p>
                    #     </div>
                    #     """,
                    #     unsafe_allow_html=True
                    # )

                    # Copy block
                    st.code(caption_text, language="markdown")

                else:
                    st.error(f"Caption {idx + 1} format invalid.")

                st.markdown("---")


elif analyze:
    st.warning("Please upload a video first.")
