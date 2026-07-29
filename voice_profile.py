"""
Speaker-relative acoustic baselines — fold into practice, no onboarding gate.

Each device learns this learner's voice from self-labels (correct / wrong) during
practice. Absolute letter gates still win on clear takes. Relative scoring only
helps the gray zone, where a fixed threshold is unfair across throats and mics.

Profile lives on the client (localStorage). Railway session disks wipe on
redeploy, so server-only storage would lose the calibration.
"""
from __future__ import annotations

import math
from typing import Any

PROFILE_VERSION = 1
MAX_SAMPLES = 8
# Need a small cluster before we trust relative distance.
MIN_FOR_RELATIVE = 2
# Absolute onset already decided — do not second-guess.
# Gray-zone rescue needs a little energy so silence cannot "match" a sparse good set.
MIN_ENERGY = 0.18
# Relative margin: must be clearly closer to one pole than the other.
REL_MARGIN = 0.12
# Key-letter soft pass: at least this fraction of the learner's median good score.
KEY_SOFT_FRAC = 0.70
KEY_SOFT_FLOOR = 0.28

# Stages whose self-label teaches the deep-throat-K vs English-K contrast.
QAF_STAGES = frozenset({"qul", "qu"})

# Stage → teaching letter for key-letter baselines (single letters only).
STAGE_LETTER = {
    ("qul", 1): "ل",
    ("huwa", 1): "و",
    ("ahad", 1): "ح",
    ("ahad", 4): "ح",
    ("samad", 2): "ص",
}


def empty_profile() -> dict:
    return {
        "version": PROFILE_VERSION,
        "qaf_good": [],
        "qaf_bad": [],
        "letters": {},  # letter -> {"good": [float], "bad": [float]}
    }


def parse_profile(raw) -> dict:
    """Accept a dict or JSON-ish object from the client; never raise."""
    if not isinstance(raw, dict):
        return empty_profile()
    out = empty_profile()
    if int(raw.get("version") or 0) != PROFILE_VERSION and raw.get("qaf_good") is None:
        return out
    out["qaf_good"] = _clip_points(raw.get("qaf_good"))
    out["qaf_bad"] = _clip_points(raw.get("qaf_bad"))
    letters = raw.get("letters") if isinstance(raw.get("letters"), dict) else {}
    cleaned = {}
    for letter, buckets in letters.items():
        if not isinstance(letter, str) or not letter or not isinstance(buckets, dict):
            continue
        cleaned[letter] = {
            "good": _clip_scores(buckets.get("good")),
            "bad": _clip_scores(buckets.get("bad")),
        }
    out["letters"] = cleaned
    return out


def _clip_points(rows) -> list[dict]:
    out = []
    if not isinstance(rows, list):
        return out
    for row in rows[-MAX_SAMPLES:]:
        if not isinstance(row, dict):
            continue
        try:
            pq = float(row.get("p_qaf") or 0.0)
            pk = float(row.get("p_kaf") or 0.0)
        except (TypeError, ValueError):
            continue
        out.append({"p_qaf": round(pq, 4), "p_kaf": round(pk, 4)})
    return out[-MAX_SAMPLES:]


def _clip_scores(rows) -> list[float]:
    out = []
    if not isinstance(rows, list):
        return out
    for x in rows[-MAX_SAMPLES:]:
        try:
            out.append(round(float(x), 4))
        except (TypeError, ValueError):
            continue
    return out[-MAX_SAMPLES:]


def take_snapshot(
    onset_probe: dict | None,
    sound_evidence: dict | None,
    stage_id: str | None = None,
    verse: int | None = None,
) -> dict:
    """Compact acoustic snapshot for this take — stored after the learner labels."""
    probe = onset_probe or {}
    ev = sound_evidence or {}
    evidence = {}
    if isinstance(ev, dict):
        for k, v in ev.items():
            try:
                evidence[str(k)] = round(float(v), 4)
            except (TypeError, ValueError):
                continue
    return {
        "p_qaf": round(float(probe.get("p_qaf") or 0.0), 4),
        "p_kaf": round(float(probe.get("p_kaf") or 0.0), 4),
        "onset": (probe.get("onset") or "")[:8],
        "evidence": evidence,
        "stage_id": (stage_id or "")[:32],
        "verse": int(verse) if verse else None,
    }


def record_label(profile: dict | None, label: str, snapshot: dict | None) -> dict:
    """Fold one self-label into the device profile. Unsure is ignored."""
    out = parse_profile(profile)
    lab = (label or "").strip().lower()
    snap = snapshot if isinstance(snapshot, dict) else None
    if lab not in ("correct", "wrong") or not snap:
        return out

    stage = (snap.get("stage_id") or "").strip()
    verse = snap.get("verse")
    try:
        verse_i = int(verse) if verse is not None else None
    except (TypeError, ValueError):
        verse_i = None

    point = {
        "p_qaf": float(snap.get("p_qaf") or 0.0),
        "p_kaf": float(snap.get("p_kaf") or 0.0),
    }
    if stage in QAF_STAGES:
        # Only keep anchors the acoustics actually support — a "correct" label
        # on a take with no clear ق must not teach the profile that 0.57/0.43
        # is a good deep-throat K.
        if lab == "correct" and point["p_qaf"] < 0.60:
            pass
        elif lab == "wrong" and point["p_kaf"] < 0.35 and point["p_qaf"] >= point["p_kaf"]:
            pass
        else:
            bucket = "qaf_good" if lab == "correct" else "qaf_bad"
            rows = list(out.get(bucket) or [])
            rows.append(point)
            out[bucket] = rows[-MAX_SAMPLES:]

    letter = STAGE_LETTER.get((stage, verse_i or 0))
    if letter:
        ev = snap.get("evidence") if isinstance(snap.get("evidence"), dict) else {}
        # Doubled L uses transcript elsewhere; single-letter evidence only here.
        score = float(ev.get(letter) or 0.0)
        # Dark L often lands as ر on Omar's takes — count that alias for laam.
        if letter == "ل":
            score = max(score, float(ev.get("ر") or 0.0))
        # Don't store "correct" with near-zero letter evidence — that poisons
        # the soft-pass baseline (session c9342d: learner said correct, L=0.13).
        if lab == "correct" and score < 0.35:
            pass
        else:
            letters = dict(out.get("letters") or {})
            slot = dict(letters.get(letter) or {"good": [], "bad": []})
            key = "good" if lab == "correct" else "bad"
            scores = list(slot.get(key) or [])
            scores.append(round(score, 4))
            slot[key] = scores[-MAX_SAMPLES:]
            letters[letter] = slot
            out["letters"] = letters

    return out


def _centroid(points: list[dict]) -> tuple[float, float] | None:
    if not points:
        return None
    pq = sum(float(p.get("p_qaf") or 0.0) for p in points) / len(points)
    pk = sum(float(p.get("p_kaf") or 0.0) for p in points) / len(points)
    return pq, pk


def _dist(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def relative_qaf_hint(probe: dict | None, profile: dict | None) -> dict | None:
    """If absolute onset is ambiguous, try this learner's own qaf/kaf anchors.

    Returns None when relative scoring must stay silent (not enough data, or
    absolute already clear). Never invents a letter from silence.
    """
    from coaching import onset_qaf_verdict

    abs_v = onset_qaf_verdict(probe)
    if abs_v.get("has_qaf") or abs_v.get("has_kaf"):
        return None

    prof = parse_profile(profile)
    good = prof.get("qaf_good") or []
    bad = prof.get("qaf_bad") or []
    if len(good) < MIN_FOR_RELATIVE and len(bad) < MIN_FOR_RELATIVE:
        return None

    pq = float(abs_v.get("p_qaf") or 0.0)
    pk = float(abs_v.get("p_kaf") or 0.0)
    if pq + pk < MIN_ENERGY:
        return None

    point = (pq, pk)
    c_good = _centroid(good) if len(good) >= MIN_FOR_RELATIVE else None
    c_bad = _centroid(bad) if len(bad) >= MIN_FOR_RELATIVE else None
    if c_good is None and c_bad is None:
        return None

    d_good = _dist(point, c_good) if c_good else None
    d_bad = _dist(point, c_bad) if c_bad else None

    # Only one pole trained: require being close to it, not merely "closer than nothing".
    if c_good is not None and c_bad is None:
        if d_good is not None and d_good <= 0.35 and pq >= pk:
            return {
                "has_qaf": True,
                "has_kaf": False,
                "source": "speaker_relative",
                "d_good": round(d_good, 3),
                "d_bad": None,
            }
        return None
    if c_bad is not None and c_good is None:
        if d_bad is not None and d_bad <= 0.35 and pk >= pq:
            return {
                "has_qaf": False,
                "has_kaf": True,
                "source": "speaker_relative",
                "d_good": None,
                "d_bad": round(d_bad, 3),
            }
        return None

    assert d_good is not None and d_bad is not None
    if d_good + REL_MARGIN < d_bad and pq >= pk * 0.85:
        return {
            "has_qaf": True,
            "has_kaf": False,
            "source": "speaker_relative",
            "d_good": round(d_good, 3),
            "d_bad": round(d_bad, 3),
        }
    if d_bad + REL_MARGIN < d_good and pk >= pq * 0.85:
        return {
            "has_qaf": False,
            "has_kaf": True,
            "source": "speaker_relative",
            "d_good": round(d_good, 3),
            "d_bad": round(d_bad, 3),
        }
    return None


def resolve_qaf_verdict(probe: dict | None, profile: dict | None = None) -> dict:
    """Absolute onset first; speaker-relative only fills the gray zone."""
    from coaching import onset_qaf_verdict

    abs_v = onset_qaf_verdict(probe)
    out = {**abs_v, "source": "absolute"}
    if abs_v.get("has_qaf") or abs_v.get("has_kaf"):
        return out
    hint = relative_qaf_hint(probe, profile)
    if not hint:
        return out
    return {
        **abs_v,
        "has_qaf": bool(hint.get("has_qaf")),
        "has_kaf": bool(hint.get("has_kaf")),
        "source": "speaker_relative",
        "relative": {
            "d_good": hint.get("d_good"),
            "d_bad": hint.get("d_bad"),
        },
    }


def _median(xs: list[float]) -> float | None:
    if not xs:
        return None
    s = sorted(xs)
    n = len(s)
    if n % 2:
        return s[n // 2]
    return 0.5 * (s[n // 2 - 1] + s[n // 2])


def key_letter_relative_ok(
    letter: str,
    score: float,
    profile: dict | None,
) -> bool:
    """Soft-pass a near-miss key letter when it matches this learner's goods."""
    if score < KEY_SOFT_FLOOR:
        return False
    prof = parse_profile(profile)
    slot = (prof.get("letters") or {}).get(letter) or {}
    goods = list(slot.get("good") or [])
    bads = list(slot.get("bad") or [])
    if len(goods) < MIN_FOR_RELATIVE:
        return False
    med = _median(goods)
    if med is None or med < KEY_SOFT_FLOOR:
        return False
    if score < med * KEY_SOFT_FRAC:
        return False
    if bads:
        med_bad = _median(bads) or 0.0
        # Must look more like their good takes than their bad ones.
        if abs(score - med) > abs(score - med_bad):
            return False
    return True


def profile_stats(profile: dict | None) -> dict[str, Any]:
    p = parse_profile(profile)
    return {
        "version": p["version"],
        "qaf_good_n": len(p.get("qaf_good") or []),
        "qaf_bad_n": len(p.get("qaf_bad") or []),
        "letters": {
            k: {
                "good_n": len((v or {}).get("good") or []),
                "bad_n": len((v or {}).get("bad") or []),
            }
            for k, v in (p.get("letters") or {}).items()
        },
    }
