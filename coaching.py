"""
Compare what Whisper heard vs the expected ayah → plain coaching.

Style for learners who aren't fluent in Arabic:
  English sound first, Arabic lightly in brackets.
One "Next step" at a time (left-to-right through the ayah).
"""
from __future__ import annotations

import re
import unicodedata

# (bare, english_word, arabic_display)
EXPECTED = {
    1: [
        ("قل", "qul", "قُلْ"),
        ("هو", "huwa", "هُوَ"),
        ("الله", "Allāhu", "ٱللَّهُ"),
        ("احد", "aḥad", "أَحَدٌ"),
    ],
    2: [
        ("الله", "Allāhu", "ٱللَّهُ"),
        ("الصمد", "aṣ-ṣamad", "ٱلصَّمَدُ"),
    ],
    3: [
        ("لم", "lam", "لَمْ"),
        ("يلد", "yalid", "يَلِدْ"),
        ("ولم", "wa lam", "وَلَمْ"),
        ("يولد", "yūlad", "يُولَدْ"),
    ],
    4: [
        ("ولم", "wa lam", "وَلَمْ"),
        ("يكن", "yakun", "يَكُن"),
        ("له", "lahu", "لَّهُ"),
        ("كفوا", "kufuwan", "كُفُوًا"),
        ("احد", "aḥad", "أَحَدٌ"),
    ],
}

# Full ayah lines for the in-card section (English-led).
AYAH_LINE = {
    1: {
        "ph": ["Qul", "huwa", "Allāhu", "aḥad"],
        "ar": ["قُلْ", "هُوَ", "ٱللَّهُ", "أَحَدٌ"],
        "key": ["qul", "huwa", "Allāhu", "aḥad"],
    },
    2: {
        "ph": ["Allāhu", "aṣ-ṣamad"],
        "ar": ["ٱللَّهُ", "ٱلصَّمَدُ"],
        "key": ["Allāhu", "aṣ-ṣamad"],
    },
    3: {
        "ph": ["Lam", "yalid", "wa lam", "yūlad"],
        "ar": ["لَمْ", "يَلِدْ", "وَلَمْ", "يُولَدْ"],
        "key": ["lam", "yalid", "wa lam", "yūlad"],
    },
    4: {
        "ph": ["Wa lam", "yakun", "lahu", "kufuwan", "aḥad"],
        "ar": ["وَلَمْ", "يَكُن", "لَّهُ", "كُفُوًا", "أَحَدٌ"],
        "key": ["wa lam", "yakun", "lahu", "kufuwan", "aḥad"],
    },
}


def section_html(verse: int, word_en: str) -> str:
    """English-phonetic ayah line with the focus word highlighted; Arabic light under it."""
    line = AYAH_LINE.get(verse)
    if not line:
        return ""
    target = (word_en or "").lower().replace("ā", "a").replace("ḥ", "h").replace("ṣ", "s")
    ph_parts = []
    ar_parts = []
    for ph, ar, key in zip(line["ph"], line["ar"], line["key"]):
        k = key.lower().replace("ā", "a").replace("ḥ", "h").replace("ṣ", "s")
        hit = (
            k == target
            or k.split()[-1] == target
            or target in k
            or k in target
        )
        if hit:
            ph_parts.append(f'<span class="focusw">{ph}</span>')
            ar_parts.append(f'<span class="focusw">{ar}</span>')
        else:
            ph_parts.append(ph)
            ar_parts.append(f'<span class="arlight">{ar}</span>')
    return (
        f'<div class="ayatsec">'
        f'<div class="ayatph">{" ".join(ph_parts)}</div>'
        f'<div class="ayatar" dir="rtl" lang="ar">{" ".join(ar_parts)}</div>'
        f'</div>'
    )


def _romanize(text: str) -> str:
    """Lazy import — avoid pulling Whisper stack when only coaching helpers are needed."""
    from transcribe_quran import romanize_ar
    return romanize_ar(text or "")


def _heard_phonetics(heard_arabic: str, heard_phonetic: str) -> list[str]:
    """One English-phonetic token per normalized heard word."""
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    raw_words = [w for w in (heard_arabic or "").split() if w]
    ph_words = [w for w in (heard_phonetic or "").split() if w]
    if ph_words and len(ph_words) == len(heard_words):
        return ph_words
    if raw_words and len(raw_words) == len(heard_words):
        return [_romanize(w) for w in raw_words]
    return [_romanize(w) for w in heard_words]


def _match_class(heard_w: str | None, exp_bare: str | None, dist: int) -> str:
    if not exp_bare:
        return "extra"
    if not heard_w:
        return "miss"
    if dist == 0:
        return "ok"
    if dist <= max(1, len(exp_bare) // 2):
        return "near"
    return "miss"


def compare_html(verse: int, heard_arabic: str, heard_phonetic: str = "") -> str:
    """
    English-led word compare for the closest-ayah panel:
    You (heard) vs Target, with match / close / miss badges.
    """
    expected = EXPECTED.get(verse) or []
    line = AYAH_LINE.get(verse) or {"ph": [], "ar": []}
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)
    # Map each heard bare-word occurrence → phonetic (in order)
    you_queue = list(you_phs)

    rows = []
    exp_i = 0
    for heard_w, exp_bare, en, ar, dist in _align_words(heard_words, expected):
        if not exp_bare:
            # Extra heard word — still show so the learner sees the mismatch
            you_ph = you_queue.pop(0) if you_queue else (_romanize(heard_w) if heard_w else "—")
            rows.append(
                f'<div class="cmprow cmpbad">'
                f'<div class="cmpyou"><span class="cmplbl">You</span> {you_ph}</div>'
                f'<div class="cmptgt"><span class="cmplbl">Target</span> —</div>'
                f'<div class="cmpbadge">extra</div></div>'
            )
            continue
        target_ph = line["ph"][exp_i] if exp_i < len(line["ph"]) else (en or "")
        target_ar = line["ar"][exp_i] if exp_i < len(line["ar"]) else (ar or "")
        exp_i += 1
        if heard_w and you_queue:
            you_ph = you_queue.pop(0)
        elif heard_w:
            you_ph = _romanize(heard_w)
        else:
            you_ph = "—"
        kind = _match_class(heard_w, exp_bare, dist)
        cls = {"ok": "cmpok", "near": "cmpnear", "miss": "cmpbad"}.get(kind, "cmpbad")
        badge = {"ok": "match", "near": "close", "miss": "miss"}.get(kind, "miss")
        rows.append(
            f'<div class="cmprow {cls}">'
            f'<div class="cmpyou"><span class="cmplbl">You</span> {you_ph}</div>'
            f'<div class="cmptgt"><span class="cmplbl">Target</span> {target_ph} '
            f'<span class="arlight">({target_ar})</span></div>'
            f'<div class="cmpbadge">{badge}</div></div>'
        )

    if not rows:
        return ""
    return (
        '<div class="cmpwrap">'
        '<div class="hmatchlbl">Closest ayah — word compare (English first)</div>'
        f'<div class="cmpbox">{"".join(rows)}</div>'
        '<div class="hnote">Green = match · Amber = close · Red = different / missing</div>'
        "</div>"
    )


def word_order_card(verse: int, heard_arabic: str, heard_phonetic: str, nwords: int) -> dict:
    """Self-standing GOOD card: full ayah + heard→target chips colored by match."""
    expected = EXPECTED.get(verse) or []
    line = AYAH_LINE.get(verse) or {"ph": [], "ar": []}
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)
    you_queue = list(you_phs)

    ph_parts, ar_parts, chips = [], [], []
    exp_i = 0
    for heard_w, exp_bare, en, ar, dist in _align_words(heard_words, expected):
        if not exp_bare:
            if you_queue:
                you_queue.pop(0)
            continue
        target_ph = line["ph"][exp_i] if exp_i < len(line["ph"]) else (en or "")
        target_ar = line["ar"][exp_i] if exp_i < len(line["ar"]) else (ar or "")
        exp_i += 1
        if heard_w and you_queue:
            you_ph = you_queue.pop(0)
        elif heard_w:
            you_ph = _romanize(heard_w)
        else:
            you_ph = "—"
        kind = _match_class(heard_w, exp_bare, dist)
        cls = {"ok": "wook", "near": "wonear", "miss": "wobad"}.get(kind, "wobad")
        ph_cls = {"ok": "wohitok", "near": "wohitnear", "miss": "wohitbad"}.get(kind, "wohitbad")
        ph_parts.append(f'<span class="{ph_cls}">{target_ph}</span>')
        ar_parts.append(f'<span class="arlight {ph_cls}">{target_ar}</span>')
        chips.append(
            f'<span class="wochip {cls}"><b>{you_ph}</b> → {target_ph}</span>'
        )

    section = (
        '<div class="ayatsec">'
        f'<div class="ayatph">{" ".join(ph_parts)}</div>'
        f'<div class="ayatar" dir="rtl" lang="ar">{" ".join(ar_parts)}</div>'
        f'<div class="worow">{"".join(chips)}</div>'
        "</div>"
    )
    n_ok = sum(1 for c in chips if "wook" in c)
    n_tot = len(chips) or 1
    return {
        "level": "ok",
        "rule": "word_order",
        "section": section,
        "plain": (
            f"Word order — heard vs target on this ayah "
            f"({n_ok}/{n_tot} words lined up cleanly; ~{nwords} detected)."
        ),
        "scholarly": None,
    }

# (heard, expected) → English-first tip. Arabic only in light brackets.
FIX = {
    ("ك", "ق"): {
        "heard": "a front K sound (kaf)",
        "want": "a deep K from the back of the throat (qaf)",
        "fix": "Say qul with a deeper K — farther back than English “cool”.",
        "ar": ("ك", "ق"),
    },
    ("ق", "ك"): {
        "heard": "a deep throat K (qaf)",
        "want": "a lighter front K (kaf)",
        "fix": "Use a lighter K, like the K in “key”.",
        "ar": ("ق", "ك"),
    },
    ("ب", "و"): {
        "heard": "a B sound (ba)",
        "want": "a W sound (waw)",
        "fix": "In huwa, round your lips for “w” like “we” — don’t close them for “b”.",
        "ar": ("ب", "و"),
    },
    ("و", "ب"): {
        "heard": "a W sound (waw)",
        "want": "a B sound (ba)",
        "fix": "Close the lips for a clear “b”.",
        "ar": ("و", "ب"),
    },
    ("ه", "ح"): {
        "heard": "a soft breathy H (ha)",
        "want": "a stronger throat H (ḥa)",
        "fix": "In aḥad, press a stronger H from the middle of the throat — not a light sigh.",
        "ar": ("ه", "ح"),
    },
    ("ح", "ه"): {
        "heard": "a strong throat H (ḥa)",
        "want": "a soft breathy H (ha)",
        "fix": "Use a lighter H, like a soft breath.",
        "ar": ("ح", "ه"),
    },
    ("ت", "ط"): {
        "heard": "a light T (ta)",
        "want": "a heavier T (ṭa)",
        "fix": "Make the T heavier — tongue slightly back.",
        "ar": ("ت", "ط"),
    },
    ("س", "ص"): {
        "heard": "a light S (seen)",
        "want": "a heavier S (ṣad)",
        "fix": "Make the S heavier / slightly darker.",
        "ar": ("س", "ص"),
    },
    ("د", "ض"): {
        "heard": "a light D (dal)",
        "want": "a heavier D (ḍad)",
        "fix": "Make the D heavier.",
        "ar": ("د", "ض"),
    },
    ("ز", "ظ"): {
        "heard": "a Z sound (zay)",
        "want": "a heavier DH/Z (ẓa)",
        "fix": "Make it heavier, tongue slightly back.",
        "ar": ("ز", "ظ"),
    },
    ("ذ", "ز"): {
        "heard": "a TH-as-in-this sound (dhal)",
        "want": "a buzzing Z (zay)",
        "fix": "Use a buzzing “z”, not “th”.",
        "ar": ("ذ", "ز"),
    },
    ("ث", "س"): {
        "heard": "a TH-as-in-think sound (tha)",
        "want": "a plain S (seen)",
        "fix": "Use a plain “s”, not “th”.",
        "ar": ("ث", "س"),
    },
}

_DIAC = re.compile(r"[\u064B-\u065F\u0670\u0640\u06D6-\u06ED]")


def normalize_ar(text: str) -> str:
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = _DIAC.sub("", t)
    t = (
        t.replace("أ", "ا")
        .replace("إ", "ا")
        .replace("آ", "ا")
        .replace("ٱ", "ا")
        .replace("ى", "ي")
        .replace("ة", "ه")
        .replace("ؤ", "و")
        .replace("ئ", "ي")
        .replace("ء", "")
    )
    t = "".join(ch if (ch.isspace() or "\u0621" <= ch <= "\u064a") else "" for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def _letters_only(word: str) -> str:
    return "".join(c for c in normalize_ar(word) if not c.isspace())


def _edit(a: str, b: str) -> int:
    if a == b:
        return 0
    n, m = len(a), len(b)
    prev = list(range(m + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[m]


def _align_chars(a: str, b: str):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    i, j = n, m
    pairs = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if a[i - 1] == b[j - 1] else 1):
            pairs.append((a[i - 1], b[j - 1])); i -= 1; j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            pairs.append((a[i - 1], None)); i -= 1
        else:
            pairs.append((None, b[j - 1])); j -= 1
    pairs.reverse()
    return pairs


def _align_words(heard_words: list[str], expected: list[tuple[str, str, str]]):
    out = []
    hi = 0
    for exp_bare, en, ar in expected:
        if hi >= len(heard_words):
            out.append((None, exp_bare, en, ar, 99))
            continue
        best_j, best_d = hi, 10**9
        for j in range(hi, min(len(heard_words), hi + 2)):
            d = _edit(_letters_only(heard_words[j]), exp_bare)
            if d < best_d:
                best_d, best_j = d, j
        while hi < best_j:
            out.append((heard_words[hi], None, None, None, 99)); hi += 1
        out.append((heard_words[hi], exp_bare, en, ar, best_d)); hi += 1
    while hi < len(heard_words):
        out.append((heard_words[hi], None, None, None, 99)); hi += 1
    return out


def _card(priority: int, verse: int, word_en: str, word_ar: str, tip: dict, hc: str, ec: str) -> dict:
    har, ear = tip.get("ar", (hc, ec))
    plain = (
        f"On <b>{word_en}</b> <span class=\"arlight\">({word_ar})</span>: "
        f"heard {tip['heard']} <span class=\"arlight\">({har})</span>, "
        f"want {tip['want']} <span class=\"arlight\">({ear})</span>."
    )
    return {
        "level": "error",
        "rule": "pronunciation",
        "priority": priority,
        "verse": verse,
        "word_en": word_en,
        "word_ar": word_ar,
        "section": section_html(verse, word_en),
        "plain": plain,
        "fix": tip["fix"],
        "scholarly": None,
        "heard_letter": hc,
        "expected_letter": ec,
    }


def coach_from_heard(verse: int, heard_arabic: str) -> list[dict]:
    expected = EXPECTED.get(verse)
    if not expected or not (heard_arabic or "").strip():
        return []

    heard_words = [w for w in normalize_ar(heard_arabic).split() if w]
    if not heard_words:
        return []

    cards = []
    seen = set()
    for priority, (heard_w, exp_bare, en, ar, dist) in enumerate(
        _align_words(heard_words, expected)
    ):
        if not exp_bare or not heard_w or not en:
            continue
        # Skip only badly mangled alignments; allow known letter tips when close
        if dist > max(2, (len(exp_bare) + 1) // 2):
            continue
        h = _letters_only(heard_w)
        if h == exp_bare:
            continue
        for hc, ec in _align_chars(h, exp_bare):
            if not hc or not ec or hc == ec:
                continue
            # Only known letter-pair tips — skip junk alignments (e.g. ف→ل)
            tip = FIX.get((hc, ec))
            if not tip:
                continue
            key = (hc, ec, en)
            if key in seen:
                continue
            seen.add(key)
            cards.append(_card(priority, verse, en, ar, tip, hc, ec))
    return cards


def madd_short_card(verse: int, word_en: str, word_ar: str, dur: float, priority: int) -> dict:
    return {
        "level": "measured",
        "rule": "madd",
        "priority": priority,
        "verse": verse,
        "word_en": word_en,
        "word_ar": word_ar,
        "section": section_html(verse, word_en),
        "plain": (
            f"On <b>{word_en}</b> <span class=\"arlight\">({word_ar})</span>: "
            f"the “oo/uu” stretch was very short (~{dur:.2f}s)."
        ),
        "fix": f"Hold the vowel in {word_en} a little longer — about two beats.",
        "scholarly": None,
    }


def ahad_bounce_card(verse: int, priority: int = 90) -> dict:
    en, ar = "aḥad", "أَحَدٌ"
    if verse == 2:
        en, ar = "aṣ-ṣamad", "ٱلصَّمَدُ"
    elif verse == 3:
        en, ar = "yalid", "يَلِدْ"
    return {
        "level": "measured",
        "rule": "qalqalah_practice",
        "priority": priority,
        "verse": verse,
        "word_en": en,
        "word_ar": ar,
        "section": section_html(verse, en),
        "plain": (
            f"On <b>{en}</b> <span class=\"arlight\">({ar})</span>: "
            f"finish with a light bounce on the final D sound (dal)."
        ),
        "fix": (
            "Stop on the D, then give a tiny echo — like a soft bounce — not a flat cut-off. "
            "Also keep the H in aḥad as a stronger throat H (ḥ), not a soft sigh."
        ),
        "scholarly": None,
    }


def qalqalah_error_card(verse: int, soft: bool = False, priority: int = 85) -> dict:
    en, ar = "aḥad", "أَحَدٌ"
    if verse == 2:
        en, ar = "aṣ-ṣamad", "ٱلصَّمَدُ"
    elif verse == 3:
        en, ar = "yalid", "يَلِدْ"
    return {
        "level": "error",
        "rule": "qalqalah",
        "priority": priority,
        "verse": verse,
        "word_en": en,
        "word_ar": ar,
        "section": section_html(verse, en),
        "verdict": "error",
        "plain": (
            f"{'Likely: ' if soft else ''}"
            f"On <b>{en}</b> <span class=\"arlight\">({ar})</span>: "
            f"the bounce on the final D wasn’t clear."
        ),
        "fix": "Stop on the D, then add a light echo/bounce — not a flat stop. Hear Al-Husary, then retry.",
        "scholarly": None,
    }


def pick_next_step(issue_cards: list[dict]) -> dict | None:
    """First fix to practice (ayah order)."""
    actionable = [c for c in issue_cards if c.get("level") in ("error", "measured") and c.get("fix")]
    if not actionable:
        return None
    actionable.sort(key=lambda c: c.get("priority", 50))
    top = dict(actionable[0])
    top["level"] = "next"
    top["rule"] = "next_step"
    top["tag"] = "NEXT STEP"
    n_left = len(actionable)
    top["steps_remaining"] = n_left
    top["plain"] = (
        f"<b>Practice this one thing next</b> "
        f"<span class=\"arlight\">({n_left} fix{'es' if n_left != 1 else ''} to go on this ayah)</span><br>"
        + top.get("plain", "")
    )
    return top
