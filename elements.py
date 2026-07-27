"""
Per-element feedback for Al-Ikhlas.
English phonetics first; Arabic lightly in brackets.
Issues are prioritized so UI can show one Next Step at a time.
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
        "madd":[("و","huwa","هُوَ","the uu in huwa",0.10,0.30,20)],
        "shadda":[("ل","Allāhu","ٱللَّهُ","the doubled L (ll)",30)],
        "qalqalah_priority": 40,
    },
    2: {
        "madd":[],
        "shadda":[("ص","aṣ-ṣamad","ٱلصَّمَدُ","the heavy doubled S",20)],
        "qalqalah_priority": 30,
    },
    3: {
        "madd":[("و","yūlad","يُولَدْ","the uu in yūlad",0.10,0.30,30)],
        "shadda":[],
        "qalqalah_priority": 20,
    },
    4: {
        "madd":[],
        "shadda":[],
        "qalqalah_priority": 50,
    },
}

def build_feedback(verse, letters, qalqalah_result, heard_arabic=None):
    spec = VERSE_ELEMENTS.get(verse, {})
    ok_cards = []
    issues = []

    detected = [l for l in letters if l["c"] != "|"]
    if detected:
        nwords = len([l for l in letters if l["c"] == "|"]) + 1
        ok_cards.append({
            "level": "ok",
            "plain": f"Got the word order — about {nwords} words lined up.",
            "scholarly": None,
        })

    # Pronunciation letter swaps (ayah order priorities 0..)
    if heard_arabic:
        issues.extend(coach.coach_from_heard(verse, heard_arabic))

    # Madd
    for (letter, wen, war, desc, lo, hi, pri) in spec.get("madd", []):
        seg = _letter_span(letters, letter)
        if seg is None:
            continue
        if seg >= lo:
            ok_cards.append({
                "level": "ok",
                "plain": (
                    f"On {wen} <span class=\"arlight\">({war})</span>: "
                    f"vowel length looked good (~{seg:.2f}s)."
                ),
                "scholarly": None,
            })
        else:
            issues.append(coach.madd_short_card(verse, wen, war, seg, pri))

    # Shadda
    for (letter, wen, war, desc, pri) in spec.get("shadda", []):
        if any(l["c"] == letter for l in letters):
            ok_cards.append({
                "level": "ok",
                "plain": (
                    f"On {wen} <span class=\"arlight\">({war})</span>: "
                    f"{desc} came through."
                ),
                "scholarly": None,
            })

    # Qalqalah
    qpri = spec.get("qalqalah_priority", 80)
    if qalqalah_result:
        lvl = qalqalah_result.get("level")
        if lvl == "ok":
            ok_cards.append({
                "level": "ok",
                "rule": "qalqalah",
                "plain": qalqalah_result.get("plain"),
                "scholarly": qalqalah_result.get("scholarly"),
                "p_error": qalqalah_result.get("p_error"),
                "confidence": qalqalah_result.get("confidence"),
                "verdict": "correct",
            })
        elif lvl == "error":
            soft = (qalqalah_result.get("confidence") or 0) < 0.70
            issues.append(coach.qalqalah_error_card(verse, soft=soft, priority=qpri))
        else:
            # defer → still give practice tip, lower urgency than clear errors
            issues.append(coach.ahad_bounce_card(verse, priority=qpri + 10))

    # NEXT STEP first (one fix), then other issues, then oks
    cards = []
    nxt = coach.pick_next_step(issues)
    if nxt:
        cards.append(nxt)
        top_issue = sorted(issues, key=lambda x: x.get("priority", 50))[0]
        rest = [c for c in sorted(issues, key=lambda x: x.get("priority", 50)) if c is not top_issue]
        cards.extend(rest)
    elif not issues:
        cards.append({
            "level": "ok",
            "rule": "next_step",
            "plain": (
                "<b>Nice — no clear fixes left on this ayah.</b> "
                "When you’re happy with it, move to the next ayah."
            ),
            "fix": None,
            "scholarly": None,
        })
    else:
        cards.extend(sorted(issues, key=lambda x: x.get("priority", 50)))

    cards.extend(ok_cards)
    return cards


def _letter_span(letters, target):
    for i, l in enumerate(letters):
        if l["c"] == target:
            if i + 1 < len(letters):
                return round(letters[i + 1]["t"] - l["t"], 3)
    return None
