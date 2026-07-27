"""
Pre-written feedback for Al-Ikhlas. No LLM at runtime — lookup + fill measured
numbers. Keyed by (rule, verdict). Scholarly footnote auto-appended.

Layered format agreed with Tanveer:
  plain instruction (with measured numbers) + scholarly footnote
Terms glossed in brackets on first use via GLOSSARY.
"""

GLOSSARY = {
    "qalqalah": "a slight echo/bounce on certain letters when they carry sukun",
    "madd": "elongation — holding a vowel longer than normal",
    "sukun": "a letter with no vowel, pronounced 'still'",
    "harakat": "beats — the unit of elongation length",
}

# The qalqalah letters ending Al-Ikhlas verses
QALQALAH_LETTER = {
    1: ("د", "dal", "أَحَدٌ / ahad"),
    2: ("د", "dal", "ٱلصَّمَدُ / as-samad"),
    3: ("د", "dal", "يُولَدْ / yoolad"),
    4: ("د", "dal", "أَحَدٌ / ahad"),
}

def qalqalah_feedback(verse, verdict, confidence, p_error=None):
    # English-first labels; elements/coaching rewrite the learner-facing cards.
    en = {1: "aḥad", 2: "aṣ-ṣamad", 3: "yalid", 4: "aḥad"}.get(verse, "the word")
    ar = {1: "أَحَدٌ", 2: "ٱلصَّمَدُ", 3: "يَلِدْ", 4: "أَحَدٌ"}.get(verse, "")
    if verdict == "correct":
        return {
            "level": "ok",
            "plain": (
                f"On {en} <span class=\"arlight\">({ar})</span>: "
                f"the final D bounce sounded good."
            ),
            "scholarly": None,
            "verdict": "correct",
        }
    if verdict == "error":
        soft = (p_error is not None and confidence < 0.70)
        return {
            "level": "error",
            "plain": (
                f"{'Likely: ' if soft else ''}"
                f"On {en} <span class=\"arlight\">({ar})</span>: "
                f"the bounce on the final D wasn’t clear."
            ),
            "fix": "Stop on the D, then a light echo — not a flat stop.",
            "scholarly": f"Qalqalah ({GLOSSARY['qalqalah']}).",
            "verdict": "error",
        }
    return {
        "level": "defer",
        "plain": f"Not sure about the final D bounce on {en} yet.",
        "scholarly": None,
        "verdict": "defer",
    }

def madd_feedback(word, measured_s, target_s, beats):
    if measured_s >= target_s * 0.8:
        return {"level":"ok",
                "plain": f"Madd in {word} held well ({measured_s:.1f}s).",
                "scholarly": None}
    return {
        "level": "measured",  # measured but not validated
        "plain": f"The elongation in {word} looks short — held {measured_s:.1f}s, "
                 f"aim for about {target_s:.1f}s ({beats} beats).",
        "scholarly": f"Madd ({GLOSSARY['madd']}) — {beats} harakat "
                     f"({GLOSSARY['harakat']}). Measured acoustically; not yet "
                     f"validated, treat as a prompt not a verdict.",
    }
