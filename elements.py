"""
Per-element feedback for Al-Ikhlas.
English phonetics first; Arabic lightly in brackets.

Card order (learner journey):
  1. All error cards
  2. Tip cards (measured / practice)
  3. NEXT STEP = first error repeated (reinforcement)
  4. (UI inserts retry controls here)
  5. Good cards — each self-standing with full ayah + highlight
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
# Priorities stay above word_shape (0..) so next-step prefers words first.
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


def build_feedback(verse, letters, qalqalah_result, heard_arabic=None, heard_phonetic=None):
    spec = VERSE_ELEMENTS.get(verse, {})
    ok_cards = []
    errors = []
    tips = []

    detected = [l for l in letters if l["c"] != "|"]
    if detected:
        nwords = len([l for l in letters if l["c"] == "|"]) + 1
        ok_cards.append(
            coach.word_order_card(
                verse,
                heard_arabic or "",
                heard_phonetic or "",
                nwords,
            )
        )

    # Pronunciation / word-shape (ayah order)
    if heard_arabic:
        errors.extend(
            coach.coach_from_heard(verse, heard_arabic, heard_phonetic or "")
        )

    # Madd
    for (letter, wen, war, desc, lo, hi, pri) in spec.get("madd", []):
        seg = _letter_span(letters, letter)
        if seg is None:
            continue
        if seg >= lo:
            ok_cards.append({
                "level": "ok",
                "rule": "madd",
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

    # Shadda
    for (letter, wen, war, desc, pri) in spec.get("shadda", []):
        if any(l["c"] == letter for l in letters):
            ok_cards.append({
                "level": "ok",
                "rule": "shadda",
                "word_en": wen,
                "word_ar": war,
                "section": coach.section_html(verse, wen),
                "plain": (
                    f"On <b>{wen}</b> <span class=\"arlight\">({war})</span>: "
                    f"{desc} came through."
                ),
                "scholarly": None,
            })

    # Qalqalah
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
            # defer → still give practice tip, lower urgency than clear errors
            tips.append(coach.ahad_bounce_card(verse, priority=qpri + 10))

    errors = sorted(
        errors,
        key=lambda x: (
            0 if (x.get("rule") == "word_shape" and x.get("identity")) else
            1 if x.get("rule") == "word_shape" else 2,
            x.get("priority", 50),
        ),
    )
    tips = sorted(tips, key=lambda x: x.get("priority", 50))
    issues = errors + tips  # for next-step pick (word_shape first)

    # Journey: all errors → tips → NEXT STEP (first issue again) → goods
    cards = []
    cards.extend(errors)
    cards.extend(tips)

    nxt = coach.pick_next_step(issues)
    if nxt:
        cards.append(nxt)
    elif not issues:
        line = coach.AYAH_LINE.get(verse) or {}
        keys = line.get("key") or [""]
        cards.append({
            "level": "next",
            "rule": "next_step",
            "tag": "NEXT STEP",
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
