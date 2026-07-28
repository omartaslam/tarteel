"""
Compare what Whisper heard vs the expected ayah → plain coaching.

Style for learners who aren't fluent in Arabic:
  English sound first, Arabic lightly in brackets.

Iteration order for the student:
  1) Get words roughly right and in order (word_shape)
  2) Then fine letter tips (throat-K, etc.)
One "Next step" at a time.
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


def _romanize(text: str) -> str:
    from transcribe_quran import romanize_ar
    return romanize_ar(text or "")


def _heard_phonetics(heard_arabic: str, heard_phonetic: str) -> list[str]:
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
    if dist <= max(1, (len(exp_bare) + 1) // 2):
        return "near"
    return "miss"


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


def _align_words(
    heard_words: list[str],
    expected: list[tuple[str, str, str]],
    you_phs: list[str] | None = None,
):
    """
    Partial / merged-word alignment.
    Treat heard letters as a stream so 'Kulhu' can cover Qul + huwa.
    Returns (heard_letters|None, exp_bare, en, ar, dist, you_ph, heard_word_idxs).
    """
    stream: list[tuple[str, int]] = []
    for wi, w in enumerate(heard_words):
        for ch in _letters_only(w):
            stream.append((ch, wi))

    out = []
    pos = 0
    for exp_bare, en, ar in expected:
        e = exp_bare
        if pos >= len(stream):
            out.append((None, exp_bare, en, ar, 99, "—", []))
            continue

        best = None  # (sort_key, dist, start, end)
        max_span = len(e) + 1  # allow one extra letter of noise, not a whole next word
        for start in range(pos, min(pos + 3, len(stream) + 1)):
            for end in range(start + 1, min(len(stream), start + max_span) + 1):
                chunk = "".join(c for c, _ in stream[start:end])
                d = _edit(chunk, e)
                subs = sum(
                    1 for a, b in _align_chars(chunk, e) if a and b and a != b
                )
                # Prefer: low dist, early start, few substitutions, then length fit
                key = (d, start, subs, abs((end - start) - len(e)))
                if best is None or key < best[0]:
                    best = (key, d, start, end)

        if best is None:
            out.append((None, exp_bare, en, ar, 99, "—", []))
            continue

        _, d, start, end = best
        if d > max(2, len(e)):
            out.append((None, exp_bare, en, ar, d, "—", []))
            continue

        chunk = "".join(c for c, _ in stream[start:end])
        widxs = []
        for i in range(start, end):
            wi = stream[i][1]
            if not widxs or widxs[-1] != wi:
                widxs.append(wi)
        if you_phs:
            parts = [you_phs[i] for i in widxs if i < len(you_phs)]
            you_ph = " ".join(parts) if parts else _romanize(chunk)
        else:
            you_ph = (
                _romanize("".join(heard_words[i] for i in widxs))
                if widxs else _romanize(chunk)
            )
        out.append((chunk, exp_bare, en, ar, d, you_ph, widxs))
        pos = end

    return out


# Word-identity swaps — coach these BEFORE fine tajweed (throat-K, etc.).
WORD_IDENTITY = {
    ("ف", "و"): {
        "heard": "an F sound (fa)",
        "want": "a W sound (waw)",
        "fix": (
            "Get the word shape first: round the lips for “w” like “we”. "
            "Go slow on huwa before finer letter tips."
        ),
        "ar": ("ف", "و"),
    },
    ("و", "ف"): {
        "heard": "a W sound (waw)",
        "want": "an F sound (fa)",
        "fix": "Use the upper teeth lightly on the lip for “f”.",
        "ar": ("و", "ف"),
    },
    ("ب", "و"): {
        "heard": "a B sound (ba)",
        "want": "a W sound (waw)",
        "fix": (
            "Get the word shape first: round your lips for “w” like “we” — "
            "don’t close them for “b”."
        ),
        "ar": ("ب", "و"),
    },
    ("و", "ب"): {
        "heard": "a W sound (waw)",
        "want": "a B sound (ba)",
        "fix": "Close the lips for a clear “b”.",
        "ar": ("و", "ب"),
    },
}

# Fine letter tips — only after words are roughly right.
FIX = {
    ("ك", "ق"): {
        "heard": "an English K (like “cull” / “cool”)",
        "want": "Arabic Qul — deep Q, not English K or G",
        "fix": (
            "Say only the word <b>Qul</b> (not “Gul”, not “Kull”).<br>"
            "1) Tip of tongue rests on the back of your bottom front teeth.<br>"
            "2) English “cool/cull” hits too far forward — that’s what we’re hearing now.<br>"
            "3) For <b>Qul</b>, make the first letter deeper: soft-gargle place in the throat, short dry pop, then “ul”.<br>"
            "4) One short word: <b>Qul</b>. Stop."
        ),
        "ar": ("ك", "ق"),
    },
    ("ق", "ك"): {
        "heard": "a deep throat K (qaf)",
        "want": "a lighter front K (kaf)",
        "fix": "Use a lighter K, like the K in “key”.",
        "ar": ("ق", "ك"),
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
FIX.update({k: dict(v) for k, v in WORD_IDENTITY.items()})


def compare_html(verse: int, heard_arabic: str, heard_phonetic: str = "") -> str:
    """English-first ayah lines with yellow marker on mismatched words."""
    expected = EXPECTED.get(verse) or []
    line = AYAH_LINE.get(verse) or {"ph": [], "ar": []}
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)
    aligned = _align_words(heard_words, expected, you_phs)

    bad_heard: set[int] = set()
    used_heard: set[int] = set()
    tgt_parts, ar_parts = [], []
    n_bad = 0
    for exp_i, (heard_w, exp_bare, en, ar, dist, you_ph, widxs) in enumerate(aligned):
        if not exp_bare:
            continue
        target_ph = line["ph"][exp_i] if exp_i < len(line["ph"]) else (en or "")
        target_ar = line["ar"][exp_i] if exp_i < len(line["ar"]) else (ar or "")
        kind = _match_class(heard_w, exp_bare, dist)
        for wi in widxs:
            used_heard.add(wi)
        if kind == "ok":
            tgt_parts.append(target_ph)
            ar_parts.append(f'<span class="arlight">{target_ar}</span>')
        else:
            n_bad += 1
            tgt_parts.append(f'<span class="marky">{target_ph}</span>')
            ar_parts.append(f'<span class="marky">{target_ar}</span>')
            for wi in widxs:
                bad_heard.add(wi)

    you_parts = []
    for i, y in enumerate(you_phs or []):
        # Yellow if this heard word fed a mismatch, or was leftover/extra.
        if i in bad_heard or i not in used_heard:
            you_parts.append(f'<span class="marky">{y}</span>')
        else:
            you_parts.append(y)

    if not tgt_parts:
        return ""
    note = (
        "Yellow marker = word needs work · unmarked = match"
        if n_bad
        else "All words lined up with the target"
    )
    return (
        '<div class="cmpwrap">'
        '<div class="hmatchlbl">Heard vs target (English first)</div>'
        f'<div class="cmpline"><span class="cmplbl">You</span> '
        f'<span class="cmplinetxt">{" ".join(you_parts) if you_parts else "—"}</span></div>'
        f'<div class="cmpline"><span class="cmplbl">Target</span> '
        f'<span class="cmplinetxt">{" ".join(tgt_parts)}</span></div>'
        f'<div class="cmpline arline" dir="rtl" lang="ar">'
        f'<span class="cmplinetxt">{" ".join(ar_parts)}</span></div>'
        f'<div class="hnote">{note}</div>'
        "</div>"
    )


def evaluate_drill(
    drill: str,
    verse: int,
    heard_arabic: str,
    heard_phonetic: str = "",
) -> dict:
    """
    Score syllable micro-drills (Qu / ul) without full-word ayah alignment.

    Returns {"passed": bool, "cards": list[dict]}.
    """
    ar = normalize_ar(heard_arabic or "")
    letters = _letters_only(ar)
    ph = (heard_phonetic or "").lower()
    ph_compact = re.sub(r"[^a-zāḥṣṭḍẓ]", "", ph)

    if drill == "qu":
        # Shape-first: lock the Ku onset (ك or ق). Deep ق is polish later, not a gate.
        has_q = "ق" in letters
        has_k = (
            "ك" in letters
            or bool(re.search(r"(^|[^a-z])(k|c)(oo|u|o|a)", ph))
            or ph_compact.startswith(("ku", "coo", "cul", "kol", "ko", "q"))
        )
        if has_q or has_k:
            cards = []
            if has_k and not has_q:
                cards.append({
                    "level": "measured",
                    "rule": "drill",
                    "key": "drill:qu:deeper_q",
                    "priority": 40,
                    "verse": verse,
                    "word_en": "Ku",
                    "word_ar": "كُ",
                    "section": section_html(verse, "qul"),
                    "plain": (
                        "Onset shape locked as <b>Ku</b>. "
                        "Later we’ll deepen that K toward Arabic <b>Q</b> (ق) — "
                        "soft-gargle place — but not yet."
                    ),
                    "fix": (
                        "For now: short <b>Ku</b> only. No L. "
                        "Deep Q is a polish step after Kul/Qul shape is locked."
                    ),
                    "scholarly": None,
                })
            return {"passed": True, "cards": cards}
        tip = {
            "heard": "almost nothing clear" if not (letters or ph.strip()) else "something without a clear K/Q onset",
            "want": "a short Ku (كُ) — K + “u” only",
            "fix": (
                "Say only <b>Ku</b> — clear K + short “u”. Stop. "
                "Do <b>not</b> add the L yet."
            ),
            "ar": ("?", "ك"),
        }
        card = _card(5, verse, "Ku", "كُ", tip, "?", "ك", rule="drill")
        card["key"] = "drill:qu:onset"
        return {"passed": False, "cards": [card]}

    if drill == "ul":
        has_l = (
            "ل" in letters
            or bool(re.search(r"(u+|oo)l|ull|\bul\b|\bol\b", ph))
            or "ul" in ph_compact
            or "ool" in ph_compact
            or ph_compact.endswith("l")
        )
        if has_l:
            return {"passed": True, "cards": []}
        tip = {
            "heard": "something without a clear L ending",
            "want": "just “ul” (u + L)",
            "fix": (
                "Say only <b>ul</b> — short “u”, then a clear L. "
                "No first letter (no K / Q) yet."
            ),
            "ar": ("?", "ل"),
        }
        card = _card(5, verse, "ul", "ـُلْ", tip, "?", "ل", rule="drill")
        card["key"] = "drill:ul:L"
        return {"passed": False, "cards": [card]}

    return {"passed": False, "cards": []}


def word_order_card(verse: int, heard_arabic: str, heard_phonetic: str, nwords: int) -> dict:
    expected = EXPECTED.get(verse) or []
    line = AYAH_LINE.get(verse) or {"ph": [], "ar": []}
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)

    ph_parts, ar_parts, chips = [], [], []
    for exp_i, (heard_w, exp_bare, en, ar, dist, you_ph, _widxs) in enumerate(
        _align_words(heard_words, expected, you_phs)
    ):
        if not exp_bare:
            continue
        target_ph = line["ph"][exp_i] if exp_i < len(line["ph"]) else (en or "")
        target_ar = line["ar"][exp_i] if exp_i < len(line["ar"]) else (ar or "")
        kind = _match_class(heard_w, exp_bare, dist)
        cls = {"ok": "wook", "near": "wonear", "miss": "wobad"}.get(kind, "wobad")
        ph_cls = {"ok": "wohitok", "near": "wohitnear", "miss": "wohitbad"}.get(kind, "wohitbad")
        ph_parts.append(f'<span class="{ph_cls}">{target_ph}</span>')
        ar_parts.append(f'<span class="arlight {ph_cls}">{target_ar}</span>')
        chips.append(
            f'<span class="wochip {cls}"><b>{you_ph or "—"}</b> → {target_ph}</span>'
        )

    section = (
        '<div class="ayatsec">'
        f'<div class="ayatph">{" ".join(ph_parts)}</div>'
        f'<div class="ayatar" dir="rtl" lang="ar">{" ".join(ar_parts)}</div>'
        f'<div class="worow">{"".join(chips)}</div>'
        "</div>"
    )
    n_ok = sum(1 for c in chips if "wook" in c)
    n_near = sum(1 for c in chips if "wonear" in c)
    n_tot = len(chips) or 1
    return {
        "level": "ok",
        "rule": "word_order",
        "section": section,
        "plain": (
            f"Word order — heard vs target on this ayah "
            f"({n_ok} exact, {n_near} close / partial, {n_tot} words)."
        ),
        "scholarly": None,
    }


def _card(
    priority: int,
    verse: int,
    word_en: str,
    word_ar: str,
    tip: dict,
    hc: str,
    ec: str,
    rule: str = "pronunciation",
) -> dict:
    har, ear = tip.get("ar", (hc, ec))
    plain = (
        f"On <b>{word_en}</b> <span class=\"arlight\">({word_ar})</span>: "
        f"heard {tip['heard']} <span class=\"arlight\">({har})</span>, "
        f"want {tip['want']} <span class=\"arlight\">({ear})</span>."
    )
    return {
        "level": "error",
        "rule": rule,
        "key": f"{rule}:{word_en}:{hc}→{ec}",
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


def word_shape_card(
    verse: int,
    word_en: str,
    word_ar: str,
    you_ph: str,
    priority: int,
    tip: dict | None = None,
) -> dict:
    """First-pass: get the word roughly right before fine letter tajweed."""
    if tip:
        plain = (
            f"On <b>{word_en}</b> <span class=\"arlight\">({word_ar})</span>: "
            f"heard roughly <b>{you_ph or '—'}</b> — "
            f"{tip['heard']} <span class=\"arlight\">({tip['ar'][0]})</span>, "
            f"want {tip['want']} <span class=\"arlight\">({tip['ar'][1]})</span>."
        )
        fix = tip["fix"]
        key = f"word_shape:{word_en}:{tip['ar'][0]}→{tip['ar'][1]}"
    else:
        plain = (
            f"On <b>{word_en}</b> <span class=\"arlight\">({word_ar})</span>: "
            f"heard roughly <b>{you_ph or '—'}</b> — get this word recognisable first."
        )
        fix = (
            f"Say <b>{word_en}</b> slowly so a listener can tell which word it is. "
            f"Don’t chase fine letter detail yet — word shape and order come first."
        )
        key = f"word_shape:{word_en}"
    return {
        "level": "error",
        "rule": "word_shape",
        "key": key,
        "priority": priority,
        "verse": verse,
        "word_en": word_en,
        "word_ar": word_ar,
        "section": section_html(verse, word_en),
        "plain": plain,
        "fix": fix,
        "scholarly": None,
        "identity": bool(tip),
        "heard_letter": tip["ar"][0] if tip else None,
        "expected_letter": tip["ar"][1] if tip else None,
    }


def _find_identity_tip(
    en: str,
    heard_w: str | None,
    exp_bare: str,
    you_ph: str,
    heard_words: list[str],
    you_phs: list[str],
) -> tuple[dict | None, str]:
    """Word-identity tip (F↔W, B↔W). Returns (tip, maybe-updated you_ph)."""
    if not en:
        return None, you_ph
    identity_tip = None
    if heard_w:
        h = _letters_only(heard_w)
        # Prefer first-letter identity when both sides start with identity pair.
        if h and exp_bare and h[0] != exp_bare[0] and (h[0], exp_bare[0]) in WORD_IDENTITY:
            identity_tip = WORD_IDENTITY[(h[0], exp_bare[0])]
        if identity_tip is None:
            for hc, ec in _align_chars(h, exp_bare):
                if hc and ec and hc != ec and (hc, ec) in WORD_IDENTITY:
                    identity_tip = WORD_IDENTITY[(hc, ec)]
                    break
        # huwa / waw words: فو→هو, بو→هو (F/B replace the W quality; ه is not the swap target)
        if identity_tip is None and "و" in exp_bare and "ف" not in exp_bare and "ب" not in exp_bare:
            if "ف" in h and "و" not in h:
                identity_tip = WORD_IDENTITY[("ف", "و")]
            elif h.startswith("ف") and "و" in h:
                identity_tip = WORD_IDENTITY[("ف", "و")]
            elif "ب" in h and "و" not in h:
                identity_tip = WORD_IDENTITY[("ب", "و")]
            elif h.startswith("ب") and "و" in h:
                identity_tip = WORD_IDENTITY[("ب", "و")]
    # Dentures / glue: F standing in for W on huwa (fāllahu)
    if identity_tip is None and en.lower() == "huwa":
        has_w = "و" in (heard_w or "")
        heard_f = (heard_w or "").startswith("ف") or (you_ph or "").lower().startswith("f")
        glued_f = any(
            (w.startswith("ف") or (i < len(you_phs) and you_phs[i].lower().startswith("f")))
            for i, w in enumerate(heard_words)
        )
        if (heard_f or glued_f) and not has_w:
            identity_tip = WORD_IDENTITY[("ف", "و")]
            if you_ph and "f" not in you_ph.lower():
                you_ph = f"{you_ph} / f…"
    return identity_tip, you_ph


def coach_from_heard(
    verse: int,
    heard_arabic: str,
    heard_phonetic: str = "",
    stage_words: list[str] | None = None,
) -> list[dict]:
    """
    Two-pass coaching:
      1) word identity (F↔W) then rough word shape/order
      2) fine letter tajweed only when no full misses
    If stage_words is set, only coach those expected words.
    """
    expected = EXPECTED.get(verse)
    if not expected or not (heard_arabic or "").strip():
        return []

    heard_words = [w for w in normalize_ar(heard_arabic).split() if w]
    if not heard_words:
        return []

    allow = None
    if stage_words is not None:
        allow = {(w or "").lower() for w in stage_words}

    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)
    aligned = _align_words(heard_words, expected, you_phs)

    cards = []
    seen = set()
    any_miss = False

    for wi, (heard_w, exp_bare, en, ar, dist, you_ph, _widxs) in enumerate(aligned):
        if not exp_bare or not en:
            continue
        if allow is not None and (en or "").lower() not in allow:
            continue
        kind = _match_class(heard_w, exp_bare, dist)
        if kind == "ok":
            continue

        identity_tip, you_ph = _find_identity_tip(
            en, heard_w, exp_bare, you_ph, heard_words, you_phs
        )
        if identity_tip:
            key = ("id", en, identity_tip["ar"])
            if key not in seen:
                seen.add(key)
                cards.append(
                    word_shape_card(verse, en, ar, you_ph, priority=wi, tip=identity_tip)
                )
            # Identity swaps (F→W) beat both generic shape and fine tajweed.
            if kind == "miss":
                any_miss = True
            continue

        if kind == "miss":
            # Full miss: get the word roughly recognisable before letter tips.
            any_miss = True
            cards.append(word_shape_card(verse, en, ar, you_ph, priority=10 + wi))
        # near without identity → leave for fine tajweed pass below

    if not any_miss:
        for wi, (heard_w, exp_bare, en, ar, dist, you_ph, _widxs) in enumerate(aligned):
            if not exp_bare or not heard_w or not en:
                continue
            if allow is not None and (en or "").lower() not in allow:
                continue
            kind = _match_class(heard_w, exp_bare, dist)
            if kind not in ("ok", "near"):
                continue
            h = _letters_only(heard_w)
            if h == exp_bare:
                continue
            for hc, ec in _align_chars(h, exp_bare):
                if not hc or not ec or hc == ec:
                    continue
                if (hc, ec) in WORD_IDENTITY:
                    continue
                tip = FIX.get((hc, ec))
                if not tip:
                    continue
                key = (hc, ec, en)
                if key in seen:
                    continue
                seen.add(key)
                cards.append(
                    _card(40 + wi, verse, en, ar, tip, hc, ec, rule="pronunciation")
                )
    return cards


def stage_word_kinds(
    verse: int,
    heard_arabic: str,
    heard_phonetic: str = "",
    stage_words: list[str] | None = None,
) -> dict[str, str]:
    """Map expected en → match kind for words in the stage."""
    expected = EXPECTED.get(verse) or []
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)
    aligned = _align_words(heard_words, expected, you_phs)
    allow = {(w or "").lower() for w in (stage_words or [])} if stage_words is not None else None
    out = {}
    for heard_w, exp_bare, en, ar, dist, you_ph, _widxs in aligned:
        if not en:
            continue
        if allow is not None and (en or "").lower() not in allow:
            continue
        out[en] = _match_class(heard_w, exp_bare, dist)
    return out


def madd_short_card(verse: int, word_en: str, word_ar: str, dur: float, priority: int) -> dict:
    return {
        "level": "measured",
        "rule": "madd",
        "key": f"madd:{word_en}",
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
        "key": f"qalqalah:{en}",
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
        "key": f"qalqalah:{en}",
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


def _issue_sort_key(c: dict):
    if c.get("rule") == "word_shape":
        tier = 0 if c.get("identity") else 1
    else:
        tier = 2
    return (tier, c.get("priority", 50))


def describe_skill(key: str | None, card: dict | None = None) -> str:
    """Short elegant English label for a practice-log / next-step key."""

    def _tw(w: str) -> str:
        if not w:
            return w
        return w if w[0].isupper() else (w[0].upper() + w[1:])

    if card and card.get("word_en"):
        wen = _tw(card["word_en"])
        rule = card.get("rule") or ""
        if rule == "word_shape" and card.get("identity"):
            plain = card.get("plain") or ""
            if "W sound" in plain or card.get("expected_letter") == "و":
                return f"the W in {wen}"
            if "B sound" in plain or card.get("expected_letter") == "ب":
                return f"the B in {wen}"
            return f"the sound shape of {wen}"
        if rule == "word_shape":
            return f"the shape of {wen}"
        if rule == "pronunciation":
            hc, ec = card.get("heard_letter"), card.get("expected_letter")
            if hc == "ك" and ec == "ق":
                return f"the deep Q in {wen}"
            if hc == "ه" and ec == "ح":
                return f"the strong Ḥ in {wen}"
            return f"the letter detail in {wen}"
        if rule in ("madd",):
            return f"the vowel length in {wen}"
        if rule in ("qalqalah", "qalqalah_practice"):
            return f"the bounce on {wen}"
        if wen:
            return wen

    if not key:
        return "this point"
    parts = str(key).split(":")
    head, rest = parts[0], parts[1:]
    if head == "word_shape":
        wen = _tw(rest[0]) if rest else "this word"
        if len(rest) >= 2 and "ف→و" in rest[1]:
            return f"the W in {wen}"
        if len(rest) >= 2 and "ب→و" in rest[1]:
            return f"the W in {wen}"
        if len(rest) >= 2 and "و→ف" in rest[1]:
            return f"the F in {wen}"
        return f"the shape of {wen}"
    if head == "pronunciation":
        wen = _tw(rest[0]) if rest else "this word"
        swap = rest[1] if len(rest) > 1 else ""
        if swap == "ك→ق":
            return f"the deep Q in {wen}"
        if swap == "ه→ح":
            return f"the strong Ḥ in {wen}"
        return f"the letter detail in {wen}"
    if head == "madd":
        return f"the vowel length in {_tw(rest[0]) if rest else 'this word'}"
    if head == "qalqalah":
        return f"the bounce on {_tw(rest[0]) if rest else 'this word'}"
    if head == "shadda":
        return f"the doubling in {_tw(rest[0]) if rest else 'this word'}"
    if head == "drill":
        if rest and rest[0] == "qu":
            return "the deep Q in Qu"
        if rest and rest[0] == "ul":
            return "the L in ul"
        return "this drill"
    return key


def pick_next_step(
    issue_cards: list[dict],
    mastered: list[str] | None = None,
    last_focus: str | None = None,
) -> dict | None:
    """
    One focus at a time.
    If a previously-mastered skill is broken again, that regression wins
    (move backwards to move forwards).
    """
    actionable = [
        c for c in issue_cards
        if c.get("level") in ("error", "measured") and c.get("fix")
    ]
    if not actionable:
        return None

    mastered_set = {m for m in (mastered or []) if m}
    issue_keys = {c.get("key") for c in actionable if c.get("key")}
    regressions = [c for c in actionable if c.get("key") and c["key"] in mastered_set]
    pool = regressions if regressions else actionable
    pool = sorted(pool, key=_issue_sort_key)
    top = dict(pool[0])
    is_reg = bool(regressions) and top.get("key") in mastered_set
    orig_rule = top.get("rule")
    need = describe_skill(top.get("key"), {**top, "rule": orig_rule})

    top["level"] = "next"
    top["rule"] = "next_step"
    top["tag"] = "REGRESSION" if is_reg else "NEXT STEP"
    top["regression"] = is_reg
    top["key"] = top.get("key")
    n_left = len(actionable)
    after_this = max(0, n_left - 1)
    # Quiet progress note — count is "more after this focus", not including it.
    more_note = (
        f' <span class="arlight">({after_this} more after this on the ayah)</span>'
        if after_this
        else ""
    )
    issue_keys = {c.get("key") for c in actionable if c.get("key")}

    fixed_key = None
    if last_focus and last_focus not in issue_keys:
        fixed_key = last_focus
    keep_key = fixed_key
    if is_reg and last_focus and top.get("key") != last_focus:
        keep_key = last_focus

    kept = describe_skill(keep_key) if keep_key else None
    detail = top.get("plain", "")

    if is_reg and kept and keep_key != top.get("key"):
        if fixed_key:
            head = (
                f"<b>You’ve steadied {kept}</b> — well done. "
                f"But <b>{need}</b> slipped.<br>"
                f"<b>Next:</b> restore {need}, and keep {kept} as it is."
            )
        else:
            head = (
                f"Hold what you’ve gained on <b>{kept}</b>. "
                f"But <b>{need}</b> has slipped.<br>"
                f"<b>Next:</b> restore {need} first — keep {kept} steady while you do."
            )
        top["plain"] = head + (
            f"<div class=\"arlight\" style=\"margin-top:8px\">{detail}</div>"
            if detail else ""
        )
        if top.get("fix"):
            top["fix"] = (
                f"{top['fix']} "
                f"Protect {kept} while you restore {need} — don’t trade one fix for the other."
            )
    elif is_reg:
        labeled = need[0].upper() + need[1:] if need else need
        head = (
            f"<b>{labeled}</b> slipped from an earlier win.<br>"
            f"<b>Next:</b> restore {need} before taking on anything new."
        )
        top["plain"] = head + (
            f"<div class=\"arlight\" style=\"margin-top:8px\">{detail}</div>"
            if detail else ""
        )
    elif kept:
        head = (
            f"<b>Nice — {kept} is holding.</b> "
            f"One thing next: <b>{need}</b>{more_note}."
        )
        top["plain"] = head + "<br>" + detail
    else:
        head = f"<b>One thing next:</b> {need}{more_note}."
        top["plain"] = head + "<br>" + detail

    top["steps_remaining"] = n_left
    top["steps_after"] = after_this
    top["fixed_key"] = fixed_key
    top["keep_key"] = keep_key
    return top
