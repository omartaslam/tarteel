"""
Tarteel demo backend. One endpoint: POST /analyze  (wav + verse) -> verdicts.
Reuses tested pipeline. Frontend served from static/.
"""
import os, tempfile
from fastapi import FastAPI, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import analyze_xlsr as analyze, explanations as ex

app = FastAPI(title="Tarteel demo")

@app.on_event("startup")
def warm():
    # load the XLSR model + classifier once, so first request isn't slow
    analyze._load()

@app.post("/analyze")
async def do_analyze(audio: UploadFile, verse: int = Form(...)):
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await audio.read())
        path = tmp.name
    try:
        raw = analyze.analyze_verse(path, verse)
    finally:
        os.unlink(path)

    cards = []
    for r in raw:
        fb = ex.qalqalah_feedback(r.get("verse",verse), r["verdict"], r["confidence"])
        cards.append({**r, **fb})
    return JSONResponse({"verse": verse, "results": cards})

@app.get("/health")
def health():
    return {"ok": True}

# static frontend last so /analyze wins
app.mount("/", StaticFiles(directory="static", html=True), name="static")
