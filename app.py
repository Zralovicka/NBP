import streamlit as st
import base64
import io
import os
import json
import uuid
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
APP_PASSWORD = os.getenv("APP_PASSWORD", "")

ASPECT_RATIOS = ["Auto", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
RESOLUTIONS = ["1K", "2K", "4K"]
MAX_BATCH = 4
MODEL_NAME = "gemini-3-pro-image-preview"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nano Banana Studio",
    page_icon="🍌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------------------------
# Custom CSS — Higgsfield-inspired dark UI
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---- Global ---- */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
}

/* Hide Streamlit defaults */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {display: none;}
div[data-testid="stDecoration"] {display: none;}

/* Main container */
.main .block-container {
    padding: 0.5rem 1rem 6rem 1rem !important;
    max-width: 100% !important;
}

/* ---- Top bar ---- */
.top-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: #0a0a0a;
    border-bottom: 1px solid #1e1e1e;
    padding: 0.5rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
}
.top-bar-logo {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 1.1rem;
    font-weight: 700;
    color: #C8FF00;
    letter-spacing: -0.3px;
}
.top-bar-logo span {
    font-size: 1.3rem;
}
.top-bar-model {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: #888;
    font-weight: 500;
}
.top-bar-model b {
    color: #C8FF00;
}

/* ---- Image Grid ---- */
.image-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 8px;
    padding-top: 56px;
    padding-bottom: 100px;
}
.image-card {
    position: relative;
    border-radius: 10px;
    overflow: hidden;
    background: #111;
    border: 1px solid #1e1e1e;
    transition: border-color 0.2s, transform 0.15s;
    cursor: pointer;
    aspect-ratio: auto;
}
.image-card:hover {
    border-color: #333;
    transform: scale(1.008);
}
.image-card img {
    width: 100%;
    height: auto;
    display: block;
}
.image-card-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.85));
    padding: 28px 12px 10px 12px;
    opacity: 0;
    transition: opacity 0.2s;
}
.image-card:hover .image-card-overlay {
    opacity: 1;
}
.image-card-badge {
    position: absolute;
    bottom: 8px;
    left: 10px;
    background: rgba(0,0,0,0.65);
    backdrop-filter: blur(4px);
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 0.65rem;
    color: #aaa;
    font-weight: 600;
    letter-spacing: 0.4px;
    display: flex;
    align-items: center;
    gap: 4px;
}
.image-card-badge .ai-dot {
    background: #C8FF00;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    display: inline-block;
}

/* ---- Bottom Bar (Prompt Area) ---- */
.bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    background: rgba(10, 10, 10, 0.92);
    backdrop-filter: blur(16px);
    border-top: 1px solid #1e1e1e;
    padding: 10px 16px;
}
.bottom-bar-inner {
    max-width: 960px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.prompt-row {
    display: flex;
    align-items: center;
    gap: 8px;
}
.controls-row {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.ctrl-pill {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.75rem;
    color: #aaa;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: default;
    white-space: nowrap;
}
.ctrl-pill b {
    color: #e0e0e0;
}
.ctrl-pill .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #C8FF00;
}

/* Generate button */
.generate-btn {
    background: #C8FF00 !important;
    color: #0a0a0a !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 28px !important;
    font-size: 0.9rem !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    letter-spacing: -0.2px;
    white-space: nowrap;
}
.generate-btn:hover {
    background: #d4ff33 !important;
    transform: scale(1.03);
}

/* ---- Streamlit overrides ---- */
.stTextInput > div > div > input {
    background: #141414 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
    color: #e0e0e0 !important;
    font-size: 0.9rem !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C8FF00 !important;
    box-shadow: 0 0 0 1px #C8FF0040 !important;
}
.stTextInput > div > div > input::placeholder {
    color: #555 !important;
}

.stSelectbox > div > div {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #e0e0e0 !important;
    font-size: 0.8rem !important;
}

div[data-testid="stFileUploader"] {
    background: #111 !important;
    border: 1px dashed #2a2a2a !important;
    border-radius: 10px !important;
    padding: 8px !important;
}

/* Spinner */
.stSpinner > div {
    border-top-color: #C8FF00 !important;
}

/* Toast/Alert */
div[data-testid="stAlert"] {
    background: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 10px !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: #111 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
}

/* ---- Empty state ---- */
.empty-state {
    text-align: center;
    padding: 120px 20px 60px 20px;
    color: #444;
}
.empty-state h2 {
    font-size: 2rem;
    font-weight: 700;
    color: #333;
    margin-bottom: 8px;
}
.empty-state p {
    font-size: 0.95rem;
    color: #444;
    max-width: 440px;
    margin: 0 auto;
}

/* ---- Delete button on cards ---- */
.del-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    background: rgba(0,0,0,0.6);
    backdrop-filter: blur(4px);
    border: 1px solid #333;
    border-radius: 6px;
    color: #ccc;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.2s;
    font-size: 0.8rem;
}
.image-card:hover .del-btn {
    opacity: 1;
}
.del-btn:hover {
    background: rgba(200, 50, 50, 0.7);
    color: #fff;
}

/* ---- Upload thumbnails ---- */
.ref-thumbs {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 4px;
}
.ref-thumb {
    width: 40px;
    height: 40px;
    border-radius: 6px;
    object-fit: cover;
    border: 1px solid #2a2a2a;
}

/* ---- Loading animation ---- */
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(200, 255, 0, 0); }
    50% { box-shadow: 0 0 20px 4px rgba(200, 255, 0, 0.15); }
}
.generating {
    animation: pulse-glow 2s ease-in-out infinite;
    border-color: #C8FF00 !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #2a2a2a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #444; }

/* Hide label on some inputs */
.hide-label label { display: none !important; }
.hide-label .stTextInput label { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Password gate
# ---------------------------------------------------------------------------
if APP_PASSWORD:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center;
                    min-height: 80vh; flex-direction: column; gap: 12px;">
            <div style="font-size: 3rem;">🍌</div>
            <div style="font-size: 1.4rem; font-weight: 700; color: #C8FF00;
                        letter-spacing: -0.5px;">Nano Banana Studio</div>
            <div style="color: #555; font-size: 0.85rem; margin-bottom: 8px;">Enter password to continue</div>
        </div>
        """, unsafe_allow_html=True)

        col_l, col_mid, col_r = st.columns([2, 1, 2])
        with col_mid:
            pw = st.text_input("Password", type="password", label_visibility="collapsed",
                               placeholder="Password")
            if st.button("Enter", use_container_width=True, type="primary"):
                if pw == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong password")
        st.stop()


# ---------------------------------------------------------------------------
# Initialize session state
# ---------------------------------------------------------------------------
if "images" not in st.session_state:
    st.session_state.images = []
if "generating" not in st.session_state:
    st.session_state.generating = False
if "supabase_client" not in st.session_state:
    st.session_state.supabase_client = None
if "loaded_from_db" not in st.session_state:
    st.session_state.loaded_from_db = False


# ---------------------------------------------------------------------------
# Supabase helpers
# ---------------------------------------------------------------------------
def get_supabase():
    if st.session_state.supabase_client is not None:
        return st.session_state.supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY or "your_" in SUPABASE_URL:
        return None
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        st.session_state.supabase_client = client
        return client
    except Exception as e:
        st.toast(f"⚠️ Supabase connection failed: {e}", icon="⚠️")
        return None


def save_to_supabase(image_b64: str, prompt: str, aspect: str, resolution: str):
    sb = get_supabase()
    if sb is None:
        return None
    try:
        # Save image to storage
        img_id = str(uuid.uuid4())
        img_bytes = base64.b64decode(image_b64)
        file_path = f"{img_id}.png"

        sb.storage.from_("generated-images").upload(
            file_path, img_bytes, {"content-type": "image/png"}
        )

        public_url = sb.storage.from_("generated-images").get_public_url(file_path)

        # Save metadata to table
        record = {
            "id": img_id,
            "prompt": prompt,
            "aspect_ratio": aspect,
            "resolution": resolution,
            "image_url": public_url,
            "metadata": json.dumps({
                "model": MODEL_NAME,
                "timestamp": datetime.now().isoformat(),
            }),
        }
        sb.table("generated_images").insert(record).execute()
        return img_id
    except Exception as e:
        st.toast(f"⚠️ Save failed: {e}", icon="⚠️")
        return None


def load_from_supabase():
    sb = get_supabase()
    if sb is None:
        return []
    try:
        resp = sb.table("generated_images").select("*").order("created_at", desc=True).limit(200).execute()
        return resp.data if resp.data else []
    except Exception:
        return []


def delete_from_supabase(img_id: str):
    sb = get_supabase()
    if sb is None:
        return
    try:
        sb.storage.from_("generated-images").remove([f"{img_id}.png"])
        sb.table("generated_images").delete().eq("id", img_id).execute()
    except Exception as e:
        st.toast(f"⚠️ Delete failed: {e}", icon="⚠️")


# ---------------------------------------------------------------------------
# Load persisted images on first run
# ---------------------------------------------------------------------------
if not st.session_state.loaded_from_db:
    db_images = load_from_supabase()
    for row in db_images:
        st.session_state.images.append({
            "id": row.get("id", str(uuid.uuid4())),
            "prompt": row.get("prompt", ""),
            "aspect_ratio": row.get("aspect_ratio", "1:1"),
            "resolution": row.get("resolution", "2K"),
            "url": row.get("image_url", ""),
            "b64": None,
            "created_at": row.get("created_at", ""),
        })
    st.session_state.loaded_from_db = True


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
def generate_images(prompt: str, ref_images: list, aspect: str, resolution: str, batch: int):
    """Call Nano Banana Pro API and return list of base64-encoded images."""
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=GOOGLE_API_KEY)

    # Build contents list
    contents = []

    # Add reference images first
    for ref in ref_images:
        img = PILImage.open(io.BytesIO(ref))
        contents.append(img)

    # Add prompt
    contents.append(prompt)

    # Config
    effective_aspect = None if aspect == "Auto" else aspect

    img_config_kwargs = {}
    if effective_aspect:
        img_config_kwargs["aspect_ratio"] = effective_aspect
    img_config_kwargs["image_size"] = resolution

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(**img_config_kwargs),
    )

    results = []
    for i in range(batch):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=contents,
                config=config,
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    img_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                    results.append(img_b64)
        except Exception as e:
            st.toast(f"⚠️ Generation {i+1} failed: {e}", icon="⚠️")
            continue

    return results


# ---------------------------------------------------------------------------
# Top bar
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-logo">
        <span>🍌</span> Nano Banana Studio
    </div>
    <div class="top-bar-model">
        <b>●</b>&nbsp; Nano Banana Pro &nbsp;·&nbsp; {MODEL_NAME}
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Gallery
# ---------------------------------------------------------------------------
if not st.session_state.images:
    st.markdown("""
    <div class="empty-state">
        <h2>🍌</h2>
        <h2>Nano Banana Studio</h2>
        <p>Start creating by typing a prompt below.<br>
        Upload reference images for context-aware generation.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Build gallery HTML
    cards_html = ""
    for idx, img in enumerate(st.session_state.images):
        if img.get("b64"):
            src = f"data:image/png;base64,{img['b64']}"
        elif img.get("url"):
            src = img["url"]
        else:
            continue

        prompt_preview = (img.get("prompt", "")[:60] + "...") if len(img.get("prompt", "")) > 60 else img.get("prompt", "")
        prompt_escaped = prompt_preview.replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;")

        cards_html += f"""
        <div class="image-card" title="{prompt_escaped}">
            <img src="{src}" alt="Generated image" loading="lazy" />
            <div class="image-card-badge">
                NANO BANANA <span class="ai-dot"></span> Pro
            </div>
        </div>
        """

    st.markdown(f'<div class="image-grid">{cards_html}</div>', unsafe_allow_html=True)

    # Delete functionality via Streamlit (since HTML buttons can't trigger Python)
    with st.sidebar:
        st.markdown("### 🗑️ Manage Images")
        if st.session_state.images:
            for idx, img in enumerate(st.session_state.images):
                col1, col2 = st.columns([3, 1])
                prompt_short = (img.get("prompt", "Untitled")[:40] + "...") if len(img.get("prompt", "")) > 40 else img.get("prompt", "Untitled")
                col1.caption(f"#{idx+1} — {prompt_short}")
                if col2.button("🗑️", key=f"del_{idx}"):
                    if img.get("id"):
                        delete_from_supabase(img["id"])
                    st.session_state.images.pop(idx)
                    st.rerun()


# ---------------------------------------------------------------------------
# Bottom bar — Prompt & Controls
# ---------------------------------------------------------------------------
# Use Streamlit columns at the bottom for the input controls
st.markdown('<div style="height: 20px"></div>', unsafe_allow_html=True)

# Reference image upload (in an expander to keep it clean)
with st.expander("📎 Reference Images (optional — up to 14)", expanded=False):
    uploaded_refs = st.file_uploader(
        "Upload reference images",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="ref_uploader",
        label_visibility="collapsed",
    )
    if uploaded_refs:
        ref_cols = st.columns(min(len(uploaded_refs), 7))
        for i, ref in enumerate(uploaded_refs[:14]):
            ref_cols[i % len(ref_cols)].image(ref, width=80)
        if len(uploaded_refs) > 14:
            st.warning("Maximum 14 reference images. Only the first 14 will be used.")

# Main prompt area
prompt_cols = st.columns([6, 1, 1, 1, 1])

with prompt_cols[0]:
    prompt_text = st.text_input(
        "Prompt",
        placeholder="Describe the scene you imagine...",
        key="prompt_input",
        label_visibility="collapsed",
    )

with prompt_cols[1]:
    aspect_ratio = st.selectbox(
        "Aspect",
        ASPECT_RATIOS,
        index=0,
        key="aspect_select",
        label_visibility="collapsed",
    )

with prompt_cols[2]:
    resolution = st.selectbox(
        "Resolution",
        RESOLUTIONS,
        index=1,  # default 2K
        key="res_select",
        label_visibility="collapsed",
    )

with prompt_cols[3]:
    batch_size = st.selectbox(
        "Batch",
        list(range(1, MAX_BATCH + 1)),
        index=0,
        key="batch_select",
        format_func=lambda x: f"{x}/{MAX_BATCH}",
        label_visibility="collapsed",
    )

with prompt_cols[4]:
    generate_clicked = st.button(
        f"Generate ⚡ {batch_size}",
        key="generate_btn",
        type="primary",
        use_container_width=True,
    )

# Control pills display
pills_html = f"""
<div class="controls-row" style="margin-top: 4px;">
    <span class="ctrl-pill"><span class="dot"></span> <b>Nano Banana Pro</b></span>
    <span class="ctrl-pill">📐 <b>{aspect_ratio}</b></span>
    <span class="ctrl-pill">🖥️ <b>{resolution}</b></span>
    <span class="ctrl-pill">🔢 <b>{batch_size}/{MAX_BATCH}</b></span>
    {f'<span class="ctrl-pill">📎 <b>{min(len(uploaded_refs), 14)} refs</b></span>' if uploaded_refs else ''}
</div>
"""
st.markdown(pills_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Generate action
# ---------------------------------------------------------------------------
if generate_clicked:
    if not prompt_text.strip():
        st.toast("Please enter a prompt first!", icon="✏️")
    elif not GOOGLE_API_KEY:
        st.toast("Google API key not configured!", icon="🔑")
    else:
        ref_bytes = []
        if uploaded_refs:
            for ref in uploaded_refs[:14]:
                ref_bytes.append(ref.read())

        with st.spinner(f"🍌 Generating {batch_size} image{'s' if batch_size > 1 else ''}..."):
            results = generate_images(
                prompt=prompt_text,
                ref_images=ref_bytes,
                aspect=aspect_ratio,
                resolution=resolution,
                batch=batch_size,
            )

        if results:
            for b64 in results:
                img_id = save_to_supabase(b64, prompt_text, aspect_ratio, resolution)
                st.session_state.images.insert(0, {
                    "id": img_id or str(uuid.uuid4()),
                    "prompt": prompt_text,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "url": None,
                    "b64": b64,
                    "created_at": datetime.now().isoformat(),
                })
            st.toast(f"✅ Generated {len(results)} image{'s' if len(results) > 1 else ''}!", icon="🍌")
            st.rerun()
        else:
            st.toast("No images generated. Check your API key and try again.", icon="❌")
