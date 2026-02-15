import streamlit as st
import base64
import io
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
def get_config(key: str, default: str = "") -> str:
    val = os.getenv(key, "")
    if not val:
        try:
            val = st.secrets.get(key, "")
        except Exception:
            pass
    return val or default

GOOGLE_API_KEY = get_config("GOOGLE_API_KEY")
SUPABASE_URL = get_config("SUPABASE_URL")
SUPABASE_KEY = get_config("SUPABASE_KEY")
APP_PASSWORD = get_config("APP_PASSWORD")

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
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

/* Hide Streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {display: none;}
div[data-testid="stDecoration"] {display: none;}

/* Push content below top bar */
.main .block-container {
    padding: 60px 1.2rem 7rem 1.2rem !important;
    max-width: 100% !important;
}

/* ---- Top bar ---- */
.top-bar {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 99;
    background: rgba(14,17,23,0.95);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255,255,255,0.06);
    padding: 10px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
    box-sizing: border-box;
}
.top-bar-logo {
    display: flex; align-items: center; gap: 8px;
    font-size: 1.05rem; font-weight: 700; color: #C8FF00;
}
.top-bar-right {
    display: flex; align-items: center; gap: 12px;
}
.top-bar-pill {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.5);
    font-weight: 500;
}
.top-bar-pill b { color: #C8FF00; }

/* ---- Control pills ---- */
.ctrl-pills {
    display: flex; align-items: center; gap: 6px;
    flex-wrap: wrap; margin-top: 2px;
}
.ctrl-pill {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 4px 13px;
    font-size: 0.72rem;
    color: rgba(255,255,255,0.45);
    font-weight: 500;
    display: inline-flex; align-items: center; gap: 5px;
}
.ctrl-pill b { color: rgba(255,255,255,0.8); }
.ctrl-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #C8FF00; display: inline-block;
}

/* ---- Empty state ---- */
.empty-state {
    text-align: center;
    padding: 80px 20px 60px;
}
.empty-state h2 {
    font-size: 2.2rem; font-weight: 700;
    color: rgba(255,255,255,0.15); margin-bottom: 6px;
}
.empty-state p {
    font-size: 0.9rem; color: rgba(255,255,255,0.25);
    max-width: 400px; margin: 0 auto;
}

/* ---- Detail view info styling ---- */
.info-row {
    display: flex; justify-content: space-between; padding: 9px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.82rem;
}
.info-label { color: rgba(255,255,255,0.4); }
.info-value { color: rgba(255,255,255,0.85); font-weight: 500; }
.section-title {
    font-size: 0.7rem; color: rgba(255,255,255,0.35); font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase; margin-bottom: 8px;
}
.prompt-text {
    font-size: 0.85rem; color: rgba(255,255,255,0.8); line-height: 1.55;
}

/* ---- Reference thumbs in detail ---- */
.ref-grid {
    display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px;
}
.ref-thumb-wrap {
    width: 72px; height: 72px; border-radius: 8px; overflow: hidden;
    border: 1px solid rgba(255,255,255,0.1);
    cursor: pointer; transition: border-color 0.15s;
}
.ref-thumb-wrap:hover { border-color: #C8FF00; }
.ref-thumb-wrap img {
    width: 100%; height: 100%; object-fit: cover; display: block;
}

/* ---- Streamlit widget overrides ---- */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: rgba(255,255,255,0.9) !important;
    font-size: 0.88rem !important;
    padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
    border-color: #C8FF00 !important;
    box-shadow: 0 0 0 1px rgba(200,255,0,0.2) !important;
}
.stTextInput > div > div > input::placeholder {
    color: rgba(255,255,255,0.25) !important;
}
.stSelectbox > div > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
}
div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
}

::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
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
        <div style="display:flex;justify-content:center;align-items:center;
                    min-height:70vh;flex-direction:column;gap:12px;">
            <div style="font-size:3rem;">🍌</div>
            <div style="font-size:1.4rem;font-weight:700;color:#C8FF00;">Nano Banana Studio</div>
            <div style="color:rgba(255,255,255,0.3);font-size:0.85rem;margin-bottom:8px;">Enter password to continue</div>
        </div>
        """, unsafe_allow_html=True)
        _l, _m, _r = st.columns([2, 1, 2])
        with _m:
            pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
            if st.button("Enter", use_container_width=True, type="primary"):
                if pw == APP_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Wrong password")
        st.stop()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
for key, default in {
    "images": [],
    "supabase_client": None,
    "loaded_from_db": False,
    "viewing_image": None,
    "viewing_ref": None,       # viewing a reference image from detail
    "ref_from_gallery": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


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
        st.toast(f"⚠️ Supabase: {e}", icon="⚠️")
        return None


def save_to_supabase(image_b64, prompt, aspect, resolution, ref_b64_list=None):
    """Save image + metadata + reference thumbnails to Supabase."""
    sb = get_supabase()
    if sb is None:
        return None
    try:
        img_id = str(uuid.uuid4())
        img_bytes = base64.b64decode(image_b64)
        file_path = f"{img_id}.png"
        sb.storage.from_("generated-images").upload(file_path, img_bytes, {"content-type": "image/png"})
        public_url = sb.storage.from_("generated-images").get_public_url(file_path)

        # Save reference image thumbnails to storage too
        ref_urls = []
        if ref_b64_list:
            for ri, rb64 in enumerate(ref_b64_list):
                ref_path = f"refs/{img_id}_ref{ri}.png"
                ref_bytes = base64.b64decode(rb64) if isinstance(rb64, str) else rb64
                sb.storage.from_("generated-images").upload(ref_path, ref_bytes, {"content-type": "image/png"})
                ref_url = sb.storage.from_("generated-images").get_public_url(ref_path)
                ref_urls.append(ref_url)

        record = {
            "id": img_id,
            "prompt": prompt,
            "aspect_ratio": aspect,
            "resolution": resolution,
            "image_url": public_url,
            "metadata": json.dumps({
                "model": MODEL_NAME,
                "timestamp": datetime.now().isoformat(),
                "ref_urls": ref_urls,
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


def delete_from_supabase(img_id):
    sb = get_supabase()
    if sb is None:
        return
    try:
        sb.storage.from_("generated-images").remove([f"{img_id}.png"])
        sb.table("generated_images").delete().eq("id", img_id).execute()
    except Exception as e:
        st.toast(f"⚠️ Delete failed: {e}", icon="⚠️")


# ---------------------------------------------------------------------------
# Load from DB
# ---------------------------------------------------------------------------
if not st.session_state.loaded_from_db:
    db_images = load_from_supabase()
    for row in db_images:
        meta = {}
        try:
            meta = json.loads(row.get("metadata", "{}"))
        except Exception:
            pass
        st.session_state.images.append({
            "id": row.get("id", str(uuid.uuid4())),
            "prompt": row.get("prompt", ""),
            "aspect_ratio": row.get("aspect_ratio", "1:1"),
            "resolution": row.get("resolution", "2K"),
            "url": row.get("image_url", ""),
            "b64": None,
            "created_at": row.get("created_at", ""),
            "ref_b64s": [],               # base64 refs (only for current session)
            "ref_urls": meta.get("ref_urls", []),  # persisted ref URLs from supabase
        })
    st.session_state.loaded_from_db = True


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
def generate_images(prompt, ref_images, aspect, resolution, batch):
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=GOOGLE_API_KEY)
    contents = []
    for ref in ref_images:
        img = PILImage.open(io.BytesIO(ref))
        contents.append(img)
    contents.append(prompt)

    effective_aspect = None if aspect == "Auto" else aspect
    img_cfg = {"image_size": resolution}
    if effective_aspect:
        img_cfg["aspect_ratio"] = effective_aspect

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(**img_cfg),
    )

    results = []
    for i in range(batch):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME, contents=contents, config=config,
            )
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    results.append(base64.b64encode(part.inline_data.data).decode("utf-8"))
        except Exception as e:
            st.toast(f"⚠️ Generation {i+1}: {e}", icon="⚠️")
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_img_src(img):
    if img.get("b64"):
        return f"data:image/png;base64,{img['b64']}"
    if img.get("url"):
        return img["url"]
    return None


def get_ref_sources(img):
    """Get all reference image sources (b64 or url) for an image."""
    sources = []
    for rb in img.get("ref_b64s", []):
        sources.append(f"data:image/png;base64,{rb}")
    for ru in img.get("ref_urls", []):
        sources.append(ru)
    return sources


# ---------------------------------------------------------------------------
# TOP BAR
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-logo">🍌 Nano Banana Studio</div>
    <div class="top-bar-right">
        <span class="top-bar-pill"><b>●</b>&nbsp; Nano Banana Pro</span>
        <span class="top-bar-pill">{len(st.session_state.images)} images</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# VIEWING A REFERENCE IMAGE (sub-detail)
# ---------------------------------------------------------------------------
if st.session_state.viewing_ref is not None:
    st.markdown("#### 🖼 Reference Image")
    ref_src = st.session_state.viewing_ref
    st.image(ref_src, use_container_width=False, width=600)
    if st.button("← Back to image details", key="back_from_ref"):
        st.session_state.viewing_ref = None
        st.rerun()
    st.markdown("---")


# ---------------------------------------------------------------------------
# DETAIL VIEW
# ---------------------------------------------------------------------------
elif st.session_state.viewing_image is not None:
    idx = st.session_state.viewing_image
    if idx < len(st.session_state.images):
        img = st.session_state.images[idx]
        src = get_img_src(img)

        if src:
            col_img, col_info = st.columns([3, 1], gap="medium")

            with col_img:
                st.image(src, use_container_width=True)

            with col_info:
                # Close
                if st.button("✕  Close", key="close_detail", use_container_width=True):
                    st.session_state.viewing_image = None
                    st.rerun()

                st.markdown("")

                # ---- PROMPT ----
                st.markdown('<div class="section-title">✦ PROMPT</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="prompt-text">{img.get("prompt", "No prompt")}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown("<br>", unsafe_allow_html=True)

                # ---- INFORMATION ----
                st.markdown('<div class="section-title">ⓘ INFORMATION</div>', unsafe_allow_html=True)
                created = str(img.get("created_at", ""))[:16].replace("T", " ")
                st.markdown(f"""
                <div class="info-row"><span class="info-label">Model</span><span class="info-value">Nano Banana Pro</span></div>
                <div class="info-row"><span class="info-label">Quality</span><span class="info-value">{img.get('resolution', '2K')}</span></div>
                <div class="info-row"><span class="info-label">Aspect Ratio</span><span class="info-value">{img.get('aspect_ratio', 'Auto')}</span></div>
                <div class="info-row"><span class="info-label">Created</span><span class="info-value">{created}</span></div>
                """, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

                # ---- REFERENCE IMAGES USED ----
                ref_sources = get_ref_sources(img)
                if ref_sources:
                    st.markdown('<div class="section-title">🖼 REFERENCE IMAGES USED</div>', unsafe_allow_html=True)
                    ref_cols = st.columns(min(len(ref_sources), 4), gap="small")
                    for ri, rsrc in enumerate(ref_sources):
                        with ref_cols[ri % len(ref_cols)]:
                            st.image(rsrc, width=80)
                            if st.button("Open", key=f"openref_{ri}", use_container_width=True):
                                st.session_state.viewing_ref = rsrc
                                st.rerun()
                    st.markdown("<br>", unsafe_allow_html=True)

                # ---- ACTIONS ----
                st.markdown('<div class="section-title">⚡ ACTIONS</div>', unsafe_allow_html=True)

                # Download
                if img.get("b64"):
                    st.download_button(
                        "⬇  Download",
                        data=base64.b64decode(img["b64"]),
                        file_name=f"nanoBanana_{img.get('id', 'image')[:8]}.png",
                        mime="image/png",
                        use_container_width=True,
                        key="detail_dl",
                    )
                elif img.get("url"):
                    st.link_button("⬇  Download", img["url"], use_container_width=True)

                # Use as reference
                if st.button("🖼  Use as Reference", use_container_width=True, key="detail_ref"):
                    st.session_state.ref_from_gallery = img
                    st.session_state.viewing_image = None
                    st.toast("Image set as reference!", icon="🖼️")
                    st.rerun()

                # Delete
                if st.button("🗑  Delete", use_container_width=True, key="detail_del"):
                    if img.get("id"):
                        delete_from_supabase(img["id"])
                    st.session_state.images.pop(idx)
                    st.session_state.viewing_image = None
                    st.toast("Deleted", icon="🗑️")
                    st.rerun()

            st.markdown("---")


# ---------------------------------------------------------------------------
# GALLERY GRID
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
    cols_per_row = 4
    images = st.session_state.images
    rows = [images[i:i + cols_per_row] for i in range(0, len(images), cols_per_row)]

    for row_imgs in rows:
        cols = st.columns(cols_per_row, gap="small")
        for col_idx, img in enumerate(row_imgs):
            with cols[col_idx]:
                src = get_img_src(img)
                if not src:
                    continue
                actual_idx = st.session_state.images.index(img)

                st.image(src, use_container_width=True)

                # Action buttons
                b1, b2, b3 = st.columns([1, 1, 1], gap="small")
                with b1:
                    if st.button("👁 View", key=f"v_{actual_idx}", use_container_width=True):
                        st.session_state.viewing_image = actual_idx
                        st.rerun()
                with b2:
                    if img.get("b64"):
                        st.download_button(
                            "⬇ Save", data=base64.b64decode(img["b64"]),
                            file_name=f"nb_{img.get('id','img')[:8]}.png",
                            mime="image/png", key=f"d_{actual_idx}",
                            use_container_width=True,
                        )
                    elif img.get("url"):
                        st.link_button("⬇ Save", img["url"], use_container_width=True)
                with b3:
                    if st.button("🗑", key=f"x_{actual_idx}", use_container_width=True):
                        if img.get("id"):
                            delete_from_supabase(img["id"])
                        st.session_state.images.pop(actual_idx)
                        if st.session_state.viewing_image == actual_idx:
                            st.session_state.viewing_image = None
                        st.toast("Deleted", icon="🗑️")
                        st.rerun()

                # Prompt caption + ref count
                prompt_short = img.get("prompt", "")[:50]
                if len(img.get("prompt", "")) > 50:
                    prompt_short += "…"
                ref_count = len(get_ref_sources(img))
                ref_tag = f" · 📎{ref_count}" if ref_count > 0 else ""
                st.caption(f"{prompt_short}{ref_tag}")


# ---------------------------------------------------------------------------
# BOTTOM — Reference upload + Prompt + Controls
# ---------------------------------------------------------------------------
st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

with st.expander("📎 Reference Images (optional — up to 14)", expanded=False):
    uploaded_refs = st.file_uploader(
        "Upload reference images", type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True, key="ref_uploader", label_visibility="collapsed",
    )
    if st.session_state.ref_from_gallery:
        ref_img = st.session_state.ref_from_gallery
        ref_src = get_img_src(ref_img)
        if ref_src:
            st.markdown("**From gallery:**")
            st.image(ref_src, width=120)
            if st.button("✕ Remove", key="rm_gal_ref"):
                st.session_state.ref_from_gallery = None
                st.rerun()
    if uploaded_refs:
        rcols = st.columns(min(len(uploaded_refs), 7))
        for i, ref in enumerate(uploaded_refs[:14]):
            rcols[i % len(rcols)].image(ref, width=80)
        if len(uploaded_refs) > 14:
            st.warning("Max 14. Only first 14 used.")

# Prompt row
p1, p2, p3, p4, p5 = st.columns([6, 1, 1, 1, 1])
with p1:
    prompt_text = st.text_input("Prompt", placeholder="Describe the scene you imagine...",
                                key="prompt_input", label_visibility="collapsed")
with p2:
    aspect_ratio = st.selectbox("Aspect", ASPECT_RATIOS, index=0,
                                key="aspect_select", label_visibility="collapsed")
with p3:
    resolution = st.selectbox("Resolution", RESOLUTIONS, index=1,
                              key="res_select", label_visibility="collapsed")
with p4:
    batch_size = st.selectbox("Batch", list(range(1, MAX_BATCH + 1)), index=0,
                              key="batch_select", format_func=lambda x: f"{x}/{MAX_BATCH}",
                              label_visibility="collapsed")
with p5:
    generate_clicked = st.button(f"Generate ⚡ {batch_size}", key="gen_btn",
                                 type="primary", use_container_width=True)

# Pills
pp = [
    '<span class="ctrl-pill"><span class="ctrl-dot"></span> <b>Nano Banana Pro</b></span>',
    f'<span class="ctrl-pill">📐 <b>{aspect_ratio}</b></span>',
    f'<span class="ctrl-pill">🖥️ <b>{resolution}</b></span>',
    f'<span class="ctrl-pill">🔢 <b>{batch_size}/{MAX_BATCH}</b></span>',
]
if uploaded_refs:
    pp.append(f'<span class="ctrl-pill">📎 <b>{min(len(uploaded_refs), 14)} refs</b></span>')
if st.session_state.ref_from_gallery:
    pp.append('<span class="ctrl-pill">🖼 <b>1 gallery ref</b></span>')
st.markdown(f'<div class="ctrl-pills">{"".join(pp)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# GENERATE ACTION
# ---------------------------------------------------------------------------
if generate_clicked:
    if not prompt_text.strip():
        st.toast("Enter a prompt first!", icon="✏️")
    elif not GOOGLE_API_KEY:
        st.toast("Google API key not configured!", icon="🔑")
    else:
        # Collect reference bytes
        ref_bytes = []
        ref_b64_for_storage = []  # base64 versions to store with the image record

        if uploaded_refs:
            for ref in uploaded_refs[:14]:
                raw = ref.read()
                ref_bytes.append(raw)
                ref_b64_for_storage.append(base64.b64encode(raw).decode("utf-8"))

        if st.session_state.ref_from_gallery:
            gal = st.session_state.ref_from_gallery
            if gal.get("b64"):
                raw = base64.b64decode(gal["b64"])
                ref_bytes.append(raw)
                ref_b64_for_storage.append(gal["b64"])

        with st.spinner(f"🍌 Generating {batch_size} image{'s' if batch_size > 1 else ''}..."):
            results = generate_images(prompt_text, ref_bytes, aspect_ratio, resolution, batch_size)

        if results:
            for b64 in results:
                img_id = save_to_supabase(b64, prompt_text, aspect_ratio, resolution, ref_b64_for_storage)
                st.session_state.images.insert(0, {
                    "id": img_id or str(uuid.uuid4()),
                    "prompt": prompt_text,
                    "aspect_ratio": aspect_ratio,
                    "resolution": resolution,
                    "url": None,
                    "b64": b64,
                    "created_at": datetime.now().isoformat(),
                    "ref_b64s": ref_b64_for_storage,
                    "ref_urls": [],
                })
            st.toast(f"✅ {len(results)} image{'s' if len(results) > 1 else ''} generated!", icon="🍌")
            st.rerun()
        else:
            st.toast("Generation failed. Check API key / try again.", icon="❌")
