"""Unit tests: word-first Qul; Qu requires back ق; middle ك must fail."""
import pytest

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


def test_qu_pass_on_qhul_phonetics_without_arabic_qaf():
    """Hollow qh/QUAL in English phonetics must count — teach ↔ measure."""
    ev = coach.evaluate_drill("qu", 1, "", "Qhul")
    assert ev["passed"] is True
    ev2 = coach.evaluate_drill("qu", 1, "", "Qual")
    assert ev2["passed"] is True
    # Still never pass clear kaf
    ev3 = coach.evaluate_drill("qu", 1, "كُ", "Qhul")
    assert ev3["passed"] is False


def test_romanize_qaf_shows_qul_label():
    from transcribe_quran import romanize_ar
    assert romanize_ar("قُلْ") == "Qul"
    assert romanize_ar("قُ") == "Qu"
    assert romanize_ar("كُلّ") == "Kull"


def test_qu_fail_on_kaf():
    # Middle ك must NOT pass — that was the cheating bug.
    ev = coach.evaluate_drill("qu", 1, "كُ", "ku")
    assert ev["passed"] is False
    assert ev["display_phonetic"] == "Ku"
    assert ev["cards"] and ev["cards"][0]["expected_letter"] == "ق"
    assert ev["cards"][0]["key"] == "drill:qu:ق"


def test_qu_phone_asr_flatten_rescued_by_align_qaf():
    """Whisper ك + acoustic onset ق → pass (phone audience must not be locked out)."""
    ev = coach.evaluate_drill(
        "qu", 1, "كُ", "Ku", onset_probe={"p_qaf": 0.99, "p_kaf": 0.00, "onset": "قل"}
    )
    assert ev["passed"] is True
    assert ev["display_arabic"] == "قُ"
    assert ev.get("qaf_rescue") is True


def test_qu_align_kaf_still_fails():
    ev = coach.evaluate_drill(
        "qu", 1, "كُ", "Ku", onset_probe={"p_qaf": 0.00, "p_kaf": 0.97, "onset": "كل"}
    )
    assert ev["passed"] is False


def test_no_acoustic_evidence_never_rescues():
    """Silence and noise score ~0 on both letters — that must not pass as ق."""
    for probe in (None, {"p_qaf": 0.0, "p_kaf": 0.0, "onset": ""}):
        v = coach.onset_qaf_verdict(probe)
        assert v["has_qaf"] is False and v["has_kaf"] is False
        assert coach.evaluate_drill("qu", 1, "كُ", "Ku", onset_probe=probe)["passed"] is False


def test_onset_verdict_thresholds():
    strong_q = coach.onset_qaf_verdict({"p_qaf": 1.0, "p_kaf": 0.0})
    strong_k = coach.onset_qaf_verdict({"p_qaf": 0.0, "p_kaf": 0.97})
    ambiguous = coach.onset_qaf_verdict({"p_qaf": 0.55, "p_kaf": 0.45})
    assert strong_q["has_qaf"] is True and strong_q["has_kaf"] is False
    assert strong_k["has_kaf"] is True and strong_k["has_qaf"] is False
    # Never lock a stage on a coin-flip onset.
    assert ambiguous["has_qaf"] is False and ambiguous["has_kaf"] is False


def test_qul_phone_asr_flatten_rescued_by_acoustic_qaf():
    """Whisper flattened ق→ك but the onset really is ق — phone users must pass."""
    cards = build_feedback(
        1,
        [],
        None,
        heard_arabic="كُلّ",
        heard_phonetic="Kull",
        stage_id="qul",
        onset_probe={"p_qaf": 1.0, "p_kaf": 0.0, "onset": "قل"},
    )
    assert cards and cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "huwa"


def test_qul_kaf_without_acoustic_qaf_must_fail():
    """The live bug: Whisper ك used to be rescued by forced-aligned letters.

    Forced alignment can only emit the expected ayah, so it "found" ق in the
    kaf benchmark, in white noise and in silence. With no acoustic ق, a ك take
    must fail.
    """
    for probe in (
        None,
        {"p_qaf": 0.0, "p_kaf": 0.97, "onset": "كل"},   # kaf benchmark
        {"p_qaf": 0.0, "p_kaf": 0.0, "onset": ""},      # silence / noise
    ):
        cards = build_feedback(
            1, [], None, heard_arabic="كُلّ", heard_phonetic="Kull",
            stage_id="qul", onset_probe=probe,
        )
        assert cards[0].get("stage_passed") is False, probe
        assert cards[0].get("stage_action") != "advance", probe


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


def test_qul_near_without_qaf_does_not_pass():
    """Shape-near garbage/ط must not lock Qul — stable gate needs ق."""
    for ar, ph in [("طل", "Ṭl"), ("لل", "ll")]:
        cards = build_feedback(
            1, [], None, heard_arabic=ar, heard_phonetic=ph, stage_id="qul"
        )
        assert cards[0].get("stage_passed") is False, (ar, ph)
        assert any("need_ق" in (c.get("key") or "") for c in cards)


def test_compare_html_stage_only_marks_qul_not_whole_ayah():
    """One-word Qul fail must not yellow the entire ayah as 'needs work'."""
    html = coach.compare_html(1, "كل", "Kull", stage_words=["qul"])
    assert 'class="marky">Qul</span>' in html
    assert 'class="marky">قُلْ</span>' in html or "قُلْ" in html
    # Other ayah words must not appear as yellow targets
    low = html.lower()
    assert "huwa" not in low
    assert "allāhu" not in low and "allahu" not in low
    assert "aḥad" not in low and "ahad" not in low
    assert "this stage" in low


def test_compare_html_full_ayah_still_shows_all_words():
    html = coach.compare_html(1, "كل", "Kull", stage_words=None)
    assert "huwa" in html.lower() or "Huwa" in html
    assert "Qul" in html


def test_qu_section_highlights_onset_not_full_qul():
    html = coach.section_html(1, "qul", highlight="qu")
    assert "focusw" in html and "Qu" in html
    # Must not wrap the entire English Qul as one focus span
    assert '<span class="focusw">Qul</span>' not in html


def test_syllable_rescue_copy_says_qu_not_qul_only():
    ev = coach.evaluate_qu_qul_bridge(1, "كُ", "ku", attempt=2)
    plain = (ev["cards"][0].get("plain") or "") + (ev["cards"][0].get("fix") or "")
    assert "only" in plain.lower() and "Qu" in plain
    assert "quality" in plain.lower()
    assert "not full Qul" in plain or "not</b> say the full word" in plain
    assert "focusw\">Qu" in (ev["cards"][0].get("section") or "")


def test_qul_kaf_tip_teaches_qual_not_cull():
    tip = coach.FIX[("ك", "ق")]
    blob = (tip.get("want") or "") + (tip.get("fix") or "")
    assert "QUAL" in blob
    assert "quality" in blob.lower()
    assert "cull" in blob.lower() or "cool" in blob.lower()


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


@pytest.mark.parametrize(
    "label,heard_ar,heard_ph,stage,expect_pass",
    [
        # Documented live pass, HANDOVER §1 (session 20260728-140251).
        ("phone Qul Qawlahu", "قَوْلَهُ", "Qawlahu", "qul", True),
        ("clean Qul", "قل", "Qul", "qul", True),
        ("middle kaf never passes", "كُل", "Kul", "qul", False),
        ("huwa on huwa", "هُوَ", "huwa", "huwa", True),
        # These two were silently broken: the whole-ayah align let قل/هو eat
        # the letters, so a correct lone word missed on its own stage.
        ("Allahu on allahu", "اللَّهُ", "Allahu", "allahu", True),
        ("ahad on ahad", "أَحَدٌ", "ahad", "ahad", True),
    ],
)
def test_stage_detection_matrix_no_regression(label, heard_ar, heard_ph, stage, expect_pass):
    cards = build_feedback(
        1, [], None, heard_arabic=heard_ar, heard_phonetic=heard_ph,
        stage_id=stage, locked_stages=[],
    )
    passed = bool(cards and cards[0].get("stage_passed"))
    assert passed is expect_pass, f"{label}: stage_passed={passed}, expected {expect_pass}"


def test_allahu_is_not_false_wrong_stage_qul():
    """Allāhu letters must not left-align as near-Qul (wrong_stage:allahu:qul)."""
    # Same shape as the live false fail: heard panel shows Allahu / اللَّهُ
    # but FOCUS claimed “sounded like Qul again”.
    # Allāhu must score on its own stage instead of being eaten by قل / هو.
    assert coach.stage_word_kinds(1, "اللَّهُ", "Allahu", ["Allāhu"]) == {"Allāhu": "ok"}
    # قل stays a tolerant near (that tolerance is what keeps Qawlahu passing on
    # Qul) — so the wrong-stage claim must be gated on a clear ok, not on near.
    assert coach.stage_word_kinds(1, "اللَّهُ", "Allahu", ["qul"]) == {"qul": "near"}
    import stages as stg
    stage = next(s for s in stg.list_stages(1) if s["id"] == "allahu")
    assert coach.detect_repeated_earlier_word(1, stage, "اللَّهُ", "Allahu") is None
    cards = build_feedback(
        1,
        [],
        None,
        heard_arabic="اللَّهُ",
        heard_phonetic="Allahu",
        stage_id="allahu",
        locked_stages=["qul", "qu", "ul", "huwa", "qul_huwa"],
    )
    assert not any(c.get("rule") == "wrong_stage" for c in cards)
    assert not any(
        "wrong_stage:allahu:qul" == (c.get("key") or "") for c in cards
    )
    assert not any(
        "sounded like" in (c.get("plain") or "") and "Qul" in (c.get("plain") or "")
        for c in cards
    )
    assert not any(
        c.get("rule") == "word_shape" and "—" in (c.get("plain") or "")
        for c in cards
    )
    assert cards[0].get("stage_passed") is True



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
