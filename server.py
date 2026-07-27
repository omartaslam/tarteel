"""Tarteel demo backend — XLSR pipeline + session storage for diagnostics."""
import os, tempfile, json
from fastapi import FastAPI, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from starlette.concurrency import run_in_threadpool
import analyze_xlsr as analyze, explanations as ex, storage

app = FastAPI(title="Tarteel demo")

@app.on_event("startup")
def warm():
    analyze._load()

def _diag_from_cards(cards):
    d = next((c for c in (cards or []) if c.get("audio_quality") is not None), {}) or {}
    return {
        "audio_quality": d.get("audio_quality"),
        "heard_arabic": d.get("heard_arabic", ""),
        "heard_phonetic": d.get("heard_phonetic", ""),
        "heard_raw": d.get("heard_raw", ""),
        "heard_match": d.get("heard_match", ""),
        "matched_arabic": d.get("matched_arabic", ""),
        "matched_phonetic": d.get("matched_phonetic", ""),
        "rms_level": d.get("rms_level"),
    }

@app.post("/analyze")
async def do_analyze(audio: UploadFile, verse: int = Form(...)):
    raw = await audio.read()
    # keep the real extension the browser/app sent (webm, m4a, wav, ogg...)
    ext = (audio.filename or "audio.webm").split(".")[-1].lower()
    if ext not in ("webm","m4a","wav","ogg","mp4","mp3"): ext="webm"
    with tempfile.NamedTemporaryFile(suffix="."+ext, delete=False) as tmp:
        tmp.write(raw); path = tmp.name
    try:
        # CPU-heavy — must not block the asyncio loop (mobile proxies drop hung connections)
        results = await run_in_threadpool(analyze.analyze_verse, path, verse)
    except Exception as e:
        return JSONResponse({"error": str(e), "results": [], "verse": verse}, status_code=500)
    finally:
        try: os.unlink(path)
        except Exception: pass
    cards = results or []
    sid = storage.save(raw, ext, verse, cards, extra={"filename":audio.filename,
                       "content_type":audio.content_type, "bytes":len(raw)})
    diag = _diag_from_cards(cards)
    return JSONResponse({"verse":verse, "results":cards, "session":sid, **diag})


@app.get("/sessions")
def sessions():
    # JSON list of all stored sessions + their computed data
    return JSONResponse(storage.list_sessions())

@app.get("/batch")
def batch():
    # compact one-per-session summary for quick review
    out=[]
    for s in storage.list_sessions():
        r=(s.get("results") or [{}])
        qc=next((c for c in r if c.get("rule")=="qalqalah"), {})
        diag=next((c for c in r if c.get("audio_quality")), {})
        out.append({
            "session":s.get("session"), "verse":s.get("verse"), "note":s.get("note",""),
            "quality":diag.get("audio_quality"), "rms":diag.get("rms_level"),
            "heard":diag.get("heard_arabic"), "heard_ph":diag.get("heard_phonetic"),
            "qalqalah":qc.get("verdict"), "p_error":qc.get("p_error"), "confidence":qc.get("confidence"),
            "cards":[c.get("plain") for c in r if c.get("plain")],
        })
    return JSONResponse(out)

@app.post("/note")
async def add_note(session: str = Form(...), note: str = Form(...)):
    import json as _j
    p=os.path.join(storage.STORE, session, "data.json")
    if os.path.exists(p):
        d=_j.load(open(p,encoding="utf-8")); d["note"]=note
        _j.dump(d, open(p,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
        return {"ok":True}
    return JSONResponse({"error":"not found"}, status_code=404)

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
