"""
Per-element feedback for Al-Ikhlas.
English phonetics first; Arabic lightly in brackets.

Beginner journey: stage ladder (isolate → join → full).
  One FOCUS tip inside the current stage (not stage advance).
  Green “Stage cleared · next step” + Hear only {next word} only after a lock.
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
    locked_stages=None,
    qu_bridge_attempt=None,
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
    # Optional Qul bridge on Qu: same ق/ك gate, up to 6 tries, then tutor defer.
    if drill:
        if drill == "qu" and qu_bridge_attempt:
            ev = coach.evaluate_qu_qul_bridge(
                verse,
                heard_arabic or "",
                heard_phonetic or "",
                attempt=qu_bridge_attempt,
            )
        else:
            ev = coach.evaluate_drill(
                drill,
                verse,
                heard_arabic or "",
                heard_phonetic or "",
            )
        errors.extend(ev.get("cards") or [])
        # defer blocks advance (no false lock) but still feeds next-step coaching
        blocking = [c for c in errors if c.get("level") in ("error", "defer")]
        stage_passed = bool(ev.get("passed")) and not blocking
        miss_words: list[str] = []
        regress_to = None
        cards = _finish_stage_cards(
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
            locked_stages=locked_stages,
        )
        # Honest drill display — never show Whisper's invented full word.
        disp = {
            "heard_arabic": ev.get("display_arabic", ""),
            "heard_phonetic": ev.get("display_phonetic", ""),
            "compare_html": ev.get("compare_html", ""),
            "heard_match": ev.get("heard_match", "drill"),
            "matched_arabic": "",
            "matched_phonetic": "",
        }
        if ev.get("bridge"):
            disp["bridge"] = ev["bridge"]
        if cards:
            cards[0] = {**cards[0], **disp}
            # Bridge pass: make the STAGE CLEAR line name the bridge win.
            if stage_passed and ev.get("bridge") and cards[0].get("stage_action") == "advance":
                cards[0]["plain"] = (
                    "<b>Locked Qu</b> from your Qul try (heard back ق). "
                    "Next stage — say <b>ul</b> "
                    "<span class=\"arlight\">(ـُلْ)</span>."
                )
        return cards

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

    # Re-said a locked earlier word (e.g. Qul again while on huwa) — don't
    # show a confusing "huwa miss / heard —" when the panel shows correct Qul.
    earlier = coach.detect_repeated_earlier_word(
        verse, stage, heard_arabic or "", heard_phonetic or ""
    )
    if earlier and stage:
        cur_set = {(w or "").lower() for w in (stage_words or [])}
        errors = [
            e
            for e in errors
            if not (
                e.get("rule") == "word_shape"
                and (e.get("word_en") or "").lower() in cur_set
            )
        ]
        errors.insert(0, coach.wrong_stage_repeat_card(verse, stage, earlier))

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

    # Stage pass: misses + real pronunciation faults (ك→ق etc.) block.
    # Analyse this take — do not demote throat-Q errors to soft tips.
    kinds = coach.stage_word_kinds(
        verse, heard_arabic or "", heard_phonetic or "", stage_words or None
    )
    miss_words = [en for en, k in kinds.items() if k == "miss"]

    def _blocks_stage(c: dict) -> bool:
        if c.get("level") != "error":
            return False
        rule = c.get("rule") or ""
        if rule in ("drill", "word_shape", "pronunciation", "qalqalah", "wrong_stage"):
            return True
        return not rule

    blocking = [c for c in errors if _blocks_stage(c)]

    # Word-first Qul: stay on Qul when ك — do NOT auto-drop to Qu on first miss.
    # Client moves to syllable rescue (Qu) only after 3 word fails.
    regress_to = None
    if miss_words and stage and len(stage.get("words") or []) > 1:
        regress_to = stg.earliest_failing_stage(verse, miss_words)
        if regress_to and regress_to.get("id") == stage.get("id"):
            regress_to = None

    stage_passed = not blocking and not miss_words

    # Qul lock requires Arabic ق in this take (same stable gate as Qu drill).
    # Shape-near without ق (طل, garbled Whisper, etc.) must NOT skip to huwa.
    needs_qaf = (stage or {}).get("id") == "qul" or (
        {(w or "").lower() for w in (stage_words or [])} == {"qul"}
    )
    if stage_passed and needs_qaf and "ق" not in (heard_arabic or ""):
        stage_passed = False
        q_err = coach._card(
            5,
            verse,
            "qul",
            "قُلْ",
            {
                "heard": "no clear back Q (qaf) in this take",
                "want": "Arabic Qul — English cue <b>QUAL</b> like <b>quality</b>",
                "fix": (
                    "Say the full word <b>Qul</b> (قُلْ). Think <b>QUAL</b> like the start of "
                    "<b>quality</b> — not “cull/cool”. I need to hear back <b>ق</b>."
                ),
                "ar": ("?", "ق"),
            },
            "?",
            "ق",
            rule="pronunciation",
        )
        q_err["key"] = "pronunciation:qul:need_ق"
        errors.insert(0, q_err)
        blocking = [c for c in errors if _blocks_stage(c)]

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
        locked_stages=locked_stages,
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
    locked_stages=None,
):
    cards = []
    cards.extend(errors)
    cards.extend(tips)

    nxt_stage = stg.next_stage(verse, (stage or {}).get("id")) if stage_passed else None
    # Word-first: locking full Qul skips syllable rescue → huwa.
    if stage_passed and (stage or {}).get("id") == "qul":
        nxt_stage = stg.get_stage(verse, "huwa")
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
        stage_n = ((stage_info or {}).get("index") or 0) + 1
        cards.append({
            "level": "next",
            "rule": "next_step",
            "tag": f"STAGE {stage_n} CLEARED",
            "key": f"stage:{stage['id']}:clear",
            "priority": 0,
            "section": coach.section_html(
                verse,
                (nxt_stage.get("focus_word") or (nxt_stage.get("words") or [""])[0]),
            ),
            "plain": (
                f"<b>Stage {stage_n} cleared:</b> {stage['say_en']}. "
                f"<b>Next step</b> — say only <b>{nxt_stage['say_en']}</b> "
                f"<span class=\"arlight\">({nxt_stage['say_ar']})</span>."
            ),
            "fix": nxt_stage.get("hint"),
            "scholarly": None,
            "stage_id": nxt_stage["id"],
            "stage_action": "advance",
            "stage": stage_info,
            "lock_also": (
                ["qu", "ul"] if (stage or {}).get("id") == "qul" else []
            ),
            "next_say_en": nxt_stage.get("say_en"),
            "next_say_ar": nxt_stage.get("say_ar"),
            "next_hint": nxt_stage.get("hint"),
            "cleared_stage_n": stage_n,
            "cleared_stage_id": (stage or {}).get("id"),
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
        nxt = coach.pick_next_step(
            issues,
            mastered=mastered,
            last_focus=last_focus,
            locked_stages=locked_stages,
        )
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
                "tag": "FOCUS",
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
