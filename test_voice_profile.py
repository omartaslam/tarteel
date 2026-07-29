"""Speaker-relative acoustic baselines — gray-zone only, absolute gates win."""
import voice_profile as vp
import coaching as coach


def test_empty_profile_is_safe():
    assert vp.parse_profile(None)["qaf_good"] == []
    assert vp.parse_profile("nope")["version"] == 1
    assert vp.relative_qaf_hint({"p_qaf": 0.5, "p_kaf": 0.4}, None) is None


def test_absolute_clear_qaf_never_uses_relative():
    """A clear absolute pass must ignore a hostile bad-cluster profile."""
    probe = {"p_qaf": 1.0, "p_kaf": 0.0, "onset": "قل"}
    # Profile that would claim everything is kaf if relative ran first.
    bad_prof = {
        "version": 1,
        "qaf_good": [],
        "qaf_bad": [{"p_qaf": 0.9, "p_kaf": 0.1}] * 3,
        "letters": {},
    }
    v = vp.resolve_qaf_verdict(probe, bad_prof)
    assert v["has_qaf"] is True
    assert v["has_kaf"] is False
    assert v["source"] == "absolute"


def test_absolute_clear_kaf_never_rescued_by_relative():
    probe = {"p_qaf": 0.0, "p_kaf": 1.0, "onset": "كل"}
    good_prof = {
        "version": 1,
        "qaf_good": [{"p_qaf": 0.95, "p_kaf": 0.05}] * 3,
        "qaf_bad": [],
        "letters": {},
    }
    v = vp.resolve_qaf_verdict(probe, good_prof)
    assert v["has_kaf"] is True
    assert v["has_qaf"] is False
    assert v["source"] == "absolute"


def test_silence_not_rescued_by_sparse_profile():
    probe = {"p_qaf": 0.0, "p_kaf": 0.0, "onset": ""}
    prof = {
        "version": 1,
        "qaf_good": [{"p_qaf": 0.9, "p_kaf": 0.05}, {"p_qaf": 0.95, "p_kaf": 0.0}],
        "qaf_bad": [{"p_qaf": 0.05, "p_kaf": 0.9}, {"p_qaf": 0.0, "p_kaf": 0.95}],
        "letters": {},
    }
    v = vp.resolve_qaf_verdict(probe, prof)
    assert v["has_qaf"] is False
    assert v["has_kaf"] is False


def test_gray_zone_matches_learner_good_cluster():
    # Absolute needs p_qaf>=0.60 & p_kaf<=0.30 (or onset letter). This is neither.
    probe = {"p_qaf": 0.48, "p_kaf": 0.35, "onset": "هو"}
    abs_v = coach.onset_qaf_verdict(probe)
    assert abs_v["has_qaf"] is False and abs_v["has_kaf"] is False

    prof = {
        "version": 1,
        "qaf_good": [
            {"p_qaf": 0.50, "p_kaf": 0.32},
            {"p_qaf": 0.46, "p_kaf": 0.36},
            {"p_qaf": 0.49, "p_kaf": 0.34},
        ],
        "qaf_bad": [
            {"p_qaf": 0.15, "p_kaf": 0.70},
            {"p_qaf": 0.10, "p_kaf": 0.80},
        ],
        "letters": {},
    }
    v = vp.resolve_qaf_verdict(probe, prof)
    assert v["has_qaf"] is True
    assert v["has_kaf"] is False
    assert v["source"] == "speaker_relative"


def test_gray_zone_matches_learner_bad_cluster():
    probe = {"p_qaf": 0.35, "p_kaf": 0.48, "onset": "هو"}
    abs_v = coach.onset_qaf_verdict(probe)
    assert abs_v["has_qaf"] is False and abs_v["has_kaf"] is False

    prof = {
        "version": 1,
        "qaf_good": [
            {"p_qaf": 0.90, "p_kaf": 0.05},
            {"p_qaf": 0.85, "p_kaf": 0.10},
        ],
        "qaf_bad": [
            {"p_qaf": 0.32, "p_kaf": 0.50},
            {"p_qaf": 0.36, "p_kaf": 0.46},
            {"p_qaf": 0.30, "p_kaf": 0.52},
        ],
        "letters": {},
    }
    v = vp.resolve_qaf_verdict(probe, prof)
    assert v["has_kaf"] is True
    assert v["has_qaf"] is False
    assert v["source"] == "speaker_relative"


def test_record_label_builds_qaf_and_letter_buckets():
    prof = vp.empty_profile()
    snap_good = {
        "p_qaf": 0.9,
        "p_kaf": 0.05,
        "evidence": {"ح": 0.95, "ل": 0.8},
        "stage_id": "qul",
        "verse": 1,
    }
    snap_bad = {
        "p_qaf": 0.1,
        "p_kaf": 0.9,
        "evidence": {"ح": 0.1, "ل": 0.05},
        "stage_id": "qul",
        "verse": 1,
    }
    prof = vp.record_label(prof, "correct", snap_good)
    prof = vp.record_label(prof, "wrong", snap_bad)
    assert len(prof["qaf_good"]) == 1
    assert len(prof["qaf_bad"]) == 1
    assert prof["letters"]["ل"]["good"] == [0.8]
    assert prof["letters"]["ل"]["bad"] == [0.05]

    # aḥad teaches ح
    snap_h = {
        "p_qaf": 0.0,
        "p_kaf": 0.0,
        "evidence": {"ح": 0.88},
        "stage_id": "ahad",
        "verse": 1,
    }
    prof = vp.record_label(prof, "correct", snap_h)
    assert prof["letters"]["ح"]["good"] == [0.88]


def test_unsure_does_not_pollute_profile():
    prof = vp.empty_profile()
    snap = {"p_qaf": 0.9, "p_kaf": 0.0, "stage_id": "qul", "verse": 1, "evidence": {}}
    out = vp.record_label(prof, "unsure", snap)
    assert out["qaf_good"] == []
    assert out["qaf_bad"] == []


def test_key_letter_soft_pass_from_learner_goods():
    # Absolute floor is 0.45 — 0.38 would fail without a profile.
    assert vp.key_letter_relative_ok("ح", 0.38, None) is False
    prof = {
        "version": 1,
        "qaf_good": [],
        "qaf_bad": [],
        "letters": {
            "ح": {
                "good": [0.50, 0.52, 0.48],
                "bad": [0.05, 0.10],
            }
        },
    }
    assert vp.key_letter_relative_ok("ح", 0.38, prof) is True
    assert vp.key_letter_relative_ok("ح", 0.10, prof) is False


def test_drill_qu_gray_zone_rescued_by_profile():
    probe = {"p_qaf": 0.48, "p_kaf": 0.35, "onset": "هو"}
    prof = {
        "version": 1,
        "qaf_good": [
            {"p_qaf": 0.50, "p_kaf": 0.32},
            {"p_qaf": 0.46, "p_kaf": 0.36},
        ],
        "qaf_bad": [
            {"p_qaf": 0.1, "p_kaf": 0.8},
            {"p_qaf": 0.15, "p_kaf": 0.7},
        ],
        "letters": {},
    }
    # Whisper wrote kaf — absolute onset is ambiguous; profile should rescue.
    without = coach.evaluate_drill("qu", 1, "كُ", "Ku", onset_probe=probe)
    assert without["passed"] is False
    with_p = coach.evaluate_drill(
        "qu", 1, "كُ", "Ku", onset_probe=probe, voice_profile=prof
    )
    assert with_p["passed"] is True
    assert with_p.get("qaf_rescue") is True
