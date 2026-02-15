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
def get_config(key, default=""):
    val = os.getenv(key, "")
    if not val:
        try: val = st.secrets.get(key, "")
        except: pass
    return val or default

GOOGLE_API_KEY = get_config("GOOGLE_API_KEY")
SUPABASE_URL = get_config("SUPABASE_URL")
SUPABASE_KEY = get_config("SUPABASE_KEY")
APP_PASSWORD = get_config("APP_PASSWORD")

ASPECT_RATIOS = ["Auto", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
RESOLUTIONS = ["1K", "2K", "4K"]
MAX_BATCH = 4
MODEL_NAME = "gemini-3-pro-image-preview"
AUTH_TOKEN = hashlib.sha256(APP_PASSWORD.encode()).hexdigest()[:16] if APP_PASSWORD else ""

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Nano Banana Studio", page_icon="🍌", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Full custom CSS — product-grade dark UI
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ===== GLOBAL RESET ===== */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, sans-serif !important;
    background-color: #0c0c0f !important;
    color: #e2e2e6 !important;
}
.stApp { background: #0c0c0f !important; }

/* Hide ALL Streamlit chrome */
#MainMenu, footer, header, .stDeployButton,
div[data-testid="stToolbar"],
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"],
div[data-testid="stHeader"] { display: none !important; }

.main .block-container {
    padding: 56px 20px 140px 20px !important;
    max-width: 100% !important;
}

/* ===== TOP NAV BAR ===== */
.nav-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    height: 50px;
    background: rgba(12,12,15,0.85);
    backdrop-filter: blur(20px) saturate(1.2);
    -webkit-backdrop-filter: blur(20px) saturate(1.2);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px;
}
.nav-logo {
    display: flex; align-items: center; gap: 10px;
    font-size: 0.95rem; font-weight: 700; color: #C8FF00;
    letter-spacing: -0.3px;
}
.nav-logo img { height: 22px; }
.nav-right { display: flex; align-items: center; gap: 10px; }
.nav-chip {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 100px; padding: 4px 14px;
    font-size: 0.7rem; color: rgba(255,255,255,0.5); font-weight: 500;
    display: flex; align-items: center; gap: 6px;
}
.nav-chip .dot {
    width: 6px; height: 6px; border-radius: 50%; background: #C8FF00;
}

/* ===== IMAGE GRID ===== */
.gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 8px;
}

/* ===== PLACEHOLDER / GENERATING CARD ===== */
.gen-placeholder {
    aspect-ratio: 1;
    background: #111114;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 12px;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    gap: 12px;
    animation: placeholder-pulse 2s ease-in-out infinite;
}
@keyframes placeholder-pulse {
    0%, 100% { border-color: rgba(200,255,0,0.05); background: #111114; }
    50% { border-color: rgba(200,255,0,0.2); background: #13131a; }
}
.gen-placeholder .spinner {
    width: 32px; height: 32px;
    border: 3px solid rgba(255,255,255,0.06);
    border-top: 3px solid #C8FF00;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.gen-placeholder .gen-text {
    font-size: 0.75rem; color: rgba(255,255,255,0.3); font-weight: 500;
}

/* ===== EMPTY STATE ===== */
.empty-hero {
    text-align: center; padding: 100px 20px 60px;
}
.empty-hero .emoji { font-size: 3.5rem; margin-bottom: 12px; }
.empty-hero h1 {
    font-size: 1.8rem; font-weight: 800; color: rgba(255,255,255,0.08);
    letter-spacing: -0.5px; margin: 0 0 8px 0;
}
.empty-hero p {
    font-size: 0.88rem; color: rgba(255,255,255,0.2);
    max-width: 380px; margin: 0 auto; line-height: 1.5;
}

/* ===== DETAIL VIEW ===== */
.detail-prompt-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px; padding: 14px 16px;
    font-size: 0.86rem; color: #ccc; line-height: 1.6;
    margin-bottom: 4px;
}
.detail-label {
    font-size: 0.65rem; color: rgba(255,255,255,0.3); font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    margin: 18px 0 8px 0;
}
.detail-row {
    display: flex; justify-content: space-between;
    padding: 9px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 0.82rem;
}
.detail-row-k { color: rgba(255,255,255,0.35); }
.detail-row-v { color: #ccc; font-weight: 600; }

/* ===== BOTTOM CONTROL BAR ===== */
.bottom-pills {
    display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 6px;
}
.bpill {
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 100px; padding: 4px 13px;
    font-size: 0.68rem; color: rgba(255,255,255,0.4); font-weight: 500;
    display: inline-flex; align-items: center; gap: 5px;
}
.bpill b { color: rgba(255,255,255,0.75); }
.bpill .dot { width: 5px; height: 5px; border-radius: 50%; background: #C8FF00; }

/* ===== STREAMLIT WIDGET OVERRIDES ===== */
/* Text input */
.stTextInput > div > div > input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #ddd !important;
    font-size: 0.88rem !important;
    padding: 11px 14px !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: rgba(200,255,0,0.5) !important;
    box-shadow: 0 0 0 2px rgba(200,255,0,0.08) !important;
}
.stTextInput > div > div > input::placeholder { color: rgba(255,255,255,0.2) !important; }

/* Select boxes */
.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"] > div {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: #ccc !important;
    font-size: 0.8rem !important;
}

/* Buttons */
.stButton > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.15s !important;
    padding: 6px 12px !important;
}
.stButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: #fff !important;
}
/* Primary button */
.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
    background: #C8FF00 !important;
    border-color: #C8FF00 !important;
    color: #0c0c0f !important;
    font-weight: 700 !important;
}
.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
    background: #d4ff33 !important;
    color: #0c0c0f !important;
}

/* Download button */
.stDownloadButton > button {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
}
.stDownloadButton > button:hover {
    background: rgba(255,255,255,0.1) !important;
    color: #fff !important;
}

/* Link button */
.stLinkButton > a {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    color: rgba(255,255,255,0.7) !important;
    font-size: 0.78rem !important;
}

/* Expander */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary span {
    color: rgba(255,255,255,0.5) !important;
    font-size: 0.82rem !important;
}

/* File uploader */
div[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
}
div[data-testid="stFileUploader"] label,
div[data-testid="stFileUploader"] span,
div[data-testid="stFileUploader"] p,
div[data-testid="stFileUploader"] small {
    color: rgba(255,255,255,0.4) !important;
}

/* Captions */
.stCaption, [data-testid="stCaptionContainer"] {
    color: rgba(255,255,255,0.3) !important;
    font-size: 0.72rem !important;
}

/* Divider */
hr { border-color: rgba(255,255,255,0.05) !important; }

/* Spinner */
.stSpinner > div > div { border-top-color: #C8FF00 !important; }

/* Toast */
div[data-testid="stToast"] {
    background: #1a1a24 !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    color: #ccc !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.15); }

/* Error messages - make readable */
.stAlert, div[data-testid="stAlert"] {
    background: rgba(255,60,60,0.08) !important;
    border: 1px solid rgba(255,60,60,0.15) !important;
    border-radius: 10px !important;
}

/* Image captions in grid */
.img-caption {
    font-size: 0.72rem; color: rgba(255,255,255,0.3);
    margin-top: 2px; line-height: 1.35;
    overflow: hidden; text-overflow: ellipsis;
    white-space: nowrap;
}

/* Subheader */
h1, h2, h3, .stSubheader {
    color: #e2e2e6 !important;
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def check_auth():
    if not APP_PASSWORD: return True
    if st.query_params.get("auth") == AUTH_TOKEN: return True
    return st.session_state.get("authenticated", False)

def do_login(password):
    if password == APP_PASSWORD:
        st.session_state.authenticated = True
        st.query_params["auth"] = AUTH_TOKEN
        return True
    return False

if not check_auth():
    st.markdown("""
    <div style="display:flex;justify-content:center;align-items:center;
                min-height:80vh;flex-direction:column;gap:14px;">
        <div style="font-size:3.5rem;">🍌</div>
        <div style="font-size:1.3rem;font-weight:800;color:#C8FF00;letter-spacing:-0.5px;">
            Nano Banana Studio</div>
        <div style="color:rgba(255,255,255,0.25);font-size:0.82rem;">
            Enter password to continue</div>
    </div>
    """, unsafe_allow_html=True)
    _l, _m, _r = st.columns([2, 1, 2])
    with _m:
        pw = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
        if st.button("Enter", use_container_width=True, type="primary"):
            if do_login(pw): st.rerun()
            else: st.error("Wrong password")
    st.stop()


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
defaults = {
    "images": [], "supabase_client": None, "loaded_from_db": False,
    "viewing_image": None, "viewing_ref": None, "ref_from_gallery": None,
    "remix_prompt": None, "remix_refs": None, "generating_count": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
def get_supabase():
    if st.session_state.supabase_client: return st.session_state.supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY or "your_" in SUPABASE_URL: return None
    try:
        from supabase import create_client
        c = create_client(SUPABASE_URL, SUPABASE_KEY)
        st.session_state.supabase_client = c
        return c
    except Exception as e:
        st.toast(f"⚠️ Supabase: {e}", icon="⚠️"); return None

def save_to_supabase(image_b64, prompt, aspect, resolution, ref_b64_list=None):
    sb = get_supabase()
    if not sb: return None
    try:
        img_id = str(uuid.uuid4())
        sb.storage.from_("generated-images").upload(
            f"{img_id}.png", base64.b64decode(image_b64), {"content-type": "image/png"})
        public_url = sb.storage.from_("generated-images").get_public_url(f"{img_id}.png")
        ref_urls = []
        if ref_b64_list:
            for ri, rb in enumerate(ref_b64_list):
                rp = f"refs/{img_id}_ref{ri}.png"
                rb_bytes = base64.b64decode(rb) if isinstance(rb, str) else rb
                sb.storage.from_("generated-images").upload(rp, rb_bytes, {"content-type": "image/png"})
                ref_urls.append(sb.storage.from_("generated-images").get_public_url(rp))
        sb.table("generated_images").insert({
            "id": img_id, "prompt": prompt, "aspect_ratio": aspect,
            "resolution": resolution, "image_url": public_url,
            "metadata": json.dumps({"model": MODEL_NAME, "timestamp": datetime.now().isoformat(), "ref_urls": ref_urls}),
        }).execute()
        return img_id
    except Exception as e:
        st.toast(f"⚠️ Save: {e}", icon="⚠️"); return None

def load_from_supabase():
    sb = get_supabase()
    if not sb: return []
    try:
        r = sb.table("generated_images").select("*").order("created_at", desc=True).limit(200).execute()
        return r.data or []
    except: return []

def delete_from_supabase(img_id):
    sb = get_supabase()
    if not sb: return
    try:
        sb.storage.from_("generated-images").remove([f"{img_id}.png"])
        sb.table("generated_images").delete().eq("id", img_id).execute()
    except Exception as e:
        st.toast(f"⚠️ Delete: {e}", icon="⚠️")

# Load DB
if not st.session_state.loaded_from_db:
    for row in load_from_supabase():
        meta = {}
        try: meta = json.loads(row.get("metadata", "{}"))
        except: pass
        st.session_state.images.append({
            "id": row.get("id", str(uuid.uuid4())),
            "prompt": row.get("prompt", ""),
            "aspect_ratio": row.get("aspect_ratio", "1:1"),
            "resolution": row.get("resolution", "2K"),
            "url": row.get("image_url", ""), "b64": None,
            "created_at": row.get("created_at", ""),
            "ref_b64s": [], "ref_urls": meta.get("ref_urls", []),
        })
    st.session_state.loaded_from_db = True


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate_images(prompt, ref_images, aspect, resolution, batch):
    from google import genai
    from google.genai import types
    from PIL import Image as PILImage

    client = genai.Client(api_key=GOOGLE_API_KEY)
    contents = [PILImage.open(io.BytesIO(r)) for r in ref_images] + [prompt]

    ar = None if aspect == "Auto" else aspect
    cfg_kw = {"image_size": resolution}
    if ar: cfg_kw["aspect_ratio"] = ar

    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"],
        image_config=types.ImageConfig(**cfg_kw),
    )
    results = []
    for i in range(batch):
        try:
            resp = client.models.generate_content(model=MODEL_NAME, contents=contents, config=config)
            for part in resp.candidates[0].content.parts:
                if part.inline_data:
                    results.append(base64.b64encode(part.inline_data.data).decode("utf-8"))
        except Exception as e:
            st.toast(f"⚠️ Gen {i+1}: {e}", icon="⚠️")
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def img_src(img):
    if img.get("b64"): return f"data:image/png;base64,{img['b64']}"
    if img.get("url"): return img["url"]
    return None

def get_refs(img):
    s = [("b64", r) for r in img.get("ref_b64s", [])]
    s += [("url", r) for r in img.get("ref_urls", [])]
    return s

def ref_display(r):
    return f"data:image/png;base64,{r[1]}" if r[0] == "b64" else r[1]


# ---------------------------------------------------------------------------
# NAV BAR
# ---------------------------------------------------------------------------
n_img = len(st.session_state.images)
st.markdown(f"""
<div class="nav-bar">
    <div class="nav-logo">🍌 Nano Banana Studio</div>
    <div class="nav-right">
        <div class="nav-chip"><span class="dot"></span> Nano Banana Pro</div>
        <div class="nav-chip">{n_img} image{"s" if n_img != 1 else ""}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DETAIL VIEW
# ---------------------------------------------------------------------------
if st.session_state.viewing_ref is not None:
    st.subheader("🖼 Reference Image")
    st.image(st.session_state.viewing_ref, use_container_width=False, width=600)
    if st.button("← Back", key="back_ref"):
        st.session_state.viewing_ref = None; st.rerun()
    st.divider()

elif st.session_state.viewing_image is not None:
    idx = st.session_state.viewing_image
    if idx < len(st.session_state.images):
        img = st.session_state.images[idx]
        src = img_src(img)
        if src:
            ci, cs = st.columns([3, 1], gap="medium")
            with ci:
                st.image(src, use_container_width=True)
            with cs:
                if st.button("✕  Close", key="cls", use_container_width=True):
                    st.session_state.viewing_image = None; st.rerun()

                # Prompt
                st.markdown('<div class="detail-label">✦ PROMPT</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-prompt-box">{img.get("prompt","—")}</div>', unsafe_allow_html=True)

                # Remix
                if st.button("🔄  Remix", key="rmx", use_container_width=True, type="primary"):
                    st.session_state.remix_prompt = img.get("prompt", "")
                    st.session_state.remix_refs = get_refs(img)
                    st.session_state.viewing_image = None
                    st.toast("Prompt & refs loaded!", icon="🔄"); st.rerun()

                # Info
                st.markdown('<div class="detail-label">ⓘ INFORMATION</div>', unsafe_allow_html=True)
                created = str(img.get("created_at", ""))[:16].replace("T", " ")
                for k, v in [("Model", "Nano Banana Pro"), ("Quality", img.get("resolution", "2K")),
                             ("Aspect", img.get("aspect_ratio", "Auto")), ("Created", created)]:
                    st.markdown(f'<div class="detail-row"><span class="detail-row-k">{k}</span><span class="detail-row-v">{v}</span></div>', unsafe_allow_html=True)

                # Refs
                refs = get_refs(img)
                if refs:
                    st.markdown('<div class="detail-label">🖼 REFERENCES USED</div>', unsafe_allow_html=True)
                    rc = st.columns(min(len(refs), 4), gap="small")
                    for ri, r in enumerate(refs):
                        with rc[ri % len(rc)]:
                            st.image(ref_display(r), width=72)
                            if st.button("Open", key=f"or_{ri}", use_container_width=True):
                                st.session_state.viewing_ref = ref_display(r); st.rerun()

                # Actions
                st.markdown('<div class="detail-label">⚡ ACTIONS</div>', unsafe_allow_html=True)
                if img.get("b64"):
                    st.download_button("⬇  Download", base64.b64decode(img["b64"]),
                        f"nb_{img['id'][:8]}.png", "image/png", use_container_width=True, key="ddl")
                elif img.get("url"):
                    st.link_button("⬇  Download", img["url"], use_container_width=True)
                if st.button("🖼  Use as Reference", use_container_width=True, key="dref"):
                    st.session_state.ref_from_gallery = img
                    st.session_state.viewing_image = None
                    st.toast("Set as reference!", icon="🖼️"); st.rerun()
                if st.button("🗑  Delete", use_container_width=True, key="ddel"):
                    if img.get("id"): delete_from_supabase(img["id"])
                    st.session_state.images.pop(idx)
                    st.session_state.viewing_image = None
                    st.toast("Deleted", icon="🗑️"); st.rerun()
            st.divider()


# ---------------------------------------------------------------------------
# GALLERY
# ---------------------------------------------------------------------------
if not st.session_state.images and st.session_state.generating_count == 0:
    st.markdown("""
    <div class="empty-hero">
        <div class="emoji">🍌</div>
        <h1>Nano Banana Studio</h1>
        <p>Type a prompt below to start generating.<br>Upload references for context-aware creation.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    cols_per = 4
    all_items = st.session_state.images

    # Show generating placeholders first
    gen_count = st.session_state.generating_count
    if gen_count > 0:
        placeholder_html = ""
        for i in range(gen_count):
            placeholder_html += """
            <div class="gen-placeholder">
                <div class="spinner"></div>
                <div class="gen-text">Generating…</div>
            </div>
            """
        # Render placeholders in a grid row
        ph_cols = st.columns(cols_per, gap="small")
        for i in range(min(gen_count, cols_per)):
            with ph_cols[i]:
                st.markdown(f"""
                <div class="gen-placeholder">
                    <div class="spinner"></div>
                    <div class="gen-text">Generating…</div>
                </div>
                """, unsafe_allow_html=True)

    # Actual images
    rows = [all_items[i:i+cols_per] for i in range(0, len(all_items), cols_per)]
    for row in rows:
        cols = st.columns(cols_per, gap="small")
        for ci, img in enumerate(row):
            with cols[ci]:
                src = img_src(img)
                if not src: continue
                aidx = st.session_state.images.index(img)

                st.image(src, use_container_width=True)

                b1, b2, b3, b4 = st.columns(4, gap="small")
                with b1:
                    if st.button("👁", key=f"v{aidx}", use_container_width=True, help="View"):
                        st.session_state.viewing_image = aidx; st.rerun()
                with b2:
                    if img.get("b64"):
                        st.download_button("⬇", base64.b64decode(img["b64"]),
                            f"nb_{img.get('id','x')[:8]}.png", "image/png",
                            key=f"d{aidx}", use_container_width=True, help="Save")
                    elif img.get("url"):
                        st.link_button("⬇", img["url"], use_container_width=True)
                with b3:
                    if st.button("🔄", key=f"r{aidx}", use_container_width=True, help="Remix"):
                        st.session_state.remix_prompt = img.get("prompt", "")
                        st.session_state.remix_refs = get_refs(img)
                        st.toast("Loaded!", icon="🔄"); st.rerun()
                with b4:
                    if st.button("🗑", key=f"x{aidx}", use_container_width=True, help="Delete"):
                        if img.get("id"): delete_from_supabase(img["id"])
                        st.session_state.images.pop(aidx)
                        if st.session_state.viewing_image == aidx:
                            st.session_state.viewing_image = None
                        st.toast("Deleted", icon="🗑️"); st.rerun()

                p_short = img.get("prompt", "")[:50]
                if len(img.get("prompt", "")) > 50: p_short += "…"
                rc = len(get_refs(img))
                st.caption(f"{p_short}{'  · 📎' + str(rc) if rc else ''}")


# ---------------------------------------------------------------------------
# BOTTOM CONTROLS
# ---------------------------------------------------------------------------
st.markdown("")

with st.expander("📎 Reference Images (optional — up to 14)", expanded=False):
    uploaded_refs = st.file_uploader("refs", type=["png","jpg","jpeg","webp"],
        accept_multiple_files=True, key="ref_up", label_visibility="collapsed")
    if st.session_state.ref_from_gallery:
        ri = st.session_state.ref_from_gallery
        rs = img_src(ri)
        if rs:
            st.markdown("**Gallery reference:**")
            st.image(rs, width=100)
            if st.button("✕ Remove", key="rmgr"):
                st.session_state.ref_from_gallery = None; st.rerun()
    if st.session_state.remix_refs:
        st.markdown("**Remix references:**")
        rmc = st.columns(min(len(st.session_state.remix_refs), 5), gap="small")
        for ri2, rs2 in enumerate(st.session_state.remix_refs):
            rmc[ri2 % len(rmc)].image(ref_display(rs2), width=72)
        if st.button("✕ Clear remix refs", key="clrr"):
            st.session_state.remix_refs = None; st.rerun()
    if uploaded_refs:
        uc = st.columns(min(len(uploaded_refs), 7))
        for i, r in enumerate(uploaded_refs[:14]):
            uc[i % len(uc)].image(r, width=72)

# Prompt
default_p = st.session_state.remix_prompt or ""
p1, p2, p3, p4, p5 = st.columns([6, 1, 1, 1, 1])
with p1:
    prompt = st.text_input("Prompt", value=default_p,
        placeholder="Describe the scene you imagine…", key="pinp", label_visibility="collapsed")
with p2:
    ar = st.selectbox("AR", ASPECT_RATIOS, 0, key="arsel", label_visibility="collapsed")
with p3:
    res = st.selectbox("Res", RESOLUTIONS, 1, key="rsel", label_visibility="collapsed")
with p4:
    batch = st.selectbox("Batch", range(1, MAX_BATCH+1), 0, key="bsel",
        format_func=lambda x: f"{x}/{MAX_BATCH}", label_visibility="collapsed")
with p5:
    gen = st.button(f"Generate ⚡ {batch}", key="gbtn", type="primary", use_container_width=True)

if st.session_state.remix_prompt:
    st.session_state.remix_prompt = None

# Pills
pp = [f'<span class="bpill"><span class="dot"></span> <b>Nano Banana Pro</b></span>',
      f'<span class="bpill">📐 <b>{ar}</b></span>',
      f'<span class="bpill">🖥️ <b>{res}</b></span>',
      f'<span class="bpill">🔢 <b>{batch}/{MAX_BATCH}</b></span>']
tr = len(uploaded_refs or [])
if st.session_state.ref_from_gallery: tr += 1
if st.session_state.remix_refs: tr += len(st.session_state.remix_refs)
if tr: pp.append(f'<span class="bpill">📎 <b>{min(tr,14)} refs</b></span>')
st.markdown(f'<div class="bottom-pills">{"".join(pp)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# GENERATE
# ---------------------------------------------------------------------------
if gen:
    if not prompt.strip():
        st.toast("Enter a prompt!", icon="✏️")
    elif not GOOGLE_API_KEY:
        st.toast("API key not set! Add it to .env", icon="🔑")
    else:
        ref_bytes, ref_b64s = [], []
        if uploaded_refs:
            for r in uploaded_refs[:14]:
                raw = r.read(); ref_bytes.append(raw)
                ref_b64s.append(base64.b64encode(raw).decode("utf-8"))
        if st.session_state.ref_from_gallery:
            g = st.session_state.ref_from_gallery
            if g.get("b64"):
                raw = base64.b64decode(g["b64"]); ref_bytes.append(raw); ref_b64s.append(g["b64"])
        if st.session_state.remix_refs:
            for kind, val in st.session_state.remix_refs:
                if kind == "b64":
                    raw = base64.b64decode(val); ref_bytes.append(raw); ref_b64s.append(val)
        ref_bytes, ref_b64s = ref_bytes[:14], ref_b64s[:14]

        # Set generating state for placeholders
        st.session_state.generating_count = batch

        with st.spinner(f"🍌 Generating {batch} image{'s' if batch > 1 else ''}…"):
            results = generate_images(prompt, ref_bytes, ar, res, batch)

        st.session_state.generating_count = 0

        if results:
            for b64 in results:
                iid = save_to_supabase(b64, prompt, ar, res, ref_b64s)
                st.session_state.images.insert(0, {
                    "id": iid or str(uuid.uuid4()), "prompt": prompt,
                    "aspect_ratio": ar, "resolution": res,
                    "url": None, "b64": b64,
                    "created_at": datetime.now().isoformat(),
                    "ref_b64s": ref_b64s, "ref_urls": [],
                })
            st.session_state.remix_refs = None
            st.toast(f"✅ {len(results)} image{'s' if len(results)>1 else ''} done!", icon="🍌")
            st.rerun()
        else:
            st.toast("Generation failed — check API key", icon="❌")
