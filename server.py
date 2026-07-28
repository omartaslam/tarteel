"""Tarteel demo backend — XLSR pipeline + session storage for diagnostics."""
import os, tempfile, time, uuid, threading, json
from fastapi import FastAPI, UploadFile, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.concurrency import run_in_threadpool
import analyze_xlsr as analyze, storage

app = FastAPI(title="Tarteel demo")

# In-memory job progress (fine for single Railway instance)
_JOBS = {}
_JOBS_LOCK = threading.Lock()


@app.on_event("startup")
def warm():
    analyze._load()


def _parse_mastered(raw) -> list:
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw if x]
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x) for x in data if x]
    except Exception:
        pass
    return []


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
        "compare_html": d.get("compare_html", ""),
        "rms_level": d.get("rms_level"),
    }


def _set_job(jid, **kw):
    with _JOBS_LOCK:
        job = _JOBS.get(jid) or {}
        job.update(kw)
        _JOBS[jid] = job


def _run_job(jid, path, ext, raw, verse, filename, content_type, mastered=None, last_focus=None, stage_id=None):
    t0 = time.time()

    def cancelled():
        with _JOBS_LOCK:
            return bool((_JOBS.get(jid) or {}).get("cancel"))

    def on_progress(pct, phase, msg):
        if cancelled():
            raise analyze.AnalysisCancelled()
        _set_job(
            jid,
            status="running",
            pct=int(pct),
            phase=phase,
            message=msg,
            elapsed=round(time.time() - t0, 1),
        )

    try:
        on_progress(2, "start", "Starting analysis…")
        cards = analyze.analyze_verse(
            path, verse,
            on_progress=on_progress,
            mastered=mastered or [],
            last_focus=last_focus or None,
            cancel_check=cancelled,
            stage_id=stage_id,
        ) or []
        if cancelled():
            _set_job(
                jid,
                status="cancelled",
                pct=0,
                phase="cancelled",
                message="Cancelled — new recording started",
                elapsed=round(time.time() - t0, 1),
            )
            return
        sid = storage.save(
            raw, ext, verse, cards,
            extra={
                "filename": filename,
                "content_type": content_type,
                "bytes": len(raw),
                "job": jid,
                "mastered": mastered or [],
                "last_focus": last_focus,
                "stage_id": stage_id,
            },
        )
        diag = _diag_from_cards(cards)
        _set_job(
            jid,
            status="done",
            pct=100,
            phase="done",
            message="Done",
            elapsed=round(time.time() - t0, 1),
            result={"verse": verse, "results": cards, "session": sid, "stage_id": stage_id, **diag},
        )
    except analyze.AnalysisCancelled:
        _set_job(
            jid,
            status="cancelled",
            pct=0,
            phase="cancelled",
            message="Cancelled — new recording started",
            elapsed=round(time.time() - t0, 1),
        )
    except Exception as e:
        if cancelled():
            _set_job(
                jid,
                status="cancelled",
                pct=0,
                phase="cancelled",
                message="Cancelled — new recording started",
                elapsed=round(time.time() - t0, 1),
            )
        else:
            _set_job(
                jid,
                status="error",
                pct=100,
                phase="error",
                message=str(e),
                elapsed=round(time.time() - t0, 1),
                error=str(e),
            )
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


@app.post("/analyze/start")
async def analyze_start(
    audio: UploadFile,
    verse: int = Form(...),
    mastered: str = Form(""),
    last_focus: str = Form(""),
    stage_id: str = Form(""),
):
    raw = await audio.read()
    ext = (audio.filename or "audio.webm").split(".")[-1].lower()
    if ext not in ("webm", "m4a", "wav", "ogg", "mp4", "mp3"):
        ext = "webm"
    with tempfile.NamedTemporaryFile(suffix="." + ext, delete=False) as tmp:
        tmp.write(raw)
        path = tmp.name
    jid = uuid.uuid4().hex[:12]
    mastered_list = _parse_mastered(mastered)
    focus = (last_focus or "").strip() or None
    stage = (stage_id or "").strip() or None
    _set_job(
        jid,
        status="queued",
        pct=0,
        phase="queued",
        message="Queued…",
        elapsed=0,
        verse=verse,
        started=time.time(),
    )
    threading.Thread(
        target=_run_job,
        args=(
            jid, path, ext, raw, verse, audio.filename, audio.content_type,
            mastered_list, focus, stage,
        ),
        daemon=True,
    ).start()
    return {"job": jid}


@app.get("/analyze/status/{jid}")
def analyze_status(jid: str):
    with _JOBS_LOCK:
        job = _JOBS.get(jid)
    if not job:
        return JSONResponse({"error": "job not found"}, status_code=404)
    out = {
        "job": jid,
        "status": job.get("status"),
        "pct": job.get("pct", 0),
        "phase": job.get("phase"),
        "message": job.get("message"),
        "elapsed": job.get("elapsed", 0),
    }
    if job.get("status") == "done":
        out["result"] = job.get("result")
    if job.get("status") == "error":
        out["error"] = job.get("error") or job.get("message")
    return JSONResponse(out)


@app.post("/analyze/cancel/{jid}")
def analyze_cancel(jid: str):
    """Stop an in-flight analysis when the user starts a new recording."""
    with _JOBS_LOCK:
        job = _JOBS.get(jid)
        if not job:
            return JSONResponse({"ok": False, "error": "job not found"}, status_code=404)
        if job.get("status") in ("done", "error", "cancelled"):
            return {"ok": True, "status": job.get("status")}
        job["cancel"] = True
        job["status"] = "cancelling"
        job["message"] = "Cancelling…"
        _JOBS[jid] = job
    return {"ok": True, "status": "cancelling"}


@app.post("/analyze")
async def do_analyze(
    audio: UploadFile,
    verse: int = Form(...),
    mastered: str = Form(""),
    last_focus: str = Form(""),
    stage_id: str = Form(""),
):
    """Legacy one-shot analyze (still used as fallback)."""
    raw = await audio.read()
    ext = (audio.filename or "audio.webm").split(".")[-1].lower()
    if ext not in ("webm", "m4a", "wav", "ogg", "mp4", "mp3"):
        ext = "webm"
    mastered_list = _parse_mastered(mastered)
    focus = (last_focus or "").strip() or None
    stage = (stage_id or "").strip() or None
    with tempfile.NamedTemporaryFile(suffix="." + ext, delete=False) as tmp:
        tmp.write(raw)
        path = tmp.name
    try:
        results = await run_in_threadpool(
            analyze.analyze_verse,
            path, verse, None, mastered_list, focus, None, stage,
        )
    except Exception as e:
        return JSONResponse({"error": str(e), "results": [], "verse": verse}, status_code=500)
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass
    cards = results or []
    sid = storage.save(
        raw, ext, verse, cards,
        extra={
            "filename": audio.filename,
            "content_type": audio.content_type,
            "bytes": len(raw),
            "mastered": mastered_list,
            "last_focus": focus,
            "stage_id": stage,
        },
    )
    diag = _diag_from_cards(cards)
    return JSONResponse({"verse": verse, "results": cards, "session": sid, "stage_id": stage, **diag})


@app.get("/sessions")
def sessions():
    return JSONResponse(storage.list_sessions())


@app.get("/batch")
def batch():
    out = []
    for s in storage.list_sessions():
        r = s.get("results") or [{}]
        qc = next((c for c in r if c.get("rule") == "qalqalah"), {})
        diag = next((c for c in r if c.get("audio_quality")), {})
        out.append({
            "session": s.get("session"), "verse": s.get("verse"), "note": s.get("note", ""),
            "quality": diag.get("audio_quality"), "rms": diag.get("rms_level"),
            "heard": diag.get("heard_arabic"), "heard_ph": diag.get("heard_phonetic"),
            "qalqalah": qc.get("verdict"), "p_error": qc.get("p_error"), "confidence": qc.get("confidence"),
            "cards": [c.get("plain") for c in r if c.get("plain")],
        })
    return JSONResponse(out)


@app.post("/note")
async def add_note(session: str = Form(...), note: str = Form(...)):
    p = os.path.join(storage.STORE, session, "data.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["note"] = note
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        return {"ok": True}
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/sessions/{sid}/audio")
def session_audio(sid: str):
    d = os.path.join(storage.STORE, sid)
    for f in os.listdir(d):
        if f.startswith("audio."):
            return FileResponse(os.path.join(d, f))
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/health")
def health():
    build = (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("RAILWAY_GIT_COMMIT")
        or os.environ.get("GIT_COMMIT")
        or "dev"
    )
    return {"ok": True, "build": build[:12]}


@app.get("/stages/{verse}")
def stages_for_verse(verse: int):
    import stages as stg
    return JSONResponse(stg.stage_public(verse, None))


app.mount("/", StaticFiles(directory="static", html=True), name="static")
