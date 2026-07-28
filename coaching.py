"""
Compare what Whisper heard vs the expected ayah → plain coaching.

Style for learners who aren't fluent in Arabic:
  English sound first, Arabic lightly in brackets.

HARD RULE — English phonetics must be spot-on (2026-07-28 lesson):
  Transliteration labels (Qul, Qu, aḥad) are NOT always the mouth cue.
  If an English reader would say the wrong sound from our spelling, rewrite the tip.
  Example: “Qul” → cull/cool/ك. Working cue: QUAL / QUA like “quality”.
  Use familiar English anchors on every tip (word, syllable, letter, join).

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
        "ph": ["Qhul", "huwa", "Allāhu", "aḥad"],
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


def section_html(verse: int, word_en: str, *, highlight: str | None = None) -> str:
    """English-phonetic ayah line with the focus word highlighted; Arabic light under it.

    highlight='qu'|'ul' marks only that part inside Qul (syllable rescue).
    Do not treat 'qu' as a hit on full 'qul' via substring — that mixed Qul/Qu copy.
    """
    line = AYAH_LINE.get(verse)
    if not line:
        return ""
    hl = (highlight or "").lower().strip()
    target = (word_en or "").lower().replace("ā", "a").replace("ḥ", "h").replace("ṣ", "s")

    ph_parts = []
    ar_parts = []
    for ph, ar, key in zip(line["ph"], line["ar"], line["key"]):
        k = key.lower().replace("ā", "a").replace("ḥ", "h").replace("ṣ", "s")
        # Syllable marks inside first word (Qul)
        if hl == "qu" and k == "qul":
            # Qhu + l  /  قُ + لْ  (phonetic is Qhul — hollow qh)
            ph_parts.append(
                f'<span class="focusw">{ph[:3] if len(ph) >= 3 else ph}</span>'
                f'{ph[3:] if len(ph) > 3 else ""}'
            )
            ar_parts.append(
                f'<span class="focusw">{ar[:2] if len(ar) >= 2 else ar}</span>'
                f'{ar[2:] if len(ar) > 2 else ""}'
            )
            continue
        if hl == "ul" and k == "qul":
            # Keep onset unmarked; mark ul tail (after Qhu / قُ)
            cut = 3 if ph.lower().startswith("qhu") else 1
            ph_parts.append(
                f'{ph[:cut] if ph else ""}'
                f'<span class="focusw">{ph[cut:] if len(ph) > cut else ph}</span>'
            )
            ar_parts.append(
                f'{ar[:1] if ar else ""}'
                f'<span class="focusw">{ar[1:] if len(ar) > 1 else ar}</span>'
            )
            continue

        hit = k == target or k.split()[-1] == target
        # Allow multi-word targets (e.g. "qul huwa") without prefix false-positives
        if not hit and " " in target:
            hit = k in target.split() or target in k
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
        "heard": "an F sound (fa) — teeth on lip, like “fan”",
        "want": "a W sound (waw) — round lips, like “we” / “woo”",
        "fix": (
            "Get the word shape first: round the lips for “w” like “we” / “woo”. "
            "On <b>huwa</b>, English cue <b>HOO-wa</b> (like “who” + “wa”). "
            "Go slow before finer letter tips."
        ),
        "ar": ("ف", "و"),
    },
    ("و", "ف"): {
        "heard": "a W sound (waw) — like “we”",
        "want": "an F sound (fa) — like “fan”",
        "fix": "Upper teeth lightly on the lip for “f” as in “fan”.",
        "ar": ("و", "ف"),
    },
    ("ب", "و"): {
        "heard": "a B sound (ba) — lips closed, like “bee”",
        "want": "a W sound (waw) — round lips, like “we”",
        "fix": (
            "Get the word shape first: round your lips for “w” like “we” — "
            "don’t close them for “b” as in “bee”. On huwa: <b>HOO-wa</b>."
        ),
        "ar": ("ب", "و"),
    },
    ("و", "ب"): {
        "heard": "a W sound (waw) — like “we”",
        "want": "a B sound (ba) — like “bee”",
        "fix": "Close the lips for a clear “b” as in “bee”.",
        "ar": ("و", "ب"),
    },
}

# Fine letter tips — only after words are roughly right.
# Each tip MUST include an English mouth cue a beginner can imitate.
FIX = {
    ("ك", "ق"): {
        "heard": "an English K (like “cull” / “cool”)",
        "want": "Arabic ق — say it like English <b>QUAL</b> (start of “quality”), not “Qul/cull”",
        "fix": (
            "The written word is <b>Qul</b> (قُلْ). The English sound cue is <b>QUAL / qhul</b> — "
            "like the opening of <b>quality</b> / <b>quad</b>, not “cull” or “cool”.<br>"
            "1) Tip of tongue rests on the back of your bottom front teeth.<br>"
            "2) English “Qul/cull/cool” hits too far forward (middle ك) — that’s what we’re hearing.<br>"
            "3) Make the first letter like <b>QUAL</b>: hollow <b>qh</b> deeper in the throat, short dry pop, then finish the L.<br>"
            "4) One short word. Stop.<br>"
            "Note: if you felt QUAL/qhul but the app shows Kull, phone ASR often flattens ق→ك — retry closer."
        ),
        "ar": ("ك", "ق"),
    },
    ("ق", "ك"): {
        "heard": "a deep throat K (qaf) — QUAL-like",
        "want": "a lighter front K (kaf) — like the K in “key” / “cool”",
        "fix": "Use a lighter K, like the K in “key” — further forward than QUAL.",
        "ar": ("ق", "ك"),
    },
    ("ه", "ح"): {
        "heard": "a soft breathy H (like the H in “ahead” / “hello”)",
        "want": "a stronger throat Ḥ — like a quiet fog-the-mirror breath",
        "fix": (
            "In <b>aḥad</b>, the Ḥ is stronger than English “h”. "
            "Cue: gentle fog-on-a-mirror breath from the middle of the throat — "
            "not the soft H in “ahead”."
        ),
        "ar": ("ه", "ح"),
    },
    ("ح", "ه"): {
        "heard": "a strong throat Ḥ (fog-mirror breath)",
        "want": "a soft breathy H (like “hello”)",
        "fix": "Use a lighter H, like the H in “hello” — not the strong fog-mirror Ḥ.",
        "ar": ("ح", "ه"),
    },
    ("ت", "ط"): {
        "heard": "a light T (like “tea”)",
        "want": "a heavier Ṭ — fuller / darker, tongue slightly back (not “tea”)",
        "fix": "Make the T fuller than English “tea” — tongue a touch back, darker tone.",
        "ar": ("ت", "ط"),
    },
    ("س", "ص"): {
        "heard": "a light S (like “see”)",
        "want": "a heavier Ṣ — darker “ss”, like a strong “saw” (not thin “see”)",
        "fix": "Make the S darker/fuller than English “see” — closer to a strong “saw”.",
        "ar": ("س", "ص"),
    },
    ("د", "ض"): {
        "heard": "a light D (like “day”)",
        "want": "a heavier Ḍ — fuller / darker D (not light “day”)",
        "fix": "Make the D fuller than English “day” — darker, tongue slightly back.",
        "ar": ("د", "ض"),
    },
    ("ز", "ظ"): {
        "heard": "a Z sound (like “zoo”)",
        "want": "a heavier Ẓ — darker DH/Z, tongue slightly back",
        "fix": "Darker than English “zoo” — tongue slightly back, heavier buzz.",
        "ar": ("ز", "ظ"),
    },
    ("ذ", "ز"): {
        "heard": "TH as in “this” / “the”",
        "want": "a buzzing Z (like “zoo”)",
        "fix": "Use a buzzing “z” as in “zoo” — not “th” as in “this”.",
        "ar": ("ذ", "ز"),
    },
    ("ث", "س"): {
        "heard": "TH as in “think” / “thin”",
        "want": "a plain S (like “see”)",
        "fix": "Use a plain “s” as in “see” — not “th” as in “think”.",
        "ar": ("ث", "س"),
    },
}
FIX.update({k: dict(v) for k, v in WORD_IDENTITY.items()})


def compare_html(
    verse: int,
    heard_arabic: str,
    heard_phonetic: str = "",
    stage_words: list[str] | None = None,
) -> str:
    """English-first compare with yellow on mismatched words.

    If stage_words is set (e.g. ['qul']), only those stage words appear as
    Target — never paint the whole ayah yellow when the learner said one word.
    """
    expected = EXPECTED.get(verse) or []
    line = AYAH_LINE.get(verse) or {"ph": [], "ar": []}
    heard_words = [w for w in normalize_ar(heard_arabic or "").split() if w]
    you_phs = _heard_phonetics(heard_arabic, heard_phonetic)
    aligned = _align_words(heard_words, expected, you_phs)
    allow = (
        {(w or "").lower() for w in stage_words}
        if stage_words is not None
        else None
    )

    bad_heard: set[int] = set()
    used_heard: set[int] = set()
    tgt_parts, ar_parts = [], []
    n_bad = 0
    for exp_i, (heard_w, exp_bare, en, ar, dist, you_ph, widxs) in enumerate(aligned):
        if not exp_bare:
            continue
        if allow is not None and (en or "").lower() not in allow:
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
    if allow is not None:
        note = (
            "Yellow = this stage word needs work · unmarked = match"
            if n_bad
            else "This stage word lined up with the target"
        )
        lbl = "Heard vs target (this stage)"
    else:
        note = (
            "Yellow marker = word needs work · unmarked = match"
            if n_bad
            else "All words lined up with the target"
        )
        lbl = "Heard vs target (English first)"
    return (
        '<div class="cmpwrap">'
        f'<div class="hmatchlbl">{lbl}</div>'
        f'<div class="cmpline"><span class="cmplbl">You</span> '
        f'<span class="cmplinetxt">{" ".join(you_parts) if you_parts else "—"}</span></div>'
        f'<div class="cmpline"><span class="cmplbl">Target</span> '
        f'<span class="cmplinetxt">{" ".join(tgt_parts)}</span></div>'
        f'<div class="cmpline arline" dir="rtl" lang="ar">'
        f'<span class="cmplinetxt">{" ".join(ar_parts)}</span></div>'
        f'<div class="hnote">{note}</div>'
        "</div>"
    )


def align_onset_qaf(align_letters: list | None) -> dict:
    """XLSR letter-track onset: phone ASR often writes ك for real ق.

    Returns {has_qaf, has_kaf, onset} from the first aligned word's letters.
    Used to rescue phone-mic takes where Whisper flattens ق→ك.
    """
    onset: list[str] = []
    for item in align_letters or []:
        c = (item or {}).get("c") if isinstance(item, dict) else None
        if not c:
            continue
        if c == "|":
            if onset:
                break
            continue
        if c in (" ",):
            continue
        onset.append(c)
        if len(onset) >= 4:
            break
    onset_s = "".join(onset)
    return {
        "has_qaf": "ق" in onset_s,
        "has_kaf": "ك" in onset_s,
        "onset": onset_s,
    }


def phonetic_back_q(heard_phonetic: str) -> bool:
    """True if English phonetics clearly cue hollow back ق (qh / QUAL), not middle K."""
    ph = (heard_phonetic or "").lower()
    if not ph.strip():
        return False
    ph_compact = re.sub(r"[^a-zāḥṣṭḍẓ]", "", ph)
    if re.search(r"(^|[^a-z])(k|c)(oo|u|o|a|ull)", ph) or ph_compact.startswith(
        ("ku", "coo", "cul", "kol", "ko", "kull", "kul")
    ):
        return False
    if "qh" in ph_compact or ph_compact.startswith(("qual", "qhul", "qhu", "qaf")):
        return True
    # bare q + u/a (Qul / Qu) without kaf — weak but better than ignoring
    if re.search(r"(^|[^a-z])q(u|ū|o|a)", ph) and "k" not in ph_compact:
        return True
    return False


def evaluate_drill(
    drill: str,
    verse: int,
    heard_arabic: str,
    heard_phonetic: str = "",
    align_letters: list | None = None,
) -> dict:
    """
    Score syllable micro-drills (Qu / ul) without full-word ayah alignment.

    Qu gate: Arabic ق passes; Arabic ك fails. Clear qh/QUAL phonetics can pass
    when ق letter is missing — but never when Arabic ك / cull phonetics win.
    Phone rescue: if Whisper wrote ك but XLSR onset shows ق (not ك), pass —
    phone ASR flatten must not lock out the main audience.
    Acoustic cluster is NOT used for lock/fail.
    Returns passed/cards plus display_* for the UI (onset only — not Whisper's
    full-word guess like كل/Kul when the drill is Qu alone).
    """
    ar = normalize_ar(heard_arabic or "")
    letters = _letters_only(ar)
    ph = (heard_phonetic or "").lower()
    ph_compact = re.sub(r"[^a-zāḥṣṭḍẓ]", "", ph)
    align_q = align_onset_qaf(align_letters)

    def _drill_compare(you_ph: str, you_ar: str, tgt_ph: str, tgt_ar: str, ok: bool) -> str:
        you_cls = "" if ok else "marky"
        tgt_cls = "" if ok else "marky"
        you_ph_h = f'<span class="{you_cls}">{you_ph}</span>' if you_cls else you_ph
        you_ar_h = f'<span class="{you_cls}">{you_ar}</span>' if you_cls else you_ar
        tgt_ph_h = f'<span class="{tgt_cls}">{tgt_ph}</span>' if tgt_cls else tgt_ph
        tgt_ar_h = f'<span class="{tgt_cls}">{tgt_ar}</span>' if tgt_cls else tgt_ar
        note = "Drill match" if ok else "Yellow = this drill piece still needs work"
        return (
            '<div class="cmpwrap">'
            '<div class="hmatchlbl">Heard vs target (this drill only)</div>'
            f'<div class="cmpline"><span class="cmplbl">You</span> '
            f'<span class="cmplinetxt">{you_ph_h}</span></div>'
            f'<div class="cmpline"><span class="cmplbl">Target</span> '
            f'<span class="cmplinetxt">{tgt_ph_h}</span></div>'
            f'<div class="cmpline arline" dir="rtl" lang="ar">'
            f'<span class="cmplinetxt">{you_ar_h} → {tgt_ar_h}</span></div>'
            f'<div class="hnote">{note}</div>'
            "</div>"
        )

    if drill == "qu":
        # Stable: Arabic ق passes; Arabic ك fails.
        # Honour clear qh/QUAL phonetics when ASR omitted ق (align teach ↔ measure).
        # Phone rescue: XLSR onset ق beats Whisper ك (flatten). Never pass align ك.
        has_q = "ق" in letters
        has_k_ar = "ك" in letters
        has_k_ph = bool(
            re.search(r"(^|[^a-z])(k|c)(oo|u|o|a|ull)", ph)
        ) or ph_compact.startswith(("ku", "coo", "cul", "kol", "ko", "kull", "kul"))
        has_qh_ph = phonetic_back_q(heard_phonetic)
        align_rescues = bool(align_q.get("has_qaf") and not align_q.get("has_kaf"))
        if align_q.get("has_kaf") and not align_q.get("has_qaf"):
            # Letter track agrees this is middle ك — real fail
            has_k_ar = True
            has_q = False
            align_rescues = False
        if has_q or align_rescues or (has_qh_ph and not has_k_ar):
            return {
                "passed": True,
                "cards": [],
                "display_arabic": "قُ",
                "display_phonetic": "Qhu",
                "compare_html": _drill_compare("Qhu", "قُ", "Qhu", "قُ", True),
                "heard_match": "drill",
                "qaf_rescue": bool(align_rescues and not has_q),
            }
        fail_key = "drill:qu:ق"
        if has_k_ar or has_k_ph:
            tip = {
                "heard": "a middle K (kaf) — like English “cool/cull”",
                "want": "back ق — English cue <b>QUA / qhul</b> (as in “quality”), not “coo/cu”",
                "fix": (
                    "Say only the onset <b>Qu</b> (قُ). English cue: <b>QUA</b> like <b>quality</b> "
                    "(hollow <b>qh</b>, not “coo/cull”).<br>"
                    "If you felt that hollow QUAL but the app shows Kull: phone ASR often flattens "
                    "ق→ك — hold the phone closer and retry. We only lock when we hear ق / qh."
                ),
                "ar": ("ك", "ق"),
            }
            card = _card(5, verse, "Qu", "قُ", tip, "ك", "ق", rule="drill")
            card["key"] = fail_key
            return {
                "passed": False,
                "cards": [card],
                "display_arabic": "كُ",
                "display_phonetic": "Ku",
                "compare_html": _drill_compare("Ku", "كُ", "Qhu", "قُ", False),
                "heard_match": "drill",
            }
        tip = {
            "heard": (
                "almost nothing clear"
                if not (letters or ph.strip())
                else "something without a clear Q onset"
            ),
            "want": "short Qu (قُ) — English cue <b>QUA / qhul</b> (as in “quality”)",
            "fix": (
                "Say only <b>Qu</b> — think <b>QUA</b> like <b>quality</b> (hollow qh), not “coo/cu”. "
                "Deep back ق + short “u”. Stop after the short u."
            ),
            "ar": ("?", "ق"),
        }
        card = _card(5, verse, "Qu", "قُ", tip, "?", "ق", rule="drill")
        card["key"] = fail_key
        return {
            "passed": False,
            "cards": [card],
            "display_arabic": "(unclear)",
            "display_phonetic": "—",
            "compare_html": _drill_compare("—", "(unclear)", "Qhu", "قُ", False),
            "heard_match": "drill",
        }

    if drill == "ul":
        has_l = (
            "ل" in letters
            or bool(re.search(r"(u+|oo)l|ull|\bul\b|\bol\b", ph))
            or "ul" in ph_compact
            or "ool" in ph_compact
            or ph_compact.endswith("l")
        )
        if has_l:
            return {
                "passed": True,
                "cards": [],
                "display_arabic": "ـُلْ",
                "display_phonetic": "ul",
                "compare_html": _drill_compare("ul", "ـُلْ", "ul", "ـُلْ", True),
                "heard_match": "drill",
            }
        # Honest fail: if ASR only caught the onset, say so — don't invent an L.
        onset_only = ("ق" in letters or "ك" in letters) and "ل" not in letters
        tip = {
            "heard": (
                "the first letter only — no L ending yet"
                if onset_only
                else (
                    "almost nothing clear"
                    if not (letters or ph.strip())
                    else "something without a clear L ending"
                )
            ),
            "want": "just “ul” — like the end of “pull” / “full”",
            "fix": (
                "Say only <b>ul</b> — short “u” + clear L, like the ending of <b>pull</b> / <b>full</b>. "
                "No first letter (no K / Q) yet."
            ),
            "ar": ("?", "ل"),
        }
        card = _card(5, verse, "ul", "ـُلْ", tip, "?", "ل", rule="drill")
        card["key"] = "drill:ul:L"
        return {
            "passed": False,
            "cards": [card],
            "display_arabic": "(unclear)",
            "display_phonetic": "—",
            "compare_html": _drill_compare("—", "(unclear)", "ul", "ـُلْ", False),
            "heard_match": "drill",
        }

    return {"passed": False, "cards": []}


def evaluate_qu_qul_bridge(
    verse: int,
    heard_arabic: str,
    heard_phonetic: str = "",
    attempt: int = 1,
    align_letters: list | None = None,
) -> dict:
    """Syllable-rescue Qu attempts after word-first Qul failed.

    Same stable gate: ق passes, ك fails. Phone ASR ك is rescued when XLSR onset is ق.
    attempt is 1..3. The 3rd miss → tutor defer.
    """
    try:
        n = int(attempt)
    except (TypeError, ValueError):
        n = 1
    n = max(1, min(3, n))
    ev = evaluate_drill(
        "qu",
        verse,
        heard_arabic or "",
        heard_phonetic or "",
        align_letters=align_letters,
    )
    left = 3 - n

    if ev.get("passed"):
        out = dict(ev)
        out["bridge"] = {
            "mode": "syllable",
            "attempt": n,
            "verdict": "pass",
        }
        return out

    fail_key = "drill:qu:ق"
    if n >= 3:
        card = {
            "level": "defer",
            "rule": "drill",
            "key": fail_key,
            "tag": "ASK A TEACHER",
            "priority": 5,
            "verse": verse,
            "word_en": "Qu",
            "word_ar": "قُ",
            "section": section_html(verse, "qul", highlight="qu"),
            "plain": (
                "<b>Ask a teacher.</b> After 3 full-word Qul tries and 3 Qu-only tries "
                "I still didn’t hear a clear back ق. "
                "Please check your Q with a teacher before we continue."
            ),
            "fix": (
                "Pause here. A teacher can confirm the deep back Q. "
                "Come back when they say you’re ready — we won’t fake a lock."
            ),
            "scholarly": None,
            "heard_letter": (ev.get("cards") or [{}])[0].get("heard_letter") or "?",
            "expected_letter": "ق",
            "bridge": {
                "mode": "syllable",
                "attempt": n,
                "verdict": "tutor",
            },
        }
        return {
            "passed": False,
            "cards": [card],
            "display_arabic": ev.get("display_arabic") or "(unclear)",
            "display_phonetic": ev.get("display_phonetic") or "—",
            "compare_html": ev.get("compare_html") or "",
            "heard_match": "drill",
            "bridge": card["bridge"],
        }

    base_cards = list(ev.get("cards") or [])
    card = dict(base_cards[0]) if base_cards else _card(
        5, verse, "Qu", "قُ",
        {
            "heard": "no clear back Q",
            "want": "QUA like quality",
            "fix": "Say only <b>Qu</b> — English cue <b>QUA</b> like <b>quality</b>, not “coo”.",
            "ar": ("?", "ق"),
        },
        "?", "ق", rule="drill",
    )
    card["key"] = fail_key
    card["section"] = section_html(verse, "qul", highlight="qu")
    more = f"Syllable rescue — say only <b>Qu</b> (not full Qul). Try {n} of 3." + (
        f" {left} left." if left else " Last syllable try."
    )
    card["plain"] = (card.get("plain") or "") + f"<br><br><b>{more}</b>"
    card["fix"] = (
        "Say only <b>Qu</b> (قُ). English cue: <b>QUA</b> like <b>quality</b> — "
        "not “coo/cull”. Deep back ق + short “u”. Stop. "
        "Do <b>not</b> say the full word yet. Middle ك still fails."
    )
    card["bridge"] = {
        "mode": "syllable",
        "attempt": n,
        "verdict": "fail",
        "left": left,
    }
    return {
        "passed": False,
        "cards": [card],
        "display_arabic": ev.get("display_arabic") or "(unclear)",
        "display_phonetic": ev.get("display_phonetic") or "—",
        "compare_html": ev.get("compare_html") or "",
        "heard_match": "drill",
        "bridge": card["bridge"],
    }


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
    hl = None
    sec_word = word_en
    if rule == "drill" and (word_en or "").lower() == "qu":
        hl = "qu"
        sec_word = "qul"
    elif rule == "drill" and (word_en or "").lower() == "ul":
        hl = "ul"
        sec_word = "qul"
    return {
        "level": "error",
        "rule": rule,
        "key": f"{rule}:{word_en}:{hc}→{ec}",
        "priority": priority,
        "verse": verse,
        "word_en": word_en,
        "word_ar": word_ar,
        "section": section_html(verse, sec_word, highlight=hl),
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


def detect_repeated_earlier_word(
    verse: int,
    stage: dict | None,
    heard_arabic: str,
    heard_phonetic: str = "",
) -> dict | None:
    """
    Learner re-said a locked earlier word while the current stage word is missing.
    Classic case: Qul locked → stage is huwa → they say Qul again → heard looks
    'correct' in the panel but the stage fails. Return the earlier stage dict.
    """
    import stages as stg

    if not stage or not (heard_arabic or "").strip():
        return None
    cur_words = list(stage.get("words") or [])
    if not cur_words:
        return None
    cur_kinds = stage_word_kinds(verse, heard_arabic, heard_phonetic, cur_words)
    if not cur_kinds:
        return None
    # Pure miss on current stage — not a partial attempt that includes the target
    if any(k in ("ok", "near") for k in cur_kinds.values()):
        return None
    if not any(k == "miss" for k in cur_kinds.values()):
        return None

    for earlier in stg.list_stages(verse):
        if earlier.get("id") == stage.get("id"):
            break
        words = list(earlier.get("words") or [])
        if len(words) != 1:
            continue
        kinds = stage_word_kinds(verse, heard_arabic, heard_phonetic, words)
        if kinds and all(k in ("ok", "near") for k in kinds.values()):
            return earlier
    return None


def wrong_stage_repeat_card(verse: int, stage: dict, earlier: dict) -> dict:
    say = stage.get("say_en") or "this"
    say_ar = stage.get("say_ar") or ""
    prev = earlier.get("say_en") or "the earlier word"
    prev_ar = earlier.get("say_ar") or ""
    focus = stage.get("focus_word") or ((stage.get("words") or [""])[0])
    return {
        "level": "error",
        "rule": "wrong_stage",
        "key": f"wrong_stage:{stage.get('id')}:{earlier.get('id')}",
        "priority": 1,
        "verse": verse,
        "word_en": say,
        "word_ar": say_ar,
        "section": section_html(verse, focus or ""),
        "plain": (
            f"<b>Wrong word for this step.</b> You’re on <b>{say}</b> "
            f"<span class=\"arlight\">({say_ar})</span> now — "
            f"<b>{prev}</b> is already locked.<br>"
            f"This take sounded like <b>{prev}</b> again "
            f"<span class=\"arlight\">({prev_ar})</span>."
        ),
        "fix": (
            f"Say only <b>{say}</b> <span class=\"arlight\">({say_ar})</span> — "
            f"not {prev}. Tap Hear only {say} first if you need the model."
        ),
        "scholarly": None,
    }


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
        if rule == "wrong_stage":
            return f"saying only {wen} (not the earlier locked word)"
        if rule == "pronunciation":
            hc, ec = card.get("heard_letter"), card.get("expected_letter")
            if hc == "ك" and ec == "ق":
                return f"QUAL (deep ق), not cull/cool — in {wen}"
            if hc == "ه" and ec == "ح":
                return f"the strong Ḥ in {wen}"
            return f"the letter detail in {wen}"
        if rule == "drill":
            hc, ec = card.get("heard_letter"), card.get("expected_letter")
            if hc == "ك" and ec == "ق":
                return "QUA like quality (not coo/cull) in Qu"
            return "Qu onset — QUA like quality"
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
            return f"QUAL (deep ق), not cull/cool — in {wen}"
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
            return "the Qu onset (back Q)"
        if rest and rest[0] == "ul":
            return "the L in ul"
        return "this drill"
    return key


def _skill_family(key: str | None) -> str | None:
    """Group related keys so we don't fake 'holding' across drill variants."""
    if not key:
        return None
    parts = str(key).split(":")
    if parts[0] == "drill" and len(parts) >= 2:
        return f"drill:{parts[1]}"
    if parts[0] == "pronunciation" and len(parts) >= 3 and parts[2] == "ك→ق":
        return "drill:qu"
    return key


def _stage_for_skill_key(key: str | None) -> str | None:
    """Map a feedback key to the beginner-stage id it belongs to (if any)."""
    if not key:
        return None
    parts = str(key).split(":")
    if parts[0] == "drill" and len(parts) >= 2:
        return parts[1]  # qu / ul
    return None


def pick_next_step(
    issue_cards: list[dict],
    mastered: list[str] | None = None,
    last_focus: str | None = None,
    locked_stages: list[str] | None = None,
) -> dict | None:
    """
    One focus at a time.
    REGRESSION only if that skill's stage was actually locked earlier —
    never a ghost from a defer / still-on-Qu practice streak.
    """
    actionable = [
        c for c in issue_cards
        if c.get("level") in ("error", "measured", "defer") and c.get("fix")
    ]
    if not actionable:
        return None

    mastered_set = {m for m in (mastered or []) if m}
    # Also treat old Qu-drill key variants as the same mastery family.
    mastered_families = {_skill_family(m) for m in mastered_set}
    locked_set = {s for s in (locked_stages or []) if s}
    issue_keys = {c.get("key") for c in actionable if c.get("key")}
    issue_families = {_skill_family(k) for k in issue_keys}

    def _was_truly_locked(key: str | None) -> bool:
        if not key:
            return False
        st = _stage_for_skill_key(key)
        # Prefer locked stages — only a real Qu lock can regress Qu.
        if st:
            return st in locked_set
        return key in mastered_set or _skill_family(key) in mastered_families

    regressions = [
        c for c in actionable
        if c.get("key") and _was_truly_locked(c.get("key"))
    ]
    pool = regressions if regressions else actionable
    pool = sorted(pool, key=_issue_sort_key)
    top = dict(pool[0])
    is_reg = bool(regressions) and _was_truly_locked(top.get("key"))
    orig_rule = top.get("rule")
    need = describe_skill(top.get("key"), {**top, "rule": orig_rule})

    top["level"] = "next"
    top["rule"] = "next_step"
    # Fail path: FOCUS (keep drilling). Reserve "NEXT STEP" for stage-clear advance.
    top["tag"] = "REGRESSION" if is_reg else "FOCUS"
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

    fixed_key = None
    # Only claim a prior focus is "holding" if it's a different skill family.
    if (
        last_focus
        and last_focus not in issue_keys
        and _skill_family(last_focus) not in issue_families
    ):
        fixed_key = last_focus
    keep_key = fixed_key
    if is_reg and last_focus and _skill_family(last_focus) != _skill_family(top.get("key")):
        keep_key = last_focus

    kept = describe_skill(keep_key) if keep_key else None
    detail = top.get("plain", "")

    if is_reg and kept and _skill_family(keep_key) != _skill_family(top.get("key")):
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
