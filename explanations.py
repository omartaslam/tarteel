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
    letter, name, word = QALQALAH_LETTER.get(verse, ("د","dal","the final letter"))
    if verdict == "correct":
        return {
            "level": "ok",
            "plain": f"Qalqalah on the {name} ({letter}) in {word} — good.",
            "scholarly": None,
        }
    if verdict == "error":
        soft = (p_error is not None and confidence < 0.70)
        tip = (f"The qalqalah bounce on the {name} ({letter}) in {word} "
               f"isn't clear. On your next try: stop on the {name}, then give it "
               f"a light echo — like a small bounce off the letter — not a flat stop.")
        return {
            "level": "error",
            "plain": (("Likely issue — " if soft else "") + tip),
            "scholarly": f"Qalqalah ({GLOSSARY['qalqalah']}). The letter {letter} "
                         f"carries sukun at the verse end, so it takes qalqalah kubra "
                         f"(the stronger bounce at a stop).",
            "verdict": "error",
        }
    # deferred — low confidence both ways
    return {
        "level": "defer",
        "plain": f"Not sure about the qalqalah on the {name} ({letter}) in {word}. "
                 f"Check this one with your teacher.",
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
