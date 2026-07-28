"""Unit tests: word-first Qul; Qu requires back ق; middle ك must fail."""
from elements import build_feedback
from stages import earliest_failing_stage, get_stage, list_stages
import coaching as coach


def test_verse1_starts_word_first():
    ids = [s["id"] for s in list_stages(1)]
    assert ids[:4] == ["qul", "qu", "ul", "huwa"]
    assert get_stage(1, "qu")["drill"] == "qu"
    assert get_stage(1, "qul")["say_ar"] == "قُلْ"


def test_qu_pass_on_qaf():
    ev = coach.evaluate_drill("qu", 1, "قُ", "qu")
    assert ev["passed"] is True
    assert ev["display_phonetic"] == "Qu"
    assert ev["display_arabic"] == "قُ"


def test_qu_fail_on_kaf():
    # Middle ك must NOT pass — that was the cheating bug.
    ev = coach.evaluate_drill("qu", 1, "كُ", "ku")
    assert ev["passed"] is False
    assert ev["display_phonetic"] == "Ku"
    assert ev["cards"] and ev["cards"][0]["expected_letter"] == "ق"
    assert ev["cards"][0]["key"] == "drill:qu:ق"


def test_next_step_does_not_claim_holding_on_same_qu_fault():
    err = {
        "level": "error",
        "rule": "drill",
        "key": "drill:qu:ق",
        "word_en": "Qu",
        "heard_letter": "ك",
        "expected_letter": "ق",
        "plain": "heard middle K",
        "fix": "use back Q",
        "priority": 5,
    }
    nxt = coach.pick_next_step(
        [err],
        mastered=["drill:qu:onset"],
        last_focus="drill:qu:onset",
    )
    assert nxt is not None
    plain = nxt.get("plain") or ""
    assert "holding" not in plain.lower()
    assert "steadied" not in plain.lower()


def test_qu_fail_on_kul_whisper():
    ev = coach.evaluate_drill("qu", 1, "كُل", "Kul")
    assert ev["passed"] is False
    assert ev["display_phonetic"] == "Ku"
    assert "ق" not in (ev.get("display_arabic") or "")


def test_qu_fail_without_onset():
    ev = coach.evaluate_drill("qu", 1, "ا", "ah")
    assert ev["passed"] is False


def test_ul_pass_on_lam():
    ev = coach.evaluate_drill("ul", 1, "ل", "ul")
    assert ev["passed"] is True


def test_ul_pass_on_whisper_variants():
    for ar, ph in [("قُلْ", "Qul"), ("كل", "Kul"), ("ول", "ul"), ("ـُل", "ool")]:
        ev = coach.evaluate_drill("ul", 1, ar, ph)
        assert ev["passed"] is True, (ar, ph)
        assert ev["display_phonetic"] == "ul"


def test_ul_fail_without_l():
    for ar, ph in [("قُ", "Qu"), ("كُ", "ku"), ("ا", "ah"), ("", "")]:
        ev = coach.evaluate_drill("ul", 1, ar, ph)
        assert ev["passed"] is False, (ar, ph)


def test_build_feedback_ul_advances_to_huwa():
    # After word-first reorder, ul → huwa (qul already tried first).
    cards = build_feedback(
        1, [], None, heard_arabic="ل", heard_phonetic="ul", stage_id="ul"
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "huwa"


def test_build_feedback_ul_stays_on_qu_onset():
    cards = build_feedback(
        1, [], None, heard_arabic="قُ", heard_phonetic="Qu", stage_id="ul"
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "stay"


def test_build_feedback_qu_kaf_stays():
    cards = build_feedback(
        1, [], None, heard_arabic="كُل", heard_phonetic="Kul", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "stay"
    assert cards[0].get("heard_phonetic") == "Ku"


def test_build_feedback_qu_qaf_advances():
    cards = build_feedback(
        1, [], None, heard_arabic="قُ", heard_phonetic="Qu", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "ul"


def test_qu_asr_qaf_locks_even_without_acoustic():
    cards = build_feedback(
        1, [], None, heard_arabic="قَوْمَا", heard_phonetic="qawma", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"


def test_build_feedback_qul_kaf_stays_word_first():
    # Word-first: ك on Qul stays (no instant regress to Qu).
    cards = build_feedback(
        1,
        [{"c": "ك", "t": 0.0}, {"c": "ل", "t": 0.2}],
        None,
        heard_arabic="كل",
        heard_phonetic="kul",
        stage_id="qul",
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "stay"


def test_build_feedback_qul_qaf_skips_to_huwa():
    cards = build_feedback(
        1,
        [{"c": "ق", "t": 0.0}, {"c": "ل", "t": 0.2}],
        None,
        heard_arabic="قل",
        heard_phonetic="Qul",
        stage_id="qul",
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "huwa"
    assert "qu" in (cards[0].get("lock_also") or [])
    assert "ul" in (cards[0].get("lock_also") or [])


def test_qul_again_on_huwa_is_wrong_stage_not_mystery_miss():
    """After Qul locks, re-saying Qul must not look like a broken huwa."""
    cards = build_feedback(
        1,
        [],
        None,
        heard_arabic="قل",
        heard_phonetic="Qul",
        stage_id="huwa",
        locked_stages=["qul", "qu", "ul"],
    )
    assert cards[0].get("stage_passed") is False
    err = next(c for c in cards if c.get("rule") == "wrong_stage")
    assert "Wrong word" in (err.get("plain") or "")
    assert "huwa" in (err.get("plain") or "").lower() or "huwa" in (err.get("fix") or "").lower()
    # Must not claim huwa was heard as "—"
    assert not any(
        c.get("rule") == "word_shape" and "—" in (c.get("plain") or "")
        for c in cards
    )


def test_stage_needs_qalqalah_only_on_bounce_word():
    from stages import stage_needs_qalqalah
    assert stage_needs_qalqalah(1, "qul") is False
    assert stage_needs_qalqalah(1, "huwa") is False
    assert stage_needs_qalqalah(1, "qu") is False
    assert stage_needs_qalqalah(1, "ahad") is True
    assert stage_needs_qalqalah(1, "full") is True
    assert stage_needs_qalqalah(1, None) is True


def test_earliest_fail_qul_goes_to_qu():
    s = earliest_failing_stage(1, ["qul"])
    assert s and s["id"] == "qu"


def test_syllable_rescue_pass_on_qaf():
    ev = coach.evaluate_qu_qul_bridge(1, "قُلْ", "Qul", attempt=1)
    assert ev["passed"] is True
    assert ev["bridge"]["verdict"] == "pass"
    cards = build_feedback(
        1, [], None, heard_arabic="قُلْ", heard_phonetic="Qul",
        stage_id="qu", qu_bridge_attempt=2,
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("next_stage_id") == "ul"


def test_syllable_rescue_kaf_never_passes():
    ev = coach.evaluate_qu_qul_bridge(1, "كُل", "Kul", attempt=1)
    assert ev["passed"] is False
    assert ev["bridge"]["verdict"] == "fail"


def test_syllable_rescue_third_fail_defers_to_tutor():
    ev = coach.evaluate_qu_qul_bridge(1, "كُ", "ku", attempt=3)
    assert ev["passed"] is False
    assert ev["bridge"]["verdict"] == "tutor"
    assert ev["cards"][0]["level"] == "defer"
    cards = build_feedback(
        1, [], None, heard_arabic="كُل", heard_phonetic="Kul",
        stage_id="qu", qu_bridge_attempt=3,
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("level") == "defer"
