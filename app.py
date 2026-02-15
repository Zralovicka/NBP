import streamlit as st
import base64
import io
import os
import json
import uuid
import hashlib
import requests as http_requests
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

st.set_page_config(page_title="Nano Banana Studio", page_icon="🍌", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', -apple-system, sans-serif !important; }

#MainMenu, footer, header, .stDeployButton,
div[data-testid="stToolbar"], div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"], div[data-testid="stHeader"] { display: none !important; }

.main .block-container { padding: 56px 24px 140px 24px !important; max-width: 100% !important; }

/* NAV */
.nav-bar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    height: 50px; background: #111;
    display: flex; align-items: center; justify-content: space-between; padding: 0 24px;
}
.nav-logo { font-size: 0.95rem; font-weight: 700; color: #C8FF00; display: flex; align-items: center; gap: 8px; }
.nav-right { display: flex; align-items: center; gap: 10px; }
.nav-chip {
    background: rgba(255,255,255,0.1); border-radius: 100px; padding: 4px 14px;
    font-size: 0.7rem; color: rgba(255,255,255,0.6); font-weight: 500;
    display: flex; align-items: center; gap: 6px;
}
.nav-chip .dot { width: 6px; height: 6px; border-radius: 50%; background: #C8FF00; }

/* PLACEHOLDER CARD */
.gen-card {
    background: #18181b; border: 1px solid #2a2a2e; border-radius: 12px;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    gap: 14px; padding: 80px 20px;
    animation: gen-pulse 2s ease-in-out infinite;
}
@keyframes gen-pulse { 0%,100%{background:#18181b} 50%{background:#1e1e24} }
.gen-card .spinner {
    width: 28px; height: 28px;
    border: 3px solid #333; border-top: 3px solid #C8FF00;
    border-radius: 50%; animation: spin 0.8s linear infinite;
}
@keyframes spin { to{transform:rotate(360deg)} }
.gen-card .gen-text { font-size: 0.72rem; color: #555; font-weight: 500; }

/* EMPTY */
.empty-hero { text-align: center; padding: 80px 20px 60px; }
.empty-hero .emoji { font-size: 3.5rem; margin-bottom: 12px; }
.empty-hero h1 { font-size: 1.6rem; font-weight: 800; color: #ccc; margin: 0 0 8px 0; }
.empty-hero p { font-size: 0.88rem; color: #aaa; max-width: 380px; margin: 0 auto; line-height: 1.5; }

/* DETAIL */
.detail-label { font-size: 0.65rem; color: #999; font-weight: 700; letter-spacing: 1px; text-transform: uppercase; margin: 18px 0 8px 0; }
.detail-prompt-box { background: #f7f7f8; border: 1px solid #e8e8ea; border-radius: 10px; padding: 14px 16px; font-size: 0.86rem; color: #333; line-height: 1.6; }
.detail-row { display: flex; justify-content: space-between; padding: 9px 0; border-bottom: 1px solid #f0f0f2; font-size: 0.82rem; }
.detail-row-k { color: #999; }
.detail-row-v { color: #333; font-weight: 600; }

/* PILLS */
.bottom-pills { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 6px; }
.bpill { background: #f3f3f5; border: 1px solid #e5e5e8; border-radius: 100px; padding: 4px 13px; font-size: 0.68rem; color: #888; font-weight: 500; display: inline-flex; align-items: center; gap: 5px; }
.bpill b { color: #444; }
.bpill .dot { width: 5px; height: 5px; border-radius: 50%; background: #a0c800; }

/* PRIMARY BTN */
.stButton > button[data-testid="stBaseButton-primary"] {
    background: #111 !important; border: none !important; color: #C8FF00 !important;
    font-weight: 700 !important; border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important; font-size: 0.85rem !important; padding: 8px 20px !important;
}
.stButton > button[data-testid="stBaseButton-primary"]:hover { background: #222 !important; }

/* REF THUMBS */
.ref-grid {
    display: flex; gap: 8px; flex-wrap: wrap; align-items: flex-start;
    padding: 8px 0;
}
.ref-thumb-wrap {
    position: relative; width: 80px;
}
.ref-thumb-wrap img {
    width: 80px; height: 80px; object-fit: cover; border-radius: 8px;
    border: 1px solid #e0e0e2;
}
.ref-source-tag {
    font-size: 0.6rem; color: #888; text-align: center; margin-top: 2px;
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

def do_login(pw):
    if pw == APP_PASSWORD:
        st.session_state.authenticated = True
        st.query_params["auth"] = AUTH_TOKEN
        return True
    return False

if not check_auth():
    st.markdown("""
    <div style="display:flex;justify-content:center;align-items:center;
                min-height:80vh;flex-direction:column;gap:14px;">
        <div style="font-size:3.5rem;">🍌</div>
        <div style="font-size:1.3rem;font-weight:800;color:#333;">Nano Banana Studio</div>
        <div style="color:#999;font-size:0.82rem;">Enter password to continue</div>
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
# Session
# ---------------------------------------------------------------------------
defaults = {
    "images": [], "supabase_client": None, "loaded_from_db": False,
    "viewing_image": None, "viewing_ref": None, "ref_from_gallery": None,
    "remix_prompt": None, "remix_refs": None,
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
        st.session_state.supabase_client = c; return c
    except Exception as e:
        st.toast(f"⚠️ Supabase: {e}", icon="⚠️"); return None

def save_to_supabase(image_b64, prompt, aspect, resolution, ref_b64_list=None):
    sb = get_supabase()
    if not sb: return None
    try:
        img_id = str(uuid.uuid4())
        sb.storage.from_("generated-images").upload(f"{img_id}.png", base64.b64decode(image_b64), {"content-type": "image/png"})
        public_url = sb.storage.from_("generated-images").get_public_url(f"{img_id}.png")
        ref_urls = []
        if ref_b64_list:
            for ri, rb in enumerate(ref_b64_list):
                rp = f"refs/{img_id}_ref{ri}.png"
                sb.storage.from_("generated-images").upload(rp, base64.b64decode(rb) if isinstance(rb, str) else rb, {"content-type": "image/png"})
                ref_urls.append(sb.storage.from_("generated-images").get_public_url(rp))
        sb.table("generated_images").insert({
            "id": img_id, "prompt": prompt, "aspect_ratio": aspect, "resolution": resolution,
            "image_url": public_url,
            "metadata": json.dumps({"model": MODEL_NAME, "timestamp": datetime.now().isoformat(), "ref_urls": ref_urls}),
        }).execute()
        return img_id
    except Exception as e:
        st.toast(f"⚠️ Save: {e}", icon="⚠️"); return None

def load_from_supabase():
    sb = get_supabase()
    if not sb: return []
    try:
        return (sb.table("generated_images").select("*").order("created_at", desc=True).limit(200).execute()).data or []
    except: return []

def delete_from_supabase(img_id):
    sb = get_supabase()
    if not sb: return
    try:
        sb.storage.from_("generated-images").remove([f"{img_id}.png"])
        sb.table("generated_images").delete().eq("id", img_id).execute()
    except Exception as e:
        st.toast(f"⚠️ Delete: {e}", icon="⚠️")

if not st.session_state.loaded_from_db:
    for row in load_from_supabase():
        meta = {}
        try: meta = json.loads(row.get("metadata", "{}"))
        except: pass
        st.session_state.images.append({
            "id": row.get("id", str(uuid.uuid4())), "prompt": row.get("prompt", ""),
            "aspect_ratio": row.get("aspect_ratio", "1:1"), "resolution": row.get("resolution", "2K"),
            "url": row.get("image_url", ""), "b64": None, "created_at": row.get("created_at", ""),
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
    a = None if aspect == "Auto" else aspect
    cfg = {"image_size": resolution}
    if a: cfg["aspect_ratio"] = a
    config = types.GenerateContentConfig(
        response_modalities=["TEXT", "IMAGE"], image_config=types.ImageConfig(**cfg))
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
    return [("b64", r) for r in img.get("ref_b64s", [])] + [("url", r) for r in img.get("ref_urls", [])]

def ref_display(r):
    return f"data:image/png;base64,{r[1]}" if r[0] == "b64" else r[1]

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_image_bytes(url):
    try:
        resp = http_requests.get(url, timeout=15)
        if resp.status_code == 200: return resp.content
    except: pass
    return None

def get_download_bytes(img):
    if img.get("b64"): return base64.b64decode(img["b64"])
    if img.get("url"): return fetch_image_bytes(img["url"])
    return None


# ---------------------------------------------------------------------------
# NAV
# ---------------------------------------------------------------------------
n = len(st.session_state.images)
st.markdown(f"""
<div class="nav-bar">
    <div class="nav-logo">🍌 Nano Banana Studio</div>
    <div class="nav-right">
        <div class="nav-chip"><span class="dot"></span> Nano Banana Pro</div>
        <div class="nav-chip">{n} image{"s" if n != 1 else ""}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DETAIL / REF VIEW
# ---------------------------------------------------------------------------
if st.session_state.viewing_ref is not None:
    st.subheader("🖼 Reference Image")
    st.image(st.session_state.viewing_ref, use_container_width=False, width=600)
    if st.button("← Back", key="bkr"):
        st.session_state.viewing_ref = None; st.rerun()
    st.divider()

elif st.session_state.viewing_image is not None:
    idx = st.session_state.viewing_image
    if idx < len(st.session_state.images):
        img = st.session_state.images[idx]
        src = img_src(img)
        if src:
            ci, cs = st.columns([3, 1], gap="medium")
            with ci: st.image(src, use_container_width=True)
            with cs:
                if st.button("✕  Close", key="cls", use_container_width=True):
                    st.session_state.viewing_image = None; st.rerun()

                st.markdown('<div class="detail-label">✦ PROMPT</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="detail-prompt-box">{img.get("prompt","—")}</div>', unsafe_allow_html=True)

                if st.button("🔄  Remix", key="rmx", use_container_width=True, type="primary"):
                    st.session_state.remix_prompt = img.get("prompt", "")
                    st.session_state.remix_refs = get_refs(img)
                    st.session_state.viewing_image = None
                    st.toast("Loaded!", icon="🔄"); st.rerun()

                st.markdown('<div class="detail-label">ⓘ INFORMATION</div>', unsafe_allow_html=True)
                cr = str(img.get("created_at", ""))[:16].replace("T", " ")
                for k, v in [("Model", "Nano Banana Pro"), ("Quality", img.get("resolution", "2K")),
                             ("Aspect", img.get("aspect_ratio", "Auto")), ("Created", cr)]:
                    st.markdown(f'<div class="detail-row"><span class="detail-row-k">{k}</span><span class="detail-row-v">{v}</span></div>', unsafe_allow_html=True)

                refs = get_refs(img)
                if refs:
                    st.markdown('<div class="detail-label">🖼 REFERENCES</div>', unsafe_allow_html=True)
                    rc = st.columns(min(len(refs), 4), gap="small")
                    for ri, r in enumerate(refs):
                        with rc[ri % len(rc)]:
                            st.image(ref_display(r), width=72)
                            if st.button("Open", key=f"or{ri}", use_container_width=True):
                                st.session_state.viewing_ref = ref_display(r); st.rerun()

                st.markdown('<div class="detail-label">⚡ ACTIONS</div>', unsafe_allow_html=True)
                dl_bytes = get_download_bytes(img)
                if dl_bytes:
                    st.download_button("⬇  Download", dl_bytes,
                        f"nb_{img.get('id','x')[:8]}.png", "image/png",
                        use_container_width=True, key="ddl")
                if st.button("🖼  Use as Reference", use_container_width=True, key="drf"):
                    st.session_state.ref_from_gallery = img; st.session_state.viewing_image = None
                    st.toast("Set as ref!", icon="🖼️"); st.rerun()
                if st.button("🗑  Delete", use_container_width=True, key="ddl2"):
                    if img.get("id"): delete_from_supabase(img["id"])
                    st.session_state.images.pop(idx); st.session_state.viewing_image = None
                    st.toast("Deleted", icon="🗑️"); st.rerun()
            st.divider()


# ---------------------------------------------------------------------------
# GALLERY — with placeholder slots at top for generation
# ---------------------------------------------------------------------------

# Reserve placeholder containers BEFORE the gallery renders
# These st.empty() slots will be filled with placeholder cards during generation
placeholder_slots = []
C = 4

# Create a row of empty containers at the very top of the gallery area
placeholder_row = st.columns(C, gap="small")
placeholder_empties = []
for i in range(C):
    with placeholder_row[i]:
        placeholder_empties.append(st.empty())

if not st.session_state.images:
    st.markdown("""
    <div class="empty-hero">
        <div class="emoji">🍌</div>
        <h1>Nano Banana Studio</h1>
        <p>Type a prompt below to start generating.<br>Upload references for context-aware creation.</p>
    </div>
    """, unsafe_allow_html=True)
else:
    for row in [st.session_state.images[i:i+C] for i in range(0, len(st.session_state.images), C)]:
        cols = st.columns(C, gap="small")
        for ci, img in enumerate(row):
            with cols[ci]:
                src = img_src(img)
                if not src: continue
                ai = st.session_state.images.index(img)
                st.image(src, use_container_width=True)
                b1, b2, b3, b4 = st.columns(4, gap="small")
                with b1:
                    if st.button("👁", key=f"v{ai}", use_container_width=True, help="View"):
                        st.session_state.viewing_image = ai; st.rerun()
                with b2:
                    dl = get_download_bytes(img)
                    if dl:
                        st.download_button("⬇", dl, f"nb_{img.get('id','x')[:8]}.png",
                            "image/png", key=f"d{ai}", use_container_width=True)
                    else:
                        st.button("⬇", key=f"d{ai}", use_container_width=True, disabled=True)
                with b3:
                    if st.button("🔄", key=f"r{ai}", use_container_width=True, help="Remix"):
                        st.session_state.remix_prompt = img.get("prompt", "")
                        st.session_state.remix_refs = get_refs(img)
                        st.toast("Loaded!", icon="🔄"); st.rerun()
                with b4:
                    if st.button("🗑", key=f"x{ai}", use_container_width=True, help="Delete"):
                        if img.get("id"): delete_from_supabase(img["id"])
                        st.session_state.images.pop(ai)
                        if st.session_state.viewing_image == ai: st.session_state.viewing_image = None
                        st.toast("Deleted", icon="🗑️"); st.rerun()
                ps = img.get("prompt", "")[:50]
                if len(img.get("prompt", "")) > 50: ps += "…"
                rc = len(get_refs(img))
                st.caption(f"{ps}{'  · 📎'+str(rc) if rc else ''}")


# ---------------------------------------------------------------------------
# REFERENCE IMAGES — unified view
# ---------------------------------------------------------------------------
st.markdown("")

# Collect all reference sources for display
all_ref_items = []  # list of (source_label, display_src)

if st.session_state.ref_from_gallery:
    s = img_src(st.session_state.ref_from_gallery)
    if s: all_ref_items.append(("Gallery", s))

if st.session_state.remix_refs:
    for r in st.session_state.remix_refs:
        all_ref_items.append(("Remix", ref_display(r)))

has_extra_refs = len(all_ref_items) > 0

with st.expander(f"📎 Reference Images — {len(all_ref_items)} loaded" if has_extra_refs else "📎 Reference Images (optional — up to 14)", expanded=has_extra_refs):
    uploaded_refs = st.file_uploader("Upload reference images", type=["png","jpg","jpeg","webp"],
        accept_multiple_files=True, key="rup", label_visibility="collapsed")

    # Show all refs in one unified thumbnail grid
    if all_ref_items or uploaded_refs:
        st.markdown("**All references that will be sent:**")

        # Build a combined list for display
        display_items = list(all_ref_items)
        if uploaded_refs:
            for f in uploaded_refs[:14]:
                display_items.append(("Upload", f))

        # Show as a grid
        grid_cols = st.columns(min(len(display_items), 7), gap="small")
        for i, (label, src) in enumerate(display_items):
            with grid_cols[i % len(grid_cols)]:
                st.image(src, width=80, use_container_width=False)
                st.caption(label)

        if len(display_items) > 14:
            st.warning("Max 14 references. Only first 14 will be used.")

        # Clear buttons
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.session_state.ref_from_gallery:
                if st.button("✕ Clear gallery ref", key="rmg", use_container_width=True):
                    st.session_state.ref_from_gallery = None; st.rerun()
        with c2:
            if st.session_state.remix_refs:
                if st.button("✕ Clear remix refs", key="clr", use_container_width=True):
                    st.session_state.remix_refs = None; st.rerun()


# ---------------------------------------------------------------------------
# PROMPT ROW
# ---------------------------------------------------------------------------
dp = st.session_state.remix_prompt or ""
p1, p2, p3, p4, p5 = st.columns([6, 1, 1, 1, 1])
with p1: prompt = st.text_input("P", value=dp, placeholder="Describe the scene you imagine…", key="pi", label_visibility="collapsed")
with p2: ar = st.selectbox("AR", ASPECT_RATIOS, 0, key="ars", label_visibility="collapsed")
with p3: res = st.selectbox("Res", RESOLUTIONS, 1, key="rss", label_visibility="collapsed")
with p4: batch = st.selectbox("B", range(1, MAX_BATCH+1), 0, key="bss", format_func=lambda x: f"{x}/{MAX_BATCH}", label_visibility="collapsed")
with p5: gen = st.button(f"Generate ⚡ {batch}", key="gb", type="primary", use_container_width=True)

if st.session_state.remix_prompt: st.session_state.remix_prompt = None

pp = [f'<span class="bpill"><span class="dot"></span> <b>Nano Banana Pro</b></span>',
      f'<span class="bpill">📐 <b>{ar}</b></span>', f'<span class="bpill">🖥️ <b>{res}</b></span>',
      f'<span class="bpill">🔢 <b>{batch}/{MAX_BATCH}</b></span>']
tr = len(uploaded_refs or [])
if st.session_state.ref_from_gallery: tr += 1
if st.session_state.remix_refs: tr += len(st.session_state.remix_refs)
if tr: pp.append(f'<span class="bpill">📎 <b>{min(tr,14)} refs</b></span>')
st.markdown(f'<div class="bottom-pills">{"".join(pp)}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# GENERATE — uses placeholder_empties for live feedback
# ---------------------------------------------------------------------------
if gen:
    if not prompt.strip(): st.toast("Enter a prompt!", icon="✏️")
    elif not GOOGLE_API_KEY: st.toast("API key not set!", icon="🔑")
    else:
        rb, r64 = [], []
        if uploaded_refs:
            for r in uploaded_refs[:14]:
                raw = r.read(); rb.append(raw); r64.append(base64.b64encode(raw).decode("utf-8"))
        if st.session_state.ref_from_gallery:
            g = st.session_state.ref_from_gallery
            if g.get("b64"):
                rb.append(base64.b64decode(g["b64"])); r64.append(g["b64"])
            elif g.get("url"):
                d = fetch_image_bytes(g["url"])
                if d: rb.append(d); r64.append(base64.b64encode(d).decode("utf-8"))
        if st.session_state.remix_refs:
            for kind, val in st.session_state.remix_refs:
                if kind == "b64":
                    rb.append(base64.b64decode(val)); r64.append(val)
                elif kind == "url":
                    d = fetch_image_bytes(val)
                    if d: rb.append(d); r64.append(base64.b64encode(d).decode("utf-8"))
        rb, r64 = rb[:14], r64[:14]

        # Show dark placeholder cards in the reserved slots
        for i in range(min(batch, C)):
            placeholder_empties[i].markdown(
                '<div class="gen-card"><div class="spinner"></div>'
                f'<div class="gen-text">Generating {i+1}/{batch}…</div></div>',
                unsafe_allow_html=True,
            )

        # Run generation
        results = generate_images(prompt, rb, ar, res, batch)

        # Clear placeholders
        for i in range(C):
            placeholder_empties[i].empty()

        if results:
            for b64 in results:
                iid = save_to_supabase(b64, prompt, ar, res, r64)
                st.session_state.images.insert(0, {
                    "id": iid or str(uuid.uuid4()), "prompt": prompt,
                    "aspect_ratio": ar, "resolution": res,
                    "url": None, "b64": b64, "created_at": datetime.now().isoformat(),
                    "ref_b64s": r64, "ref_urls": [],
                })
            st.session_state.remix_refs = None
            st.toast(f"✅ {len(results)} image{'s' if len(results)>1 else ''} done!", icon="🍌"); st.rerun()
        else:
            st.toast("Failed — check API key", icon="❌")
