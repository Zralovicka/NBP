import streamlit as st
import base64
import io
import os
import json
import uuid
import hashlib
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

# Auth token: a hash of the password so we can store it in query params safely
AUTH_TOKEN = hashlib.sha256(APP_PASSWORD.encode()).hexdigest()[:16] if APP_PASSWORD else ""

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

#MainMenu, footer, header {visibility: hidden;}
.stDeployButton {display: none;}
div[data-testid="stToolbar"] {display: none;}
div[data-testid="stDecoration"] {display: none;}

.main .block-container {
    padding: 60px 1.2rem 7rem 1.2rem !important;
    max-width: 100% !important;
}

/* Top bar */
.top-bar {
    position: fixed;
    top: 0; left: 0; right: 0;
    z-index: 99;
    background: #1a1a2e;
    border-bottom: 1px solid #2a2a3e;
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
.top-bar-right { display: flex; align-items: center; gap: 12px; }
.top-bar-pill {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 0.75rem;
    color: rgba(255,255,255,0.7);
    font-weight: 500;
}

/* Control pills */
.ctrl-pills {
    display: flex; align-items: center; gap: 6px;
    flex-wrap: wrap; margin-top: 4px;
}
.ctrl-pill {
    background: #262630; border: 1px solid #363645;
    border-radius: 20px; padding: 4px 13px;
    font-size: 0.72rem; color: #999; font-weight: 500;
    display: inline-flex; align-items: center; gap: 5px;
}
.ctrl-pill b { color: #ddd; }
.ctrl-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #C8FF00; display: inline-block;
}

/* Empty state */
.empty-state { text-align: center; padding: 80px 20px 60px; }
.empty-state h2 { font-size: 2.2rem; font-weight: 700; color: #555; margin-bottom: 6px; }
.empty-state p { font-size: 0.9rem; color: #777; max-width: 400px; margin: 0 auto; }

/* Detail view */
.detail-section-title {
    font-size: 0.72rem; color: #888; font-weight: 600;
    letter-spacing: 0.8px; text-transform: uppercase;
    margin-bottom: 8px; margin-top: 16px;
}
.detail-prompt {
    font-size: 0.88rem; line-height: 1.6;
    padding: 10px 14px; background: #f5f5f5;
    border-radius: 8px; border: 1px solid #e0e0e0; color: #333;
}
.detail-info-row {
    display: flex; justify-content: space-between;
    padding: 10px 0; border-bottom: 1px solid #eee; font-size: 0.84rem;
}
.detail-info-label { color: #888; }
.detail-info-value { color: #333; font-weight: 600; }

@media (prefers-color-scheme: dark) {
    .detail-prompt { background: #1e1e2e; border-color: #2e2e3e; color: #ddd; }
    .detail-info-row { border-bottom-color: #2a2a3a; }
    .detail-info-label { color: #888; }
    .detail-info-value { color: #ddd; }
}

/* Paste zone */
.paste-zone {
    border: 2px dashed #ccc;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
    color: #999;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.2s;
    margin-bottom: 8px;
}
.paste-zone:hover, .paste-zone.drag-over {
    border-color: #C8FF00;
    color: #666;
    background: rgba(200,255,0,0.03);
}
.paste-zone.has-images {
    border-color: #C8FF00;
    border-style: solid;
    background: rgba(200,255,0,0.05);
}
.paste-thumbs {
    display: flex; gap: 6px; flex-wrap: wrap;
    justify-content: center; margin-top: 8px;
}
.paste-thumbs img {
    width: 60px; height: 60px; object-fit: cover;
    border-radius: 6px; border: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Persistent auth — survives refresh via query params
# ---------------------------------------------------------------------------
def check_auth():
    """Check if user is authenticated, using query params to persist across refresh."""
    if not APP_PASSWORD:
        return True  # no password set, always authenticated

    # Check query params for auth token
    params = st.query_params
    if params.get("auth") == AUTH_TOKEN:
        return True

    # Check session state
    if st.session_state.get("authenticated"):
        return True

    return False


def do_login(password):
    """Attempt login, set query param on success."""
    if password == APP_PASSWORD:
        st.session_state.authenticated = True
        st.query_params["auth"] = AUTH_TOKEN
        return True
    return False


if not check_auth():
    st.markdown("""
    <div style="display:flex;justify-content:center;align-items:center;
                min-height:70vh;flex-direction:column;gap:12px;">
        <div style="font-size:3rem;">🍌</div>
        <div style="font-size:1.4rem;font-weight:700;color:#C8FF00;">Nano Banana Studio</div>
        <div style="color:#888;font-size:0.85rem;margin-bottom:8px;">Enter password to continue</div>
    </div>
    """, unsafe_allow_html=True)
    _l, _m, _r = st.columns([2, 1, 2])
    with _m:
        pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
        if st.button("Enter", use_container_width=True, type="primary"):
            if do_login(pw):
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
    "viewing_ref": None,
    "ref_from_gallery": None,
    "remix_prompt": None,       # pre-fill prompt from remix
    "remix_refs": None,         # pre-fill refs from remix
    "pasted_images": [],        # images pasted from clipboard
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
    sb = get_supabase()
    if sb is None:
        return None
    try:
        img_id = str(uuid.uuid4())
        img_bytes = base64.b64decode(image_b64)
        file_path = f"{img_id}.png"
        sb.storage.from_("generated-images").upload(file_path, img_bytes, {"content-type": "image/png"})
        public_url = sb.storage.from_("generated-images").get_public_url(file_path)

        ref_urls = []
        if ref_b64_list:
            for ri, rb64 in enumerate(ref_b64_list):
                ref_path = f"refs/{img_id}_ref{ri}.png"
                ref_bytes = base64.b64decode(rb64) if isinstance(rb64, str) else rb64
                sb.storage.from_("generated-images").upload(ref_path, ref_bytes, {"content-type": "image/png"})
                ref_url = sb.storage.from_("generated-images").get_public_url(ref_path)
                ref_urls.append(ref_url)

        record = {
            "id": img_id, "prompt": prompt, "aspect_ratio": aspect,
            "resolution": resolution, "image_url": public_url,
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
            "ref_b64s": [],
            "ref_urls": meta.get("ref_urls", []),
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
    sources = []
    for rb in img.get("ref_b64s", []):
        sources.append(("b64", rb))
    for ru in img.get("ref_urls", []):
        sources.append(("url", ru))
    return sources

def ref_src_to_display(ref_tuple):
    kind, val = ref_tuple
    if kind == "b64":
        return f"data:image/png;base64,{val}"
    return val


# ---------------------------------------------------------------------------
# TOP BAR
# ---------------------------------------------------------------------------
st.markdown(f"""
<div class="top-bar">
    <div class="top-bar-logo">🍌 Nano Banana Studio</div>
    <div class="top-bar-right">
        <span class="top-bar-pill">● Nano Banana Pro</span>
        <span class="top-bar-pill">{len(st.session_state.images)} images</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# VIEWING A REFERENCE IMAGE (sub-detail)
# ---------------------------------------------------------------------------
if st.session_state.viewing_ref is not None:
    st.subheader("🖼 Reference Image")
    st.image(st.session_state.viewing_ref, use_container_width=False, width=600)
    if st.button("← Back to image details", key="back_from_ref"):
        st.session_state.viewing_ref = None
        st.rerun()
    st.divider()


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
                if st.button("✕  Close", key="close_detail", use_container_width=True):
                    st.session_state.viewing_image = None
                    st.rerun()

                # PROMPT
                st.markdown('<div class="detail-section-title">✦ PROMPT</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="detail-prompt">{img.get("prompt", "No prompt")}</div>',
                    unsafe_allow_html=True,
                )

                # REMIX BUTTON (copies prompt + refs back to generation controls)
                if st.button("🔄  Remix (re-use prompt + refs)", key="detail_remix", use_container_width=True, type="primary"):
                    st.session_state.remix_prompt = img.get("prompt", "")
                    # Collect ref data for remix
                    ref_sources = get_ref_sources(img)
                    st.session_state.remix_refs = ref_sources
                    st.session_state.viewing_image = None
                    st.toast("Prompt & references loaded! Edit and hit Generate.", icon="🔄")
                    st.rerun()

                # INFORMATION
                st.markdown('<div class="detail-section-title">ⓘ INFORMATION</div>', unsafe_allow_html=True)
                created = str(img.get("created_at", ""))[:16].replace("T", " ")
                st.markdown(f"""
                <div class="detail-info-row"><span class="detail-info-label">Model</span><span class="detail-info-value">Nano Banana Pro</span></div>
                <div class="detail-info-row"><span class="detail-info-label">Quality</span><span class="detail-info-value">{img.get('resolution', '2K')}</span></div>
                <div class="detail-info-row"><span class="detail-info-label">Aspect Ratio</span><span class="detail-info-value">{img.get('aspect_ratio', 'Auto')}</span></div>
                <div class="detail-info-row"><span class="detail-info-label">Created</span><span class="detail-info-value">{created}</span></div>
                """, unsafe_allow_html=True)

                # REFERENCE IMAGES USED
                ref_sources = get_ref_sources(img)
                if ref_sources:
                    st.markdown('<div class="detail-section-title">🖼 REFERENCE IMAGES USED</div>', unsafe_allow_html=True)
                    ref_cols = st.columns(min(len(ref_sources), 4), gap="small")
                    for ri, rs in enumerate(ref_sources):
                        with ref_cols[ri % len(ref_cols)]:
                            st.image(ref_src_to_display(rs), width=80)
                            if st.button("Open", key=f"openref_{ri}", use_container_width=True):
                                st.session_state.viewing_ref = ref_src_to_display(rs)
                                st.rerun()

                # ACTIONS
                st.markdown('<div class="detail-section-title">⚡ ACTIONS</div>', unsafe_allow_html=True)

                if img.get("b64"):
                    st.download_button(
                        "⬇  Download", data=base64.b64decode(img["b64"]),
                        file_name=f"nanoBanana_{img.get('id', 'image')[:8]}.png",
                        mime="image/png", use_container_width=True, key="detail_dl",
                    )
                elif img.get("url"):
                    st.link_button("⬇  Download", img["url"], use_container_width=True)

                if st.button("🖼  Use as Reference", use_container_width=True, key="detail_ref"):
                    st.session_state.ref_from_gallery = img
                    st.session_state.viewing_image = None
                    st.toast("Image set as reference!", icon="🖼️")
                    st.rerun()

                if st.button("🗑  Delete", use_container_width=True, key="detail_del"):
                    if img.get("id"):
                        delete_from_supabase(img["id"])
                    st.session_state.images.pop(idx)
                    st.session_state.viewing_image = None
                    st.toast("Deleted", icon="🗑️")
                    st.rerun()

            st.divider()


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

                # Action buttons: View, Save, Remix, Delete
                b1, b2, b3, b4 = st.columns([1, 1, 1, 1], gap="small")
                with b1:
                    if st.button("👁", key=f"v_{actual_idx}", use_container_width=True, help="View details"):
                        st.session_state.viewing_image = actual_idx
                        st.rerun()
                with b2:
                    if img.get("b64"):
                        st.download_button(
                            "⬇", data=base64.b64decode(img["b64"]),
                            file_name=f"nb_{img.get('id','img')[:8]}.png",
                            mime="image/png", key=f"d_{actual_idx}",
                            use_container_width=True, help="Download",
                        )
                    elif img.get("url"):
                        st.link_button("⬇", img["url"], use_container_width=True)
                with b3:
                    if st.button("🔄", key=f"r_{actual_idx}", use_container_width=True, help="Remix"):
                        st.session_state.remix_prompt = img.get("prompt", "")
                        st.session_state.remix_refs = get_ref_sources(img)
                        st.toast("Prompt & refs loaded!", icon="🔄")
                        st.rerun()
                with b4:
                    if st.button("🗑", key=f"x_{actual_idx}", use_container_width=True, help="Delete"):
                        if img.get("id"):
                            delete_from_supabase(img["id"])
                        st.session_state.images.pop(actual_idx)
                        if st.session_state.viewing_image == actual_idx:
                            st.session_state.viewing_image = None
                        st.toast("Deleted", icon="🗑️")
                        st.rerun()

                prompt_short = img.get("prompt", "")[:50]
                if len(img.get("prompt", "")) > 50:
                    prompt_short += "…"
                ref_count = len(get_ref_sources(img))
                ref_tag = f" · 📎{ref_count}" if ref_count > 0 else ""
                st.caption(f"{prompt_short}{ref_tag}")


# ---------------------------------------------------------------------------
# CLIPBOARD PASTE ZONE — captures Ctrl+V images
# ---------------------------------------------------------------------------
st.markdown("")

# The paste zone uses a Streamlit component via html+js that communicates
# pasted image data back to Streamlit through a hidden text input
paste_component = st.container()
with paste_component:
    st.markdown("""
    <div id="paste-zone" class="paste-zone" tabindex="0"
         onclick="this.focus()"
         onpaste="handlePaste(event)"
         ondragover="event.preventDefault(); this.classList.add('drag-over');"
         ondragleave="this.classList.remove('drag-over');"
         ondrop="handleDrop(event)">
        📋 Click here and paste (Ctrl+V) or drag & drop images to add as references
        <div id="paste-thumbs" class="paste-thumbs"></div>
    </div>

    <script>
    const pastedImages = [];

    function handleImageData(dataUrl) {
        pastedImages.push(dataUrl);
        updateThumbs();
        updateStreamlit();
    }

    function handlePaste(event) {
        const items = event.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.startsWith('image/')) {
                event.preventDefault();
                const blob = items[i].getAsFile();
                const reader = new FileReader();
                reader.onload = function(e) {
                    handleImageData(e.target.result);
                };
                reader.readAsDataURL(blob);
                return;
            }
        }
    }

    function handleDrop(event) {
        event.preventDefault();
        document.getElementById('paste-zone').classList.remove('drag-over');
        const files = event.dataTransfer.files;
        for (let i = 0; i < files.length; i++) {
            if (files[i].type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    handleImageData(e.target.result);
                };
                reader.readAsDataURL(files[i]);
            }
        }
    }

    function updateThumbs() {
        const container = document.getElementById('paste-thumbs');
        const zone = document.getElementById('paste-zone');
        container.innerHTML = '';
        if (pastedImages.length > 0) {
            zone.classList.add('has-images');
        }
        pastedImages.forEach((src, idx) => {
            const img = document.createElement('img');
            img.src = src;
            img.title = 'Pasted image ' + (idx + 1);
            container.appendChild(img);
        });
    }

    function updateStreamlit() {
        // Write to a hidden textarea that Streamlit can read
        const el = document.getElementById('pasted-data-input');
        if (el) {
            // Store as JSON array of data URLs
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLTextAreaElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(el, JSON.stringify(pastedImages));
            el.dispatchEvent(new Event('input', { bubbles: true }));
        }
    }

    // Also listen for paste on the whole document as fallback
    document.addEventListener('paste', function(event) {
        const items = event.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.startsWith('image/')) {
                // Only handle if not in a text input
                const active = document.activeElement;
                if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
                    // Check if it's our hidden textarea or the paste zone
                    if (active.id !== 'pasted-data-input') {
                        // It's the prompt input — redirect to paste handler
                        event.preventDefault();
                        const blob = items[i].getAsFile();
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            handleImageData(e.target.result);
                        };
                        reader.readAsDataURL(blob);
                        return;
                    }
                }
            }
        }
    });
    </script>
    """, unsafe_allow_html=True)

# Hidden text area to receive pasted image data from JS
pasted_data = st.text_area(
    "pasted_data", key="pasted_data_input", label_visibility="collapsed",
    height=0, placeholder="",
)

# Hide the text area visually
st.markdown("""
<style>
div[data-testid="stTextArea"]:has(textarea#pasted-data-input),
div:has(> div > textarea[aria-label="pasted_data"]) {
    position: absolute !important;
    height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
}
</style>
""", unsafe_allow_html=True)

# Process pasted images
if pasted_data and pasted_data.strip().startswith("["):
    try:
        data_urls = json.loads(pasted_data)
        new_pasted = []
        for du in data_urls:
            if du.startswith("data:image"):
                # Extract base64 part
                b64_part = du.split(",", 1)[1] if "," in du else ""
                if b64_part and b64_part not in [p for p in st.session_state.pasted_images]:
                    new_pasted.append(b64_part)
        if new_pasted:
            st.session_state.pasted_images = new_pasted
    except Exception:
        pass

# Show pasted image previews
if st.session_state.pasted_images:
    pcols = st.columns(min(len(st.session_state.pasted_images), 7))
    for pi, pb64 in enumerate(st.session_state.pasted_images):
        pcols[pi % len(pcols)].image(f"data:image/png;base64,{pb64}", width=70)
    if st.button("✕ Clear pasted images", key="clear_pasted"):
        st.session_state.pasted_images = []
        st.rerun()


# ---------------------------------------------------------------------------
# REFERENCE IMAGES (file upload + gallery ref + remix refs)
# ---------------------------------------------------------------------------
with st.expander("📎 Reference Images (optional — up to 14)", expanded=False):
    uploaded_refs = st.file_uploader(
        "Upload reference images", type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True, key="ref_uploader", label_visibility="collapsed",
    )

    # Gallery reference
    if st.session_state.ref_from_gallery:
        ref_img = st.session_state.ref_from_gallery
        ref_src = get_img_src(ref_img)
        if ref_src:
            st.markdown("**From gallery:**")
            st.image(ref_src, width=120)
            if st.button("✕ Remove", key="rm_gal_ref"):
                st.session_state.ref_from_gallery = None
                st.rerun()

    # Remix references
    if st.session_state.remix_refs:
        st.markdown("**From remix:**")
        rmx_cols = st.columns(min(len(st.session_state.remix_refs), 5), gap="small")
        for ri, rs in enumerate(st.session_state.remix_refs):
            rmx_cols[ri % len(rmx_cols)].image(ref_src_to_display(rs), width=80)
        if st.button("✕ Clear remix refs", key="clear_remix_refs"):
            st.session_state.remix_refs = None
            st.rerun()

    # Uploaded file previews
    if uploaded_refs:
        rcols = st.columns(min(len(uploaded_refs), 7))
        for i, ref in enumerate(uploaded_refs[:14]):
            rcols[i % len(rcols)].image(ref, width=80)
        if len(uploaded_refs) > 14:
            st.warning("Max 14. Only first 14 used.")


# ---------------------------------------------------------------------------
# PROMPT ROW
# ---------------------------------------------------------------------------
# If remix is active, pre-fill the prompt
default_prompt = st.session_state.remix_prompt or ""

p1, p2, p3, p4, p5 = st.columns([6, 1, 1, 1, 1])
with p1:
    prompt_text = st.text_input(
        "Prompt", value=default_prompt,
        placeholder="Describe the scene you imagine...",
        key="prompt_input", label_visibility="collapsed",
    )
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

# Clear remix prompt after it's been loaded into the input
if st.session_state.remix_prompt:
    st.session_state.remix_prompt = None

# Pills
pp = [
    '<span class="ctrl-pill"><span class="ctrl-dot"></span> <b>Nano Banana Pro</b></span>',
    f'<span class="ctrl-pill">📐 <b>{aspect_ratio}</b></span>',
    f'<span class="ctrl-pill">🖥️ <b>{resolution}</b></span>',
    f'<span class="ctrl-pill">🔢 <b>{batch_size}/{MAX_BATCH}</b></span>',
]
total_refs = len(uploaded_refs or []) + len(st.session_state.pasted_images)
if st.session_state.ref_from_gallery:
    total_refs += 1
if st.session_state.remix_refs:
    total_refs += len(st.session_state.remix_refs)
if total_refs > 0:
    pp.append(f'<span class="ctrl-pill">📎 <b>{min(total_refs, 14)} refs</b></span>')
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
        ref_bytes = []
        ref_b64_for_storage = []

        # 1. Uploaded files
        if uploaded_refs:
            for ref in uploaded_refs[:14]:
                raw = ref.read()
                ref_bytes.append(raw)
                ref_b64_for_storage.append(base64.b64encode(raw).decode("utf-8"))

        # 2. Pasted images
        for pb64 in st.session_state.pasted_images:
            raw = base64.b64decode(pb64)
            ref_bytes.append(raw)
            ref_b64_for_storage.append(pb64)

        # 3. Gallery reference
        if st.session_state.ref_from_gallery:
            gal = st.session_state.ref_from_gallery
            if gal.get("b64"):
                raw = base64.b64decode(gal["b64"])
                ref_bytes.append(raw)
                ref_b64_for_storage.append(gal["b64"])

        # 4. Remix references
        if st.session_state.remix_refs:
            for kind, val in st.session_state.remix_refs:
                if kind == "b64":
                    raw = base64.b64decode(val)
                    ref_bytes.append(raw)
                    ref_b64_for_storage.append(val)
                # url refs from remix — we'd need to download them
                # For now, skip URL refs in generation (they're already in supabase)

        # Cap at 14
        ref_bytes = ref_bytes[:14]
        ref_b64_for_storage = ref_b64_for_storage[:14]

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
                    "url": None, "b64": b64,
                    "created_at": datetime.now().isoformat(),
                    "ref_b64s": ref_b64_for_storage,
                    "ref_urls": [],
                })
            # Clear pasted images and remix after generation
            st.session_state.pasted_images = []
            st.session_state.remix_refs = None
            st.toast(f"✅ {len(results)} image{'s' if len(results) > 1 else ''} generated!", icon="🍌")
            st.rerun()
        else:
            st.toast("Generation failed. Check API key / try again.", icon="❌")
