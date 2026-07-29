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
        # Measured sound, with no vocabulary to guess from.
        "sound_letters": d.get("sound_letters", ""),
        "sound_evidence": d.get("sound_evidence", {}),
        # Acoustic snapshot for device voice calibration after self-label.
        "voice_sample": d.get("voice_sample"),
    }


def _set_job(jid, **kw):
    with _JOBS_LOCK:
        job = _JOBS.get(jid) or {}
        job.update(kw)
        _JOBS[jid] = job


def _parse_voice_profile(raw) -> dict | None:
    """Optional JSON voice profile from this device. Never raise."""
    import voice_profile as vp

    if not raw:
        return None
    if isinstance(raw, dict):
        return vp.parse_profile(raw)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return vp.parse_profile(data)
    except Exception:
        pass
    return None


def _run_job(jid, path, ext, raw, verse, filename, content_type, mastered=None, last_focus=None, stage_id=None, locked_stages=None, qu_bridge_attempt=None, voice_profile=None):
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
            locked_stages=locked_stages or [],
            qu_bridge_attempt=qu_bridge_attempt,
            voice_profile=voice_profile,
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
                "qu_bridge_attempt": qu_bridge_attempt,
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
    locked_stages: str = Form(""),
    qu_bridge_attempt: str = Form(""),
    voice_profile: str = Form(""),
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
    locked_list = _parse_mastered(locked_stages)
    focus = (last_focus or "").strip() or None
    stage = (stage_id or "").strip() or None
    voice = _parse_voice_profile(voice_profile)
    bridge_n = None
    try:
        if (qu_bridge_attempt or "").strip():
            bridge_n = int(str(qu_bridge_attempt).strip())
    except ValueError:
        bridge_n = None
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
            mastered_list, focus, stage, locked_list, bridge_n, voice,
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
    locked_stages: str = Form(""),
    qu_bridge_attempt: str = Form(""),
    voice_profile: str = Form(""),
):
    """Legacy one-shot analyze (still used as fallback)."""
    raw = await audio.read()
    ext = (audio.filename or "audio.webm").split(".")[-1].lower()
    if ext not in ("webm", "m4a", "wav", "ogg", "mp4", "mp3"):
        ext = "webm"
    mastered_list = _parse_mastered(mastered)
    locked_list = _parse_mastered(locked_stages)
    focus = (last_focus or "").strip() or None
    stage = (stage_id or "").strip() or None
    voice = _parse_voice_profile(voice_profile)
    bridge_n = None
    try:
        if (qu_bridge_attempt or "").strip():
            bridge_n = int(str(qu_bridge_attempt).strip())
    except ValueError:
        bridge_n = None
    with tempfile.NamedTemporaryFile(suffix="." + ext, delete=False) as tmp:
        tmp.write(raw)
        path = tmp.name
    try:
        results = await run_in_threadpool(
            analyze.analyze_verse,
            path, verse, None, mastered_list, focus, None, stage, locked_list, bridge_n, voice,
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
            "qu_bridge_attempt": bridge_n,
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


@app.post("/label")
async def add_label(
    session: str = Form(...),
    label: str = Form(...),
    stage_id: str = Form(""),
    voice_sample: str = Form(""),
    voice_profile: str = Form(""),
):
    """The learner's own verdict, captured BEFORE ours is revealed.

    Order matters: a label collected after the app has said "wrong" is anchored
    to the app's opinion and is worthless as ground truth. This is the only
    record of what the learner intended, and the whole accuracy protocol
    depends on it.

    When voice_sample + voice_profile are sent, fold the label into this
    device's speaker-relative acoustic baseline and return the updated profile.
    """
    import voice_profile as vp

    label = (label or "").strip().lower()
    if label not in ("correct", "think_correct", "think_wrong", "wrong", "unsure"):
        return JSONResponse({"error": "bad label"}, status_code=400)
    p = os.path.join(storage.STORE, session, "data.json")
    if not os.path.exists(p):
        return JSONResponse({"error": "not found"}, status_code=404)
    d = json.load(open(p, encoding="utf-8"))
    d["self_label"] = label
    d["self_label_stage"] = (stage_id or d.get("stage_id") or "")
    d["self_label_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

    snap = None
    if voice_sample:
        try:
            snap = json.loads(voice_sample)
        except Exception:
            snap = None
    if not isinstance(snap, dict):
        # Fall back to the acoustic snapshot saved with the take.
        c0 = (d.get("results") or [{}])[0]
        snap = c0.get("voice_sample") if isinstance(c0.get("voice_sample"), dict) else None
    if isinstance(snap, dict) and stage_id and not snap.get("stage_id"):
        snap = {**snap, "stage_id": stage_id}
    if isinstance(snap, dict) and d.get("verse") and not snap.get("verse"):
        snap = {**snap, "verse": d.get("verse")}

    updated = vp.record_label(_parse_voice_profile(voice_profile), label, snap)
    d["voice_sample"] = snap
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return {
        "ok": True,
        "self_label": label,
        "voice_profile": updated,
        "voice_stats": vp.profile_stats(updated),
    }


@app.get("/labels")
def labels():
    """Every labelled take, flattened — this is the accuracy dataset."""
    rows = []
    for d in storage.list_sessions():
        lab = d.get("self_label")
        if not lab:
            continue
        c = (d.get("results") or [{}])[0]
        probe = c.get("onset_probe") or {}
        rows.append({
            "session": d.get("session"),
            "when": d.get("when"),
            "verse": d.get("verse"),
            "stage_id": d.get("stage_id"),
            "learner_said": lab,
            "app_passed": c.get("stage_passed"),
            "agree": (
                (lab in ("correct", "think_correct")) == bool(c.get("stage_passed"))
                if lab in ("correct", "think_correct", "wrong", "think_wrong")
                else None
            ),
            "sound_letters": c.get("sound_letters"),
            "word_guess": c.get("heard_arabic"),
            "p_qaf": probe.get("p_qaf"),
            "p_kaf": probe.get("p_kaf"),
            "card": c.get("key"),
        })
    scored = [r for r in rows if r["agree"] is not None]
    agreed = [r for r in scored if r["agree"]]
    return JSONResponse({
        "labelled": len(rows),
        "scored": len(scored),
        "agreement": round(100 * len(agreed) / len(scored), 1) if scored else None,
        "takes": rows,
    })


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
    if not os.path.isdir(d):
        return JSONResponse({"error": "not found"}, status_code=404)
    for f in os.listdir(d):
        if f.startswith("audio."):
            path = os.path.join(d, f)
            ext = f.rsplit(".", 1)[-1].lower()
            media = {
                "m4a": "audio/mp4",
                "mp4": "audio/mp4",
                "aac": "audio/aac",
                "mp3": "audio/mpeg",
                "wav": "audio/wav",
                "webm": "audio/webm",
                "ogg": "audio/ogg",
            }.get(ext, "application/octet-stream")
            return FileResponse(
                path,
                media_type=media,
                headers={
                    "Content-Disposition": f'inline; filename="{sid}.{ext}"',
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "private, max-age=3600",
                },
            )
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/sessions/{sid}/play")
def session_play(sid: str):
    """Simple HTML player so takes open in-browser instead of downloading."""
    import re
    if not re.fullmatch(r"[0-9]{8}-[0-9]{6}-[a-f0-9]+", sid or ""):
        return JSONResponse({"error": "bad session"}, status_code=400)
    d = os.path.join(storage.STORE, sid)
    if not os.path.isdir(d):
        return JSONResponse({"error": "not found"}, status_code=404)
    # Pull heard labels if present
    label = ""
    try:
        import json
        meta = json.load(open(os.path.join(d, "data.json"), encoding="utf-8"))
        r = (meta.get("results") or [{}])[0]
        ph = r.get("heard_phonetic") or ""
        ar = r.get("heard_arabic") or ""
        if ph or ar:
            label = f"{ph} · {ar}".strip(" ·")
    except Exception:
        pass
    from fastapi.responses import HTMLResponse
    safe_label = (label or sid).replace("<", "").replace(">", "")
    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Take {sid}</title>
<style>
body{{font-family:Georgia,serif;max-width:28rem;margin:2rem auto;padding:0 1.2rem;background:#f7f4ef;color:#1a1a1a}}
h1{{font-size:1.1rem;margin:0 0 .5rem}}
p{{color:#556;font-size:.9rem}}
audio{{width:100%;margin-top:1rem}}
a{{color:#0b5}}
</style></head><body>
<h1>Your take</h1>
<p>{safe_label}</p>
<audio controls autoplay src="/sessions/{sid}/audio"></audio>
<p style="margin-top:1.2rem"><a href="/">← Tarteel</a></p>
</body></html>"""
    return HTMLResponse(html)


@app.get("/husary/{code}")
def husary_proxy(code: str):
    """Same-origin proxy — iOS Safari often fails on cross-origin Audio URLs."""
    import re
    import urllib.request
    if not re.fullmatch(r"\d{6}", code or ""):
        return JSONResponse({"error": "bad code"}, status_code=400)
    url = f"https://everyayah.com/data/Husary_128kbps/{code}.mp3"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Tarteel/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            ctype = resp.headers.get("Content-Type") or "audio/mpeg"
    except Exception as e:
        return JSONResponse({"error": f"husary fetch failed: {e}"}, status_code=502)
    from fastapi.responses import Response
    return Response(
        content=data,
        media_type=ctype,
        headers={
            "Cache-Control": "public, max-age=86400",
            "Accept-Ranges": "bytes",
        },
    )


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
