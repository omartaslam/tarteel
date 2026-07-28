"""
Per-element feedback for Al-Ikhlas.
English phonetics first; Arabic lightly in brackets.

Beginner journey: stage ladder (isolate → join → full).
  One NEXT STEP inside the current stage.
  Forward only when the stage passes; step back if an earlier piece breaks.
  Micro-drills (Qu / ul) use syllable scoring before full Qul.
"""
import coaching as coach
import stages as stg

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
    stage_id=None,
):
    spec = VERSE_ELEMENTS.get(verse, {})
    stage = stg.get_stage(verse, stage_id)
    stage_words = list((stage or {}).get("words") or [])
    drill = (stage or {}).get("drill")
    stage_info = stg.stage_public(verse, (stage or {}).get("id"))
    focus_word = (stage or {}).get("focus_word") or (
        (stage_words[0] if stage_words else "") or ""
    )

    ok_cards = []
    errors = []
    tips = []

    # Syllable micro-drills: Qu / ul — do not score against full ayah words.
    if drill:
        ev = coach.evaluate_drill(
            drill, verse, heard_arabic or "", heard_phonetic or ""
        )
        errors.extend(ev.get("cards") or [])
        blocking = [c for c in errors if c.get("level") == "error"]
        stage_passed = bool(ev.get("passed")) and not blocking
        miss_words: list[str] = []
        regress_to = None
        return _finish_stage_cards(
            verse=verse,
            stage=stage,
            stage_info=stage_info,
            stage_words=stage_words,
            focus_word=focus_word,
            errors=errors,
            tips=tips,
            ok_cards=ok_cards,
            blocking=blocking,
            miss_words=miss_words,
            stage_passed=stage_passed,
            regress_to=regress_to,
            mastered=mastered,
            last_focus=last_focus,
        )

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
            coach.coach_from_heard(
                verse,
                heard_arabic,
                heard_phonetic or "",
                stage_words=stage_words or None,
            )
        )

    for (letter, wen, war, desc, lo, hi, pri) in spec.get("madd", []):
        if stage_words and not stg.word_in_stage(wen, stage):
            continue
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
            # Madd is polish — tip only, does not block stage advance.
            tips.append(coach.madd_short_card(verse, wen, war, seg, pri))

    for (letter, wen, war, desc, pri) in spec.get("shadda", []):
        if stage_words and not stg.word_in_stage(wen, stage):
            continue
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
    q_en = "aḥad"
    if verse == 2:
        q_en = "aṣ-ṣamad"
    elif verse == 3:
        q_en = "yalid"
    q_in_stage = (not stage_words) or stg.word_in_stage(q_en, stage)

    if qalqalah_result and q_in_stage:
        lvl = qalqalah_result.get("level")
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
            # Soft practice tip — does not block stage advance alone.
            tips.append(coach.ahad_bounce_card(verse, priority=qpri + 10))

    errors = sorted(errors, key=coach._issue_sort_key)
    tips = sorted(tips, key=lambda x: x.get("priority", 50))

    # Stage pass: no blocking errors (shape / identity / pronunciation / hard qalqalah).
    blocking = [c for c in errors if c.get("level") == "error"]
    kinds = coach.stage_word_kinds(
        verse, heard_arabic or "", heard_phonetic or "", stage_words or None
    )
    miss_words = [en for en, k in kinds.items() if k == "miss"]

    # If a join stage breaks an earlier locked word, step back.
    regress_to = None
    if miss_words and stage and len(stage.get("words") or []) > 1:
        regress_to = stg.earliest_failing_stage(verse, miss_words)
        if regress_to and regress_to.get("id") == stage.get("id"):
            regress_to = None

    # Full Qul still showing English K → step back to Qu onset drill.
    if (
        not regress_to
        and stage
        and stage.get("id") == "qul"
        and any(
            c.get("heard_letter") == "ك" and c.get("expected_letter") == "ق"
            for c in blocking
        )
    ):
        regress_to = stg.get_stage(verse, "qu")

    stage_passed = not blocking and not miss_words
    return _finish_stage_cards(
        verse=verse,
        stage=stage,
        stage_info=stage_info,
        stage_words=stage_words,
        focus_word=focus_word,
        errors=errors,
        tips=tips,
        ok_cards=ok_cards,
        blocking=blocking,
        miss_words=miss_words,
        stage_passed=stage_passed,
        regress_to=regress_to,
        mastered=mastered,
        last_focus=last_focus,
    )


def _finish_stage_cards(
    *,
    verse,
    stage,
    stage_info,
    stage_words,
    focus_word,
    errors,
    tips,
    ok_cards,
    blocking,
    miss_words,
    stage_passed,
    regress_to,
    mastered,
    last_focus,
):
    cards = []
    cards.extend(errors)
    cards.extend(tips)

    nxt_stage = stg.next_stage(verse, (stage or {}).get("id")) if stage_passed else None
    say = (stage or {}).get("say_en") or focus_word or "this"
    say_ar = (stage or {}).get("say_ar") or ""

    if regress_to and not stage_passed:
        cards.append({
            "level": "next",
            "rule": "next_step",
            "tag": "STEP BACK",
            "key": f"stage:{regress_to['id']}",
            "priority": 0,
            "section": coach.section_html(
                verse, (regress_to.get("focus_word") or (regress_to.get("words") or [""])[0])
            ),
            "plain": (
                f"<b>Step back:</b> {regress_to['say_en']} needs locking again "
                f"before this join.<br>"
                f"Say only <b>{regress_to['say_en']}</b> "
                f"<span class=\"arlight\">({regress_to['say_ar']})</span>."
            ),
            "fix": regress_to.get("hint"),
            "scholarly": None,
            "stage_id": regress_to["id"],
            "stage_action": "regress",
            "stage": stage_info,
        })
    elif stage_passed and nxt_stage:
        cards.append({
            "level": "next",
            "rule": "next_step",
            "tag": "STAGE CLEAR",
            "key": f"stage:{stage['id']}:clear",
            "priority": 0,
            "section": coach.section_html(
                verse,
                (nxt_stage.get("focus_word") or (nxt_stage.get("words") or [""])[0]),
            ),
            "plain": (
                f"<b>Locked:</b> {stage['say_en']}. "
                f"Next stage — say <b>{nxt_stage['say_en']}</b> "
                f"<span class=\"arlight\">({nxt_stage['say_ar']})</span>."
            ),
            "fix": nxt_stage.get("hint"),
            "scholarly": None,
            "stage_id": nxt_stage["id"],
            "stage_action": "advance",
            "stage": stage_info,
        })
    elif stage_passed and not nxt_stage:
        cards.append({
            "level": "next",
            "rule": "next_step",
            "tag": "AYAH CLEAR",
            "key": "ayah_clear",
            "priority": 0,
            "section": coach.section_html(verse, focus_word or ""),
            "plain": (
                "<b>Nice — this ayah’s stages are locked.</b> "
                "When you’re happy with it, move to the next ayah."
            ),
            "fix": None,
            "scholarly": None,
            "stage_id": (stage or {}).get("id"),
            "stage_action": "complete",
            "stage": stage_info,
        })
    else:
        issues = blocking + tips
        nxt = coach.pick_next_step(issues, mastered=mastered, last_focus=last_focus)
        if nxt:
            nxt["stage"] = stage_info
            nxt["stage_id"] = (stage or {}).get("id")
            nxt["stage_action"] = "stay"
            plain = nxt.get("plain") or ""
            plain = plain.replace("on the ayah)", "in this stage)")
            nxt["plain"] = plain
            cards.append(nxt)
        elif not issues:
            cards.append({
                "level": "next",
                "rule": "next_step",
                "tag": "NEXT STEP",
                "key": f"stage:{(stage or {}).get('id')}",
                "section": coach.section_html(verse, focus_word or ""),
                "plain": (
                    f"<b>Try again:</b> say only <b>{say}</b> "
                    f"<span class=\"arlight\">({say_ar})</span>."
                ),
                "fix": (stage or {}).get("hint"),
                "scholarly": None,
                "stage_id": (stage or {}).get("id"),
                "stage_action": "stay",
                "stage": stage_info,
            })

    cards.extend(ok_cards)

    # Attach stage meta on first diagnostic card for the client
    meta = {
        "stage": stage_info,
        "stage_passed": stage_passed,
        "stage_action": (
            "regress" if regress_to and not stage_passed
            else ("advance" if stage_passed and nxt_stage
                  else ("complete" if stage_passed else "stay"))
        ),
        "next_stage_id": (
            (regress_to or {}).get("id") if regress_to and not stage_passed
            else ((nxt_stage or {}).get("id") if stage_passed and nxt_stage
                  else (stage or {}).get("id"))
        ),
    }
    if cards:
        cards[0] = {**cards[0], **meta}
    else:
        cards.append({**meta, "level": "ok", "rule": "stage", "plain": ""})
    return cards


def _letter_span(letters, target):
    for i, l in enumerate(letters):
        if l["c"] == target:
            if i + 1 < len(letters):
                return round(letters[i + 1]["t"] - l["t"], 3)
    return None
