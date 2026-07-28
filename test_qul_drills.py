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
    cards = build_feedback(
        1, [], None, heard_arabic="قُ", heard_phonetic="Qu", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "ul"


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
