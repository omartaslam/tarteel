"""Unit tests for Ku / ul micro-drill scoring and stage ladder."""
from elements import build_feedback
from stages import earliest_failing_stage, get_stage, list_stages
import coaching as coach


def test_verse1_starts_with_qu_ul_qul():
    ids = [s["id"] for s in list_stages(1)]
    assert ids[:3] == ["qu", "ul", "qul"]
    assert get_stage(1, "qu")["drill"] == "qu"
    assert get_stage(1, "ul")["drill"] == "ul"
    assert get_stage(1, "qul").get("drill") is None


def test_ku_pass_on_kaf():
    # Shape-first: English K onset is enough to lock Ku.
    ev = coach.evaluate_drill("qu", 1, "كُ", "ku")
    assert ev["passed"] is True


def test_ku_pass_on_qaf():
    ev = coach.evaluate_drill("qu", 1, "قُ", "qu")
    assert ev["passed"] is True
    assert ev["cards"] == []


def test_ku_fail_without_onset():
    ev = coach.evaluate_drill("qu", 1, "ا", "ah")
    assert ev["passed"] is False


def test_ul_pass_on_lam():
    ev = coach.evaluate_drill("ul", 1, "ل", "ul")
    assert ev["passed"] is True


def test_ul_fail_without_l():
    ev = coach.evaluate_drill("ul", 1, "أ", "ah")
    assert ev["passed"] is False


def test_build_feedback_ku_advances_on_kul():
    # Latest live takes were heard as Kul — must advance past Ku.
    cards = build_feedback(
        1, [], None, heard_arabic="كُل", heard_phonetic="Kul", stage_id="qu"
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "ul"


def test_build_feedback_qul_near_kul_advances():
    # كل ≈ قل (near). ك→ق is polish tip, must not block stage.
    cards = build_feedback(
        1,
        [{"c": "ك", "t": 0.0}, {"c": "ل", "t": 0.2}],
        None,
        heard_arabic="كل",
        heard_phonetic="kul",
        stage_id="qul",
    )
    assert cards[0].get("stage_passed") is True
    assert cards[0].get("stage_action") == "advance"
    assert cards[0].get("next_stage_id") == "huwa"
    # Polish tip still present
    tips = [c for c in cards if c.get("rule") == "pronunciation"]
    assert tips and tips[0].get("level") == "measured"


def test_earliest_fail_qul_goes_to_qu():
    s = earliest_failing_stage(1, ["qul"])
    assert s and s["id"] == "qu"
