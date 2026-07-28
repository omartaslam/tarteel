"""Unit tests for Qu / ul micro-drill scoring and stage ladder."""
from elements import build_feedback
from stages import earliest_failing_stage, get_stage, list_stages
import coaching as coach


def test_verse1_starts_with_qu_ul_qul():
    ids = [s["id"] for s in list_stages(1)]
    assert ids[:3] == ["qu", "ul", "qul"]
    assert get_stage(1, "qu")["drill"] == "qu"
    assert get_stage(1, "ul")["drill"] == "ul"
    assert get_stage(1, "qul").get("drill") is None


def test_qu_pass_on_qaf():
    ev = coach.evaluate_drill("qu", 1, "قُ", "qu")
    assert ev["passed"] is True
    assert ev["cards"] == []


def test_qu_fail_on_kaf():
    ev = coach.evaluate_drill("qu", 1, "كُ", "ku")
    assert ev["passed"] is False
    assert ev["cards"]
    assert ev["cards"][0]["expected_letter"] == "ق"


def test_ul_pass_on_lam():
    ev = coach.evaluate_drill("ul", 1, "ل", "ul")
    assert ev["passed"] is True


def test_ul_fail_without_l():
    ev = coach.evaluate_drill("ul", 1, "أ", "ah")
    assert ev["passed"] is False


def test_build_feedback_qu_advances():
    cards = build_feedback(
        1, [], None, heard_arabic="قو", heard_phonetic="qu", stage_id="qu"
    )
    meta = cards[0]
    assert meta.get("stage_passed") is True
    assert meta.get("stage_action") == "advance"
    assert meta.get("next_stage_id") == "ul"


def test_build_feedback_qu_stays_on_k():
    cards = build_feedback(
        1, [], None, heard_arabic="كُل", heard_phonetic="kul", stage_id="qu"
    )
    meta = next(c for c in cards if c.get("stage_action") or c.get("stage_passed") is not None)
    # meta is merged onto first card
    assert cards[0].get("stage_passed") is False
    assert cards[0].get("stage_action") == "stay"


def test_qul_kaf_regresses_to_qu():
    cards = build_feedback(
        1,
        [{"c": "ك", "t": 0.0}, {"c": "ل", "t": 0.2}],
        None,
        heard_arabic="كل",
        heard_phonetic="kul",
        stage_id="qul",
    )
    assert cards[0].get("stage_action") == "regress"
    assert cards[0].get("next_stage_id") == "qu"


def test_earliest_fail_qul_goes_to_qu():
    s = earliest_failing_stage(1, ["qul"])
    assert s and s["id"] == "qu"
