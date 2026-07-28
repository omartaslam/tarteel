"""
Beginner stage ladder for Al-Ikhlas.

Isolate a chunk → lock it → join with the previous → only then move on.
Forward only when the current stage passes; step back if an earlier piece breaks.
"""
from __future__ import annotations

# Each stage: id, English prompt, Arabic prompt, expected word keys (EXPECTED en names)
# word_idxs: indices into EXPECTED[verse]
STAGES = {
    1: [
        # Micro-drills: lock the deep-Q onset, then the ending, then join as Qul.
        # "drill" stages use syllable scoring (not full-word ayah alignment).
        {
            "id": "qu",
            "title": "Qu",
            "say_en": "Qu",
            "say_ar": "قُ",
            "hint": (
                "Only the first half: deep Q + short “u”. "
                "Soft-gargle place in the throat — not English K."
            ),
            "words": [],
            "idxs": [],
            "drill": "qu",
            "focus_word": "qul",
        },
        {
            "id": "ul",
            "title": "ul",
            "say_en": "ul",
            "say_ar": "ـُلْ",
            "hint": "Only the ending: “ul” — short u + clear L. No first letter yet.",
            "words": [],
            "idxs": [],
            "drill": "ul",
            "focus_word": "qul",
        },
        {
            "id": "qul",
            "title": "Qul",
            "say_en": "Qul",
            "say_ar": "قُلْ",
            "hint": "Join Qu + ul into one short word: Qul.",
            "words": ["qul"],
            "idxs": [0],
        },
        {
            "id": "huwa",
            "title": "huwa",
            "say_en": "huwa",
            "say_ar": "هُوَ",
            "hint": "Say only huwa — round the lips for the W.",
            "words": ["huwa"],
            "idxs": [1],
        },
        {
            "id": "qul_huwa",
            "title": "Qul huwa",
            "say_en": "Qul huwa",
            "say_ar": "قُلْ هُوَ",
            "hint": "Join the two words you locked.",
            "words": ["qul", "huwa"],
            "idxs": [0, 1],
        },
        {
            "id": "allahu",
            "title": "Allāhu",
            "say_en": "Allāhu",
            "say_ar": "ٱللَّهُ",
            "hint": "Say only Allāhu — hold the doubled L.",
            "words": ["Allāhu"],
            "idxs": [2],
        },
        {
            "id": "qul_huwa_allahu",
            "title": "Qul huwa Allāhu",
            "say_en": "Qul huwa Allāhu",
            "say_ar": "قُلْ هُوَ ٱللَّهُ",
            "hint": "Join through Allāhu.",
            "words": ["qul", "huwa", "Allāhu"],
            "idxs": [0, 1, 2],
        },
        {
            "id": "ahad",
            "title": "aḥad",
            "say_en": "aḥad",
            "say_ar": "أَحَدٌ",
            "hint": "Say only aḥad — finish with a light bounce on the D.",
            "words": ["aḥad"],
            "idxs": [3],
        },
        {
            "id": "full",
            "title": "Full ayah",
            "say_en": "Qul huwa Allāhu aḥad",
            "say_ar": "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
            "hint": "The whole ayah — keep every locked piece.",
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
            "hint": "Say only Allāhu.",
            "words": ["Allāhu"],
            "idxs": [0],
        },
        {
            "id": "samad",
            "title": "aṣ-ṣamad",
            "say_en": "aṣ-ṣamad",
            "say_ar": "ٱلصَّمَدُ",
            "hint": "Say only aṣ-ṣamad.",
            "words": ["aṣ-ṣamad"],
            "idxs": [1],
        },
        {
            "id": "full",
            "title": "Full ayah",
            "say_en": "Allāhu aṣ-ṣamad",
            "say_ar": "ٱللَّهُ ٱلصَّمَدُ",
            "hint": "Join both words.",
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
        "drill": cur.get("drill"),
        "is_full": cur.get("id") == "full",
        "ladder": [
            {"id": s["id"], "title": s["title"], "say_en": s["say_en"]}
            for s in stages
        ],
    }


def word_in_stage(en: str, stage: dict | None) -> bool:
    if not stage:
        return True
    target = {(w or "").lower() for w in (stage.get("words") or [])}
    return (en or "").lower() in target


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
