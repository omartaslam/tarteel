"""Unit tests: Qu requires back ق; middle ك must fail."""
from elements import build_feedback
from stages import earliest_failing_stage, get_stage, list_stages
import coaching as coach


def test_verse1_starts_with_qu_ul_qul():
    ids = [s["id"] for s in list_stages(1)]
    assert ids[:3] == ["qu", "ul", "qul"]
    assert get_stage(1, "qu")["drill"] == "qu"
    assert get_stage(1, "qu")["say_ar"] == "قُ"


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
    # Switching between unclear vs kaf must not say "deep Q is holding".
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
        mastered=["drill:qu:onset"],  # old variant
        last_focus="drill:qu:onset",
    )
    assert nxt is not None
    plain = nxt.get("plain") or ""
    assert "holding" not in plain.lower()
    assert "steadied" not in plain.lower()


def test_qu_fail_on_kul_whisper():
    # Incorrect bench-style take: كل/Kul → fail, show Ku not full word invent for target.
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


def test_build_feedback_qu_kaf_stays():
    cards = build_feedback(
        1, [], None, heard_arabic="كُل", heard_phonetic="Kul", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "stay"
    assert cards[0].get("heard_phonetic") == "Ku"


def test_build_feedback_qu_qaf_advances():
    # Without acoustic payload → ASR-letter gate (stable fallback).
    cards = build_feedback(
        1, [], None, heard_arabic="قُ", heard_phonetic="Qu", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "ul"


def test_qu_hybrid_pass_needs_acoustic_agreement():
    import qu_acoustic as qa

    ac = qa.score_path("data/qu_corpus/correct/qul_minshawi.wav")
    assert ac and ac.get("p_qaf") is not None
    ev = coach.evaluate_drill("qu", 1, "قُل", "Qul", acoustic=ac)
    assert ev["passed"] is True
    assert ev.get("qu_decision", {}).get("verdict") == "pass"


def test_qu_hybrid_defers_when_acoustic_unsure():
    thr = {
        "pass_p_hi": 0.82,
        "pass_p": 0.70,
        "pass_margin": 0.20,
        "fail_p_lo": 0.28,
        "fail_p": 0.40,
        "fail_margin": -0.30,
    }
    fake = {
        "p_qaf": 0.55,
        "margin": 0.0,
        "d_q": 1.0,
        "d_k": 1.0,
        "version": "test",
        "thresholds": thr,
    }
    cards = build_feedback(
        1,
        [],
        None,
        heard_arabic="قُ",
        heard_phonetic="Qu",
        stage_id="qu",
        qu_acoustic=fake,
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "stay"
    assert cards[0].get("level") in ("defer", "next")


def test_build_feedback_qul_kaf_blocks():
    # كل ≈ قل near, but ك→ق must block (and step back to Qu).
    cards = build_feedback(
        1,
        [{"c": "ك", "t": 0.0}, {"c": "ل", "t": 0.2}],
        None,
        heard_arabic="كل",
        heard_phonetic="kul",
        stage_id="qul",
    )
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "regress"
    assert cards[0].get("next_stage_id") == "qu"


def test_earliest_fail_qul_goes_to_qu():
    s = earliest_failing_stage(1, ["qul"])
    assert s and s["id"] == "qu"
