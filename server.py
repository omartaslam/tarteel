"""Tarteel demo backend — XLSR pipeline + session storage for diagnostics."""
import os, tempfile, json
from fastapi import FastAPI, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import analyze_xlsr as analyze, explanations as ex, storage

app = FastAPI(title="Tarteel demo")

@app.on_event("startup")
def warm():
    analyze._load()

@app.post("/analyze")
async def do_analyze(audio: UploadFile, verse: int = Form(...)):
    raw = await audio.read()
    # keep the real extension the browser/app sent (webm, m4a, wav, ogg...)
    ext = (audio.filename or "audio.webm").split(".")[-1].lower()
    if ext not in ("webm","m4a","wav","ogg","mp4","mp3"): ext="webm"
    with tempfile.NamedTemporaryFile(suffix="."+ext, delete=False) as tmp:
        tmp.write(raw); path = tmp.name
    try:
        results = analyze.analyze_verse(path, verse)
    finally:
        os.unlink(path)
    cards = results  # analyze now returns full per-element feedback cards
    # store everything for diagnosis
    sid = storage.save(raw, ext, verse, cards, extra={"filename":audio.filename,
                       "content_type":audio.content_type, "bytes":len(raw)})
    return JSONResponse({"verse":verse, "results":cards, "session":sid})

@app.get("/sessions")
def sessions():
    # JSON list of all stored sessions + their computed data
    return JSONResponse(storage.list_sessions())

@app.get("/sessions/{sid}/audio")
def session_audio(sid: str):
    d = os.path.join(storage.STORE, sid)
    for f in os.listdir(d):
        if f.startswith("audio."):
            return FileResponse(os.path.join(d,f))
    return JSONResponse({"error":"not found"}, status_code=404)

@app.get("/health")
def health(): return {"ok": True}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
