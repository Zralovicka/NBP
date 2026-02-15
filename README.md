# 🍌 Nano Banana Studio

A personal AI image generation tool powered by Google's **Nano Banana Pro** (Gemini 3 Pro Image Preview), with a UI inspired by Higgsfield.

![Nano Banana Pro](https://img.shields.io/badge/Model-Nano_Banana_Pro-C8FF00)
![Streamlit](https://img.shields.io/badge/Framework-Streamlit-FF4B4B)
![Supabase](https://img.shields.io/badge/Storage-Supabase-3ECF8E)

---

## Features

- **Higgsfield-inspired dark UI** — clean image grid, bottom prompt bar, pill controls
- **Nano Banana Pro** — Google's most advanced image generation model
- **Multi-image upload** — up to 14 reference images for context-aware generation
- **Aspect ratio control** — Auto, 1:1, 2:3, 3:2, 3:4, 4:3, 4:5, 5:4, 9:16, 16:9, 21:9
- **Resolution control** — 1K, 2K, 4K
- **Batch generation** — generate 1-4 images per prompt
- **Persistent storage** — all images saved to Supabase
- **Image management** — delete images from sidebar

---

## Quick Setup (5 minutes)

### 1. Install dependencies

```bash
cd nanobanana
pip install -r requirements.txt
```

### 2. Set up Supabase

1. Go to [supabase.com](https://supabase.com) → open your project
2. Click **SQL Editor** → **New Query**
3. Paste the contents of `setup_supabase.sql` and click **Run**
4. Go to **Settings** → **API** and copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon public key** (the `eyJ...` string)

### 3. Configure environment

Edit the `.env` file:

```env
GOOGLE_API_KEY=
SUPABASE_URL=
SUPABASE_KEY=
```

### 4. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`

---

## Usage

1. **Type a prompt** in the bottom input bar
2. **Upload reference images** (optional) — click the 📎 expander
3. **Choose settings** — aspect ratio, resolution, batch size
4. **Click Generate** — images appear in the grid
5. **Manage images** — open sidebar (☰) to delete individual images

---

## File Structure

```
nanobanana/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── setup_supabase.sql      # Database & storage setup script
├── .env                    # API keys (edit this!)
├── .streamlit/
│   └── config.toml         # Dark theme & Streamlit config
└── README.md               # This file
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `google.genai` not found | Run `pip install google-genai` |
| Images not saving | Check Supabase URL/key in `.env` |
| "API key not configured" | Add your Google API key to `.env` |
| Generation fails | Check API quota at [console.cloud.google.com](https://console.cloud.google.com) |
| 4K images fail | Some aspect ratios may not support 4K — try 2K |

---

## V2 Ideas

- [ ] Image editing / inpainting via chat
- [ ] Prompt history & favorites
- [ ] Image download button on hover
- [ ] Folder/collection organization
- [ ] Search through generated images
- [ ] Prompt templates library
- [ ] Google Search grounding toggle
- [ ] Cost tracking per generation
