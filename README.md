# Generation Vault

> Never lose a ComfyUI generation again.  
> Your ComfyUI memory — search every generation you've ever made.

---

## Quick Start — 30 seconds

```
Download → Unzip → Double-click → Drag PNG → Found
```

**No Python. No pip. No terminal.**

[Download portable zip](https://github.com/biuta666/generation-vault/releases) (80 MB, includes everything) → unzip → double-click `start.bat` → browser opens → drop a ComfyUI PNG.

Or click **"Try Demo"** to see it work without any PNG.

---

## What it does

Drop a ComfyUI PNG → metadata appears instantly (prompt, model, LoRA, seed, sampler, steps) → stored in a local database. Search everything by keyword later.

**No cloud. No API. Everything stays on your machine.**

---

## How it works

```
Drop PNG → ComfyUIParser extracts metadata → SQLite (FTS5) → Search UI
```

- **Parser** reads the workflow JSON embedded in every ComfyUI PNG
- **Database** stores prompt, negative, model, LoRA, seed, CFG, sampler, steps
- **Search** by keyword (FTS5), model name, LoRA name, or seed
- **UI** is a local Streamlit app — drag, search, find

---

## Why this exists

If you use ComfyUI, you've had this moment:

- "Which LoRA did I use for that face?"
- "What seed gave me that perfect composition?"
- "I remember the prompt was about a sunset, but I can't find it."

Generation Vault is the answer. One drag. Found.

---

## Current

- ✅ ComfyUI PNG metadata parsing
- ✅ Local SQLite database (FTS5 full-text search)
- ✅ Search by prompt / model / LoRA / seed
- ✅ Clean Streamlit UI — Import, Search, Detail, Health

## Not included (yet)

- ❌ AI / cloud / login / accounts
- ❌ A1111 parser (planned)
- ❌ Video / Timeline

---

## Tech

Pure Python + Streamlit. Zero external AI dependencies. Zero API calls. Zero data leaves your computer.

`Pillow` reads the PNG chunks. `sqlite3` (built-in) stores everything. `streamlit` renders the UI.

---

## Early preview. Looking for feedback.

If you use ComfyUI daily, try it. Open an Issue if something breaks — or tell me what you'd want next.

**Try Demo:** Click the "Try Demo" button on first launch — no need to find a ComfyUI PNG.

**Price:** Free during preview. Future price: **$39 one-time** (no subscriptions, no cloud).

---

## License

MIT
