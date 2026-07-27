"""
Per-element feedback for Al-Ikhlas.
English phonetics first; Arabic lightly in brackets.

Card journey (UI focuses the learner):
  NEXT STEP (one focus; regressions first if a prior win broke)
  → retry actions
  → all other cards (regression / progress check)
"""
import coaching as coach

SOUND = {
    "ق":"qaf (deep K)","ل":"lam (L)","ه":"ha (soft H)","و":"waw (W)",
    "ا":"alif (aa)","ح":"Ha (throat H)","د":"dal (D)","ص":"Sad (heavy S)",
    "م":"meem (M)","ي":"ya (Y)","ن":"noon (N)","ك":"kaf (K)","ف":"fa (F)",
    "ب":"ba (B)","ت":"ta (T)","ر":"ra (R)","أ":"hamza (glottal)",
    "|":"(word break)",
}

# madd targets: (letter, word_en, word_ar, desc, lo, hi, priority)
VERSE_ELEMENTS = {
    1: {
        "madd":[("و","huwa","هُوَ","the uu in huwa",0.10,0.30,60)],
        "shadda":[("ل","Allāhu","ٱللَّهُ","the doubled L (ll)",30)],
        "qalqalah_priority": 70,
    },
    2: {
        "madd":[],
        "shadda":[("ص","aṣ-ṣamad","ٱلصَّمَدُ","the heavy doubled S",20)],
        "qalqalah_priority": 70,
    },
    3: {
        "madd":[("و","yūlad","يُولَدْ","the uu in yūlad",0.10,0.30,60)],
        "shadda":[],
        "qalqalah_priority": 70,
    },
    4: {
        "madd":[],
        "shadda":[],
        "qalqalah_priority": 70,
    },
}


def build_feedback(
    verse,
    letters,
    qalqalah_result,
    heard_arabic=None,
    heard_phonetic=None,
    mastered=None,
    last_focus=None,
):
    spec = VERSE_ELEMENTS.get(verse, {})
    ok_cards = []
    errors = []
    tips = []

    detected = [l for l in letters if l["c"] != "|"]
    if detected:
        nwords = len([l for l in letters if l["c"] == "|"]) + 1
        wo = coach.word_order_card(
            verse,
            heard_arabic or "",
            heard_phonetic or "",
            nwords,
        )
        wo["key"] = "word_order"
        ok_cards.append(wo)

    if heard_arabic:
        errors.extend(
            coach.coach_from_heard(verse, heard_arabic, heard_phonetic or "")
        )

    for (letter, wen, war, desc, lo, hi, pri) in spec.get("madd", []):
        seg = _letter_span(letters, letter)
        if seg is None:
            continue
        if seg >= lo:
            ok_cards.append({
                "level": "ok",
                "rule": "madd",
                "key": f"madd:{wen}",
                "word_en": wen,
                "word_ar": war,
                "section": coach.section_html(verse, wen),
                "plain": (
                    f"On <b>{wen}</b> <span class=\"arlight\">({war})</span>: "
                    f"vowel length looked good (~{seg:.2f}s)."
                ),
                "scholarly": None,
            })
        else:
            tips.append(coach.madd_short_card(verse, wen, war, seg, pri))

    for (letter, wen, war, desc, pri) in spec.get("shadda", []):
        if any(l["c"] == letter for l in letters):
            ok_cards.append({
                "level": "ok",
                "rule": "shadda",
                "key": f"shadda:{wen}",
                "word_en": wen,
                "word_ar": war,
                "section": coach.section_html(verse, wen),
                "plain": (
                    f"On <b>{wen}</b> <span class=\"arlight\">({war})</span>: "
                    f"{desc} came through."
                ),
                "scholarly": None,
            })

    qpri = spec.get("qalqalah_priority", 80)
    if qalqalah_result:
        lvl = qalqalah_result.get("level")
        q_en = "aḥad"
        if verse == 2:
            q_en = "aṣ-ṣamad"
        elif verse == 3:
            q_en = "yalid"
        if lvl == "ok":
            ok_cards.append({
                "level": "ok",
                "rule": "qalqalah",
                "key": f"qalqalah:{q_en}",
                "section": coach.section_html(verse, q_en),
                "plain": qalqalah_result.get("plain"),
                "scholarly": qalqalah_result.get("scholarly"),
                "p_error": qalqalah_result.get("p_error"),
                "confidence": qalqalah_result.get("confidence"),
                "verdict": "correct",
            })
        elif lvl == "error":
            soft = (qalqalah_result.get("confidence") or 0) < 0.70
            errors.append(coach.qalqalah_error_card(verse, soft=soft, priority=qpri))
        else:
            tips.append(coach.ahad_bounce_card(verse, priority=qpri + 10))

    errors = sorted(errors, key=coach._issue_sort_key)
    tips = sorted(tips, key=lambda x: x.get("priority", 50))
    issues = errors + tips

    cards = []
    cards.extend(errors)
    cards.extend(tips)

    nxt = coach.pick_next_step(issues, mastered=mastered, last_focus=last_focus)
    if nxt:
        cards.append(nxt)
    elif not issues:
        line = coach.AYAH_LINE.get(verse) or {}
        keys = line.get("key") or [""]
        cards.append({
            "level": "next",
            "rule": "next_step",
            "tag": "NEXT STEP",
            "key": "ayah_clear",
            "section": coach.section_html(verse, keys[0]),
            "plain": (
                "<b>Nice — no clear fixes left on this ayah.</b> "
                "When you’re happy with it, move to the next ayah."
            ),
            "fix": None,
            "scholarly": None,
        })

    cards.extend(ok_cards)
    return cards


def _letter_span(letters, target):
    for i, l in enumerate(letters):
        if l["c"] == target:
            if i + 1 < len(letters):
                return round(letters[i + 1]["t"] - l["t"], 3)
    return None
