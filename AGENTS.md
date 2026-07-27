# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single Python FastAPI service — "Tarteel", a Quran recitation
(tajweed) analysis web app for Surah Al-Ikhlas. There is no database, no
separate frontend build, and no other services. Everything runs in one
`uvicorn` process that also serves the static frontend.

### Environment
- Python deps live in a local virtualenv at `.venv` (created by the startup
  update script). Always invoke tools via `.venv/bin/...` (e.g.
  `.venv/bin/uvicorn`, `.venv/bin/python`, `.venv/bin/pip`). The system Python is
  PEP 668 externally-managed, so do not `pip install` into it.
- `torch`/`torchaudio` are installed CPU-only from the PyTorch CPU wheel index
  (they are intentionally NOT in `requirements.txt`; see `Dockerfile`).
- `ffmpeg` (system binary) is required by the analysis pipeline and is already
  present on the VM.

### Running the app (dev)
- Start: `.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8000`
  (add `--reload` for hot-reload during development).
- The app serves the UI at `http://localhost:8000/` and the API under the same
  origin (`/analyze`, `/sessions`, `/batch`, `/note`, `/health`).

### Model (non-obvious)
- On startup `server.py:warm()` calls `analyze_xlsr._load()`, which downloads the
  `jonatasgrosman/wav2vec2-large-xlsr-53-arabic` model (~1 GB) from HuggingFace
  into `~/.cache/huggingface` on first use. This cache persists in the VM
  snapshot, so subsequent starts are fast. If the cache is cold, the first
  server start (or first `/analyze`) will block while downloading — allow extra
  time and ensure network access.
- The trained classifier `models/qalqalah_clf_xlsr.pkl` is committed to the repo
  and loaded at startup; it is not downloadable.

### Testing
- There is no automated test suite and no lint config in this repo.
- End-to-end smoke test of the core pipeline (no microphone needed): download a
  reference recitation and POST it to `/analyze`, e.g.
  `curl -s -o /tmp/v1.mp3 https://everyayah.com/data/Husary_128kbps/112001.mp3`
  then
  `curl -s -X POST http://localhost:8000/analyze -F "audio=@/tmp/v1.mp3" -F "verse=1"`.
  A healthy response returns per-element tajweed feedback cards and a `session`
  id. Valid `verse` values are 1-4 (Al-Ikhlas).
- The browser UI's "Record" button needs a real microphone (unavailable in the
  cloud VM), so exercise the analysis pipeline via the `/analyze` endpoint
  instead of recording in-browser.

### Notes
- Sessions are written to a local `sessions/` directory (not committed); it is
  created on first analysis and is fine to leave in place.
