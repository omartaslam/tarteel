"""
Session storage: save every recording + computed data so we can diagnose
live behaviour (esp. defer cases) and review real iPhone takes.
Railway disk for now (wipes on redeploy). Migrate to R2/S3 later.
"""
import os, json, time, uuid

STORE = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(STORE, exist_ok=True)

def save(audio_bytes, ext, verse, results, extra=None):
    sid = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
    d = os.path.join(STORE, sid); os.makedirs(d, exist_ok=True)
    # raw audio exactly as the UI captured it
    with open(os.path.join(d, f"audio.{ext}"), "wb") as f:
        f.write(audio_bytes)
    # everything computed
    meta = {"session": sid, "verse": verse, "results": results,
            "when": time.strftime("%Y-%m-%d %H:%M:%S"), **(extra or {})}
    with open(os.path.join(d, "data.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return sid

def list_sessions():
    out = []
    for sid in sorted(os.listdir(STORE), reverse=True):
        p = os.path.join(STORE, sid, "data.json")
        if os.path.exists(p):
            out.append(json.load(open(p, encoding="utf-8")))
    return out
