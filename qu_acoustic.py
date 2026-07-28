"""
Qu (ق vs ك) acoustic scorer — corpus cluster + hybrid ASR gate.

Trained on adult male EveryAyah Qul onsets (correct back ق) vs middle-ك /
Kul clips (incorrect). Runtime decision:

  • PASS  only if ASR shows ق AND acoustic looks like the correct cluster
  • FAIL  if ASR shows ك (never lock Qu on kaf) — or acoustic strongly kaf
  • DEFER when ASR ق but acoustic is unsure / disagrees (ask teacher, clear reason)

False "Locked Qu" is worse than an occasional defer.
"""
from __future__ import annotations

import os
import pickle
import re
import subprocess
import tempfile
from functools import lru_cache

import librosa
import numpy as np

SR = 22050
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "qu_qaf_cluster.pkl")

_DIAC = re.compile(r"[\u064B-\u065F\u0670\u0640\u06D6-\u06ED]")


@lru_cache(maxsize=1)
def _load_model():
    if not os.path.exists(MODEL_PATH):
        return None
    with open(MODEL_PATH, "rb") as f:
        return pickle.load(f)


def _load_wav(path: str, sr: int = SR) -> np.ndarray:
    if path.lower().endswith(".wav"):
        y, _ = librosa.load(path, sr=sr)
        return y
    out = tempfile.mktemp(suffix=".wav")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", path, "-ar", str(sr), "-ac", "1", out],
            capture_output=True,
            check=False,
        )
        y, _ = librosa.load(out, sr=sr)
        return y
    finally:
        try:
            if os.path.exists(out):
                os.unlink(out)
        except OSError:
            pass


def _onset_seg(y: np.ndarray, sr: int = SR, dur: float = 0.30) -> np.ndarray:
    yt, _ = librosa.effects.trim(y, top_db=28)
    if len(yt) < int(0.08 * sr):
        yt = y
    oenv = librosa.onset.onset_strength(y=yt, sr=sr)
    ons = librosa.onset.onset_detect(onset_envelope=oenv, sr=sr, units="samples")
    start = max(0, int(ons[0]) - int(0.015 * sr)) if len(ons) else 0
    end = min(len(yt), start + int(dur * sr))
    if end - start < int(0.10 * sr):
        start, end = 0, min(len(yt), int(dur * sr))
    return yt[start:end]


def _feat(seg: np.ndarray, sr: int = SR) -> np.ndarray | None:
    s = seg.astype(np.float32)
    if len(s) < 128:
        return None
    s = s / (np.max(np.abs(s)) + 1e-9) * 0.9
    mf = librosa.feature.mfcc(y=s, sr=sr, n_mfcc=13, n_fft=512, hop_length=128)
    delta = librosa.feature.delta(mf)
    cent = librosa.feature.spectral_centroid(y=s, sr=sr, n_fft=512, hop_length=128)[0]
    bw = librosa.feature.spectral_bandwidth(y=s, sr=sr, n_fft=512, hop_length=128)[0]
    flat = librosa.feature.spectral_flatness(y=s, n_fft=512, hop_length=128)[0]
    zcr = librosa.feature.zero_crossing_rate(s, hop_length=128)[0]
    rms = librosa.feature.rms(y=s, hop_length=128)[0]
    S = np.abs(librosa.stft(s, n_fft=512, hop_length=128))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=512)

    def br(a, b):
        m = (freqs >= a) & (freqs < b)
        return float(S[m].mean()) if m.any() else 0.0

    low, mid, high = br(80, 700), br(700, 2200), br(2200, 6500)
    tot = low + mid + high + 1e-12
    half = max(len(s) // 3, 128)
    early, late = s[:half], s[half:]
    c_e = float(
        librosa.feature.spectral_centroid(y=early, sr=sr, n_fft=512, hop_length=128).mean()
    )
    c_l = (
        float(librosa.feature.spectral_centroid(y=late, sr=sr, n_fft=512, hop_length=128).mean())
        if len(late) > 64
        else c_e
    )
    return np.concatenate(
        [
            mf.mean(1),
            mf.std(1),
            delta.mean(1),
            [
                cent.mean(),
                cent.std(),
                bw.mean(),
                flat.mean(),
                zcr.mean(),
                rms.min(),
                rms.max(),
                rms.max() - rms.min(),
                low / tot,
                mid / tot,
                high / tot,
                c_e,
                c_l,
                c_e - c_l,
                len(s) / sr,
            ],
        ]
    ).astype(np.float64)


def score_audio(y: np.ndarray, sr: int = SR) -> dict | None:
    """Acoustic-only scores for a waveform (already mono)."""
    model = _load_model()
    if model is None:
        return None
    seg = _onset_seg(y, sr=sr)
    v = _feat(seg, sr=sr)
    if v is None:
        return None
    pipe = model["pipeline"]
    sc = pipe.named_steps["sc"]
    c_pos = model["centroid_q"]
    c_neg = model["centroid_k"]
    p_q = float(pipe.predict_proba([v])[0, 1])
    zs = sc.transform([v])[0]
    d_q = float(np.linalg.norm(zs - c_pos))
    d_k = float(np.linalg.norm(zs - c_neg))
    thr = model.get("thresholds") or {}
    return {
        "p_qaf": round(p_q, 4),
        "d_q": round(d_q, 4),
        "d_k": round(d_k, 4),
        "margin": round(d_k - d_q, 4),
        "version": model.get("version", "qu_acoustic"),
        "thresholds": thr,
    }


def score_path(path: str) -> dict | None:
    try:
        y = _load_wav(path)
        return score_audio(y, sr=SR)
    except Exception as e:
        return {"error": str(e), "p_qaf": None}


def _asr_flags(heard_arabic: str, heard_phonetic: str) -> tuple[bool, bool]:
    ar = _DIAC.sub("", heard_arabic or "")
    letters = "".join(c for c in ar if not c.isspace())
    ph = (heard_phonetic or "").lower()
    ph_compact = re.sub(r"[^a-zāḥṣṭḍẓ]", "", ph)
    has_q = "ق" in letters
    has_k = "ك" in letters or bool(
        re.search(r"(^|[^a-z])(k|c)(oo|u|o|a|ull)", ph)
    ) or ph_compact.startswith(("ku", "coo", "cul", "kol", "ko", "kull", "kul"))
    return has_q, has_k


def _acoustic_q(p_q: float, margin: float, thr: dict) -> bool:
    hi = float(thr.get("pass_p_hi", 0.82))
    p = float(thr.get("pass_p", 0.70))
    m = float(thr.get("pass_margin", 0.20))
    return (p_q >= hi) or (p_q >= p and margin >= m)


def _acoustic_k(p_q: float, margin: float, thr: dict) -> bool:
    lo = float(thr.get("fail_p_lo", 0.28))
    p = float(thr.get("fail_p", 0.40))
    m = float(thr.get("fail_margin", -0.30))
    return (p_q <= lo) or (p_q <= p and margin <= m)


def decide(
    heard_arabic: str,
    heard_phonetic: str = "",
    acoustic: dict | None = None,
) -> dict:
    """
    Hybrid Qu verdict.

    Returns dict with keys: verdict ('pass'|'fail'|'defer'), reason, asr_q, asr_k,
    acoustic (echo), plain (learner-facing reason when defer/fail context needed).
    """
    has_q, has_k = _asr_flags(heard_arabic, heard_phonetic)
    ac = acoustic if isinstance(acoustic, dict) and acoustic.get("p_qaf") is not None else None
    thr = (ac or {}).get("thresholds") or ((_load_model() or {}).get("thresholds") or {})

    base = {
        "asr_q": has_q,
        "asr_k": has_k,
        "acoustic": ac,
        "version": (ac or {}).get("version") or "asr_only",
    }

    # No acoustic model available → keep legacy ASR letter gate (stable behaviour).
    if ac is None:
        if has_q:
            return {**base, "verdict": "pass", "reason": "asr_qaf_no_acoustic_model", "plain": ""}
        if has_k:
            return {**base, "verdict": "fail", "reason": "asr_kaf_no_acoustic_model", "plain": ""}
        return {
            **base,
            "verdict": "fail",
            "reason": "asr_unclear_no_acoustic_model",
            "plain": "",
        }

    p_q = float(ac["p_qaf"])
    margin = float(ac["margin"])
    ac_q = _acoustic_q(p_q, margin, thr)
    ac_k = _acoustic_k(p_q, margin, thr)

    # Never lock Qu when ASR heard middle ك.
    if has_k:
        return {
            **base,
            "verdict": "fail",
            "reason": "asr_kaf",
            "plain": "",
            "acoustic_q": ac_q,
            "acoustic_k": ac_k,
        }

    if has_q and ac_q:
        return {
            **base,
            "verdict": "pass",
            "reason": "asr_and_acoustic_qaf",
            "plain": "",
            "acoustic_q": ac_q,
            "acoustic_k": ac_k,
        }

    if has_q and ac_k:
        return {
            **base,
            "verdict": "defer",
            "reason": "disagree_asr_qaf_acoustic_kaf",
            "plain": (
                "I’m not confident enough to lock Qu yet. "
                "The transcript looked like a back Q, but the sound is closer to a middle K. "
                "Try again with a deeper / more hollow Q — or ask a teacher to confirm."
            ),
            "acoustic_q": ac_q,
            "acoustic_k": ac_k,
        }

    if has_q and not ac_q:
        return {
            **base,
            "verdict": "defer",
            "reason": "asr_qaf_acoustic_unsure",
            "plain": (
                "I’m not confident enough to lock Qu yet. "
                "I need a clearer deep back Q (not English / middle K). "
                "Listen to the correct sample, then try one short Qu."
            ),
            "acoustic_q": ac_q,
            "acoustic_k": ac_k,
        }

    # ASR heard neither ق nor ك (garbage / other letter). Do NOT invent “Ku”
    # from acoustics alone — that falsely accused a take of middle-K.
    return {
        **base,
        "verdict": "defer",
        "reason": "asr_unclear",
        "plain": (
            "I couldn’t clearly hear Qu on this take — not confident enough to judge. "
            "Say one short <b>Qu</b> (deep back Q + “u”) closer to the phone, "
            "or ask a teacher if this keeps happening."
        ),
        "acoustic_q": ac_q,
        "acoustic_k": ac_k,
    }
