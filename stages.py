"""
Beginner stage ladder for Al-Ikhlas.

Isolate a chunk → lock it → join with the previous → only then move on.
Forward only when the current stage passes; step back if an earlier piece breaks.

Stage UI contract (prototype — replicate for every new step; see static/index.html):
  Every live stage must show Hear only {current} + Correct/Incorrect for THAT stage.
  UI fields live on STAGE_LADDER in index.html:
    hear     — clip for this step only
    compare  — {note, ok:{src,title,sub}, bad:{src,title,sub}}
  Do not hard-code a Qul-only compare panel. Ayah 1 is the filled prototype;
  later ayahs get the same shape (stub compare until clips exist).
"""
from __future__ import annotations

# Each stage: id, English prompt, Arabic prompt, expected word keys (EXPECTED en names)
# word_idxs: indices into EXPECTED[verse]
# hear + compare are defined in static/index.html STAGE_LADDER (UI prototype).
STAGES = {
    1: [
        # Word-first: full Qul ×3, then syllable rescue (Qu → ul), then tutor defer.
        {
            "id": "qul",
            "title": "Qul",
            "say_en": "Qul",
            "say_ar": "قُلْ",
            "hint": (
                "Say the full word <b>Qul</b> (قُلْ).<br>"
                "<b>1.</b> Say <b>CAW-l</b> (the word “call”).<br>"
                "<b>2.</b> Hold that throat position — don’t move it.<br>"
                "<b>3.</b> Keep it there and change only the vowel to the short "
                "<b>u</b> in “pull” → <b>QUL</b>.<br>"
                "Not “KWOL” and not “KUL”. "
                "Three tries here; if stuck we’ll break it into Qu + ul."
            ),
            "words": ["qul"],
            "idxs": [0],
        },
        {
            "id": "qu",
            "title": "Qu",
            "say_en": "Qu",
            "say_ar": "قُ",
            "hint": (
                "Syllable rescue — only the start (قُ). Say <b>CAW</b> (the start of "
                "“call”) and stop before the L. That back throat position is the "
                "sound. Not “coo”, not “kwa”. "
                "Yellow mark on the ayah shows where you are."
            ),
            "words": [],
            "idxs": [0],
            "drill": "qu",
            "focus_word": "qul",
            "highlight": "qu",
        },
        {
            "id": "ul",
            "title": "ul",
            "say_en": "ul",
            "say_ar": "ـُلْ",
            "hint": "Only the ending: <b>ul</b> — like the end of “pull” / “full” (short u + clear L). No Q/K at the front.",
            "words": [],
            "idxs": [0],
            "drill": "ul",
            "focus_word": "qul",
            "highlight": "ul",
        },
        {
            "id": "huwa",
            "title": "huwa",
            "say_en": "huwa",
            "say_ar": "هُوَ",
            "hint": (
                "Say only <b>huwa</b>. English cue: <b>HOO-wa</b> — like “who” then “wa” "
                "(round lips on the W). Not “hoo-fa” or “boo-a”."
            ),
            "words": ["huwa"],
            "idxs": [1],
        },
        {
            "id": "qul_huwa",
            "title": "Qul huwa",
            "say_en": "Qul huwa",
            "say_ar": "قُلْ هُوَ",
            "hint": (
                "Join: <b>QUL</b> (throat from “call” + vowel from “pull”) then <b>HOO-wa</b>. "
                "Keep the deep throat K from Qul and the W from huwa."
            ),
            "words": ["qul", "huwa"],
            "idxs": [0, 1],
        },
        {
            "id": "allahu",
            "title": "Allāhu",
            "say_en": "Allāhu",
            "say_ar": "ٱللَّهُ",
            "hint": (
                "Say only <b>Allāhu</b>. English cue: <b>Al-LAA-hu</b> — hold the doubled L "
                "(like a long “ll” in “Allah”), then “hu”. Don’t rush it like English “Allah!”."
            ),
            "words": ["Allāhu"],
            "idxs": [2],
        },
        {
            "id": "qul_huwa_allahu",
            "title": "Qul huwa Allāhu",
            "say_en": "Qul huwa Allāhu",
            "say_ar": "قُلْ هُوَ ٱللَّهُ",
            "hint": "Join through Allāhu — QUL (call-throat + pull-vowel) · HOO-wa · Al-LAA-hu.",
            "words": ["qul", "huwa", "Allāhu"],
            "idxs": [0, 1, 2],
        },
        {
            "id": "ahad",
            "title": "aḥad",
            "say_en": "aḥad",
            "say_ar": "أَحَدٌ",
            "hint": (
                "Say only <b>aḥad</b>. English cue: <b>a-ḤAD</b> — the Ḥ is a fog-the-mirror breath "
                "(stronger than the H in “ahead”), then a light bounce on the D."
            ),
            "words": ["aḥad"],
            "idxs": [3],
        },
        {
            "id": "full",
            "title": "Full ayah",
            "say_en": "Qul huwa Allāhu aḥad",
            "say_ar": "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
            "hint": "Whole ayah: QUL (call-throat + pull-vowel) · HOO-wa · Al-LAA-hu · a-ḤAD. Keep every locked piece.",
            "words": ["qul", "huwa", "Allāhu", "aḥad"],
            "idxs": [0, 1, 2, 3],
        },
    ],
    2: [
        {
            "id": "allahu",
            "title": "Allāhu",
            "say_en": "Allāhu",
            "say_ar": "ٱللَّهُ",
            "hint": (
                "Say only <b>Allāhu</b>. English cue: <b>Al-LAA-hu</b> — hold the doubled L "
                "(like a long “ll”), then “hu”. Don’t rush it like English “Allah!”."
            ),
            "words": ["Allāhu"],
            "idxs": [0],
        },
        {
            "id": "samad",
            "title": "aṣ-ṣamad",
            "say_en": "aṣ-ṣamad",
            "say_ar": "ٱلصَّمَدُ",
            "hint": (
                "Say only <b>aṣ-ṣamad</b>. English cue: <b>as-ṢA-mad</b> — heavy Ṣ "
                "(darker than soft “s”), then “mad”."
            ),
            "words": ["aṣ-ṣamad"],
            "idxs": [1],
        },
        {
            "id": "full",
            "title": "Full ayah",
            "say_en": "Allāhu aṣ-ṣamad",
            "say_ar": "ٱللَّهُ ٱلصَّمَدُ",
            "hint": "Join: Al-LAA-hu · as-ṢA-mad. Keep the held L and the heavy Ṣ.",
            "words": ["Allāhu", "aṣ-ṣamad"],
            "idxs": [0, 1],
        },
    ],
    3: [
        {
            "id": "lam",
            "title": "Lam",
            "say_en": "Lam",
            "say_ar": "لَمْ",
            "hint": "Say only Lam.",
            "words": ["lam"],
            "idxs": [0],
        },
        {
            "id": "yalid",
            "title": "yalid",
            "say_en": "yalid",
            "say_ar": "يَلِدْ",
            "hint": "Say only yalid.",
            "words": ["yalid"],
            "idxs": [1],
        },
        {
            "id": "lam_yalid",
            "title": "Lam yalid",
            "say_en": "Lam yalid",
            "say_ar": "لَمْ يَلِدْ",
            "hint": "Join Lam yalid.",
            "words": ["lam", "yalid"],
            "idxs": [0, 1],
        },
        {
            "id": "wa_lam",
            "title": "wa lam",
            "say_en": "wa lam",
            "say_ar": "وَلَمْ",
            "hint": "Say only wa lam.",
            "words": ["wa lam"],
            "idxs": [2],
        },
        {
            "id": "yulad",
            "title": "yūlad",
            "say_en": "yūlad",
            "say_ar": "يُولَدْ",
            "hint": "Say only yūlad.",
            "words": ["yūlad"],
            "idxs": [3],
        },
        {
            "id": "full",
            "title": "Full ayah",
            "say_en": "Lam yalid wa lam yūlad",
            "say_ar": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
            "hint": "The whole ayah.",
            "words": ["lam", "yalid", "wa lam", "yūlad"],
            "idxs": [0, 1, 2, 3],
        },
    ],
    4: [
        {
            "id": "wa_lam",
            "title": "Wa lam",
            "say_en": "Wa lam",
            "say_ar": "وَلَمْ",
            "hint": "Say only Wa lam.",
            "words": ["wa lam"],
            "idxs": [0],
        },
        {
            "id": "yakun",
            "title": "yakun",
            "say_en": "yakun",
            "say_ar": "يَكُن",
            "hint": "Say only yakun.",
            "words": ["yakun"],
            "idxs": [1],
        },
        {
            "id": "lahu",
            "title": "lahu",
            "say_en": "lahu",
            "say_ar": "لَّهُ",
            "hint": "Say only lahu.",
            "words": ["lahu"],
            "idxs": [2],
        },
        {
            "id": "kufuwan",
            "title": "kufuwan",
            "say_en": "kufuwan",
            "say_ar": "كُفُوًا",
            "hint": "Say only kufuwan.",
            "words": ["kufuwan"],
            "idxs": [3],
        },
        {
            "id": "ahad",
            "title": "aḥad",
            "say_en": "aḥad",
            "say_ar": "أَحَدٌ",
            "hint": "Say only aḥad.",
            "words": ["aḥad"],
            "idxs": [4],
        },
        {
            "id": "full",
            "title": "Full ayah",
            "say_en": "Wa lam yakun lahu kufuwan aḥad",
            "say_ar": "وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ",
            "hint": "The whole ayah.",
            "words": ["wa lam", "yakun", "lahu", "kufuwan", "aḥad"],
            "idxs": [0, 1, 2, 3, 4],
        },
    ],
}


def list_stages(verse: int) -> list[dict]:
    return list(STAGES.get(verse) or [])


def get_stage(verse: int, stage_id: str | None) -> dict | None:
    stages = list_stages(verse)
    if not stages:
        return None
    if not stage_id:
        return stages[0]
    for s in stages:
        if s["id"] == stage_id:
            return s
    return stages[0]


def stage_index(verse: int, stage_id: str | None) -> int:
    stages = list_stages(verse)
    if not stages:
        return 0
    sid = (stage_id or stages[0]["id"])
    for i, s in enumerate(stages):
        if s["id"] == sid:
            return i
    return 0


def next_stage(verse: int, stage_id: str | None) -> dict | None:
    stages = list_stages(verse)
    i = stage_index(verse, stage_id)
    if i + 1 < len(stages):
        return stages[i + 1]
    return None


def prev_stage(verse: int, stage_id: str | None) -> dict | None:
    stages = list_stages(verse)
    i = stage_index(verse, stage_id)
    if i > 0:
        return stages[i - 1]
    return None


def stage_public(verse: int, stage_id: str | None) -> dict:
    """JSON-safe stage info for the client."""
    stages = list_stages(verse)
    cur = get_stage(verse, stage_id) or {}
    i = stage_index(verse, stage_id)
    return {
        "verse": verse,
        "stage_id": cur.get("id"),
        "index": i,
        "total": len(stages),
        "title": cur.get("title"),
        "say_en": cur.get("say_en"),
        "say_ar": cur.get("say_ar"),
        "hint": cur.get("hint"),
        "words": list(cur.get("words") or []),
        "idxs": list(cur.get("idxs") or []),
        "highlight": cur.get("highlight"),
        "drill": cur.get("drill"),
        "is_full": cur.get("id") == "full",
        "ladder": [
            {
                "id": s["id"],
                "title": s["title"],
                "say_en": s["say_en"],
                "idxs": list(s.get("idxs") or []),
                "highlight": s.get("highlight"),
            }
            for s in stages
        ],
    }


def word_in_stage(en: str, stage: dict | None) -> bool:
    if not stage:
        return True
    target = {(w or "").lower() for w in (stage.get("words") or [])}
    return (en or "").lower() in target


# Final bounce (qalqalah) word per ayah — only score when that word is in-stage.
QALQALAH_WORD = {1: "aḥad", 2: "aṣ-ṣamad", 3: "yalid", 4: "aḥad"}


def stage_needs_qalqalah(verse: int, stage_id: str | None) -> bool:
    """Word/drill stages without the bounce letter must not require final dal."""
    if not stage_id:
        return True  # no stage context → full ayah path
    stage = get_stage(verse, stage_id)
    if not stage:
        return True
    if stage.get("drill"):
        return False
    words = stage.get("words") or []
    if not words:
        return True
    qw = QALQALAH_WORD.get(verse)
    if not qw:
        return True
    return word_in_stage(qw, stage)


def earliest_failing_stage(verse: int, failing_words: list[str]) -> dict | None:
    """If a join breaks an earlier piece, step back to that piece's isolate stage."""
    stages = list_stages(verse)
    fail = {(w or "").lower() for w in failing_words}
    if not fail:
        return None
    # Qul onset lives in the Qu micro-drill — step there first.
    if "qul" in fail:
        for s in stages:
            if s.get("id") == "qu":
                return s
    for s in stages:
        # Prefer single-word stages that match a failure (skip empty drill stages)
        words = s.get("words") or []
        if len(words) == 1 and (words[0] or "").lower() in fail:
            return s
    for s in stages:
        if any((w or "").lower() in fail for w in (s.get("words") or [])):
            return s
    return None


def stage_html(verse: int, stage_id: str | None) -> str:
    info = stage_public(verse, stage_id)
    if not info.get("stage_id"):
        return ""
    i = info["index"] + 1
    n = info["total"]
    return (
        f'<div class="stagcard">'
        f'<div class="staglbl">Stage {i} of {n} — {info["title"]}</div>'
        f'<div class="stagsay">{info["say_en"]}</div>'
        f'<div class="stagar" dir="rtl" lang="ar">{info["say_ar"]}</div>'
        f'<div class="staghint">{info["hint"]}</div>'
        f"</div>"
    )
