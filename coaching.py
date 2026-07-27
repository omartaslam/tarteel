"""
Compare what Whisper heard vs the expected ayah, and turn letter swaps into
plain-English coaching cards the learner can act on next try.
"""
from __future__ import annotations

import re
import unicodedata

# Expected bare (undiacritized) words + learner-facing labels per ayah.
EXPECTED = {
    1: [
        ("قل", "قُلْ / qul"),
        ("هو", "هُوَ / huwa"),
        ("الله", "ٱللَّهُ / Allāhu"),
        ("احد", "أَحَدٌ / ahad"),
    ],
    2: [
        ("الله", "ٱللَّهُ / Allāhu"),
        ("الصمد", "ٱلصَّمَدُ / aṣ-ṣamad"),
    ],
    3: [
        ("لم", "لَمْ / lam"),
        ("يلد", "يَلِدْ / yalid"),
        ("ولم", "وَلَمْ / wa lam"),
        ("يولد", "يُولَدْ / yūlad"),
    ],
    4: [
        ("ولم", "وَلَمْ / wa lam"),
        ("يكن", "يَكُن / yakun"),
        ("له", "لَّهُ / lahu"),
        ("كفوا", "كُفُوًا / kufuwan"),
        ("احد", "أَحَدٌ / ahad"),
    ],
}

# Common tilawah confusions → how to fix (plain English).
# Keys are (heard_letter, expected_letter).
FIX = {
    ("ك", "ق"): {
        "plain": "Heard kaf (ك / plain K) where qaf (ق / deep K) belongs in {word}.",
        "fix": "For ق / qaf: make the sound farther back in the throat — a deeper K, not the front kaf (ك).",
    },
    ("ق", "ك"): {
        "plain": "Heard qaf (ق) where kaf (ك) belongs in {word}.",
        "fix": "Use a lighter front K (ك / kaf), not the deep throat ق.",
    },
    ("ب", "و"): {
        "plain": "Heard ba (ب / B) instead of waw (و / W) in {word}.",
        "fix": "Round the lips for و / waw — like English 'w' in 'we' (huwa), not a 'b' lip closure.",
    },
    ("و", "ب"): {
        "plain": "Heard waw (و / W) instead of ba (ب / B) in {word}.",
        "fix": "Close the lips for ب / ba — a clear 'b', not a 'w'.",
    },
    ("ه", "ح"): {
        "plain": "Heard soft ha (ه) instead of throat Ha (ح / ḥ) in {word}.",
        "fix": "For ح / ḥa: squeeze from the middle of the throat — a strong 'h', not the light breathy ه.",
    },
    ("ح", "ه"): {
        "plain": "Heard throat Ha (ح) instead of soft ha (ه) in {word}.",
        "fix": "Use a lighter breathy ه / ha, not the pressed throat ح.",
    },
    ("ت", "ط"): {
        "plain": "Heard light ta (ت) instead of heavy Ta (ط) in {word}.",
        "fix": "For ط / Ṭa: raise the back of the tongue — a heavier 't'.",
    },
    ("س", "ص"): {
        "plain": "Heard light seen (س) instead of heavy Sad (ص) in {word}.",
        "fix": "For ص / Ṣad: round/heavien the 's' — tongue slightly back.",
    },
    ("د", "ض"): {
        "plain": "Heard dal (د) instead of Dad (ض) in {word}.",
        "fix": "For ض / Ḍad: a heavier 'd' with the side of the tongue.",
    },
    ("ز", "ظ"): {
        "plain": "Heard zay (ز) instead of Za (ظ) in {word}.",
        "fix": "For ظ / Ẓa: a heavier 'dh/z' sound with the tongue back.",
    },
    ("ذ", "ز"): {
        "plain": "Heard dhal (ذ) instead of zay (ز) in {word}.",
        "fix": "Use ز / zay (buzzing 'z'), not ذ / dhal ('th' in 'this').",
    },
    ("ث", "س"): {
        "plain": "Heard tha (ث) instead of seen (س) in {word}.",
        "fix": "Use س / seen (plain 's'), not ث / tha ('th' in 'think').",
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
    # drop non-letters except spaces
    t = "".join(ch if (ch.isspace() or "\u0621" <= ch <= "\u064a") else "" for ch in t)
    return re.sub(r"\s+", " ", t).strip()


def _letters_only(word: str) -> str:
    return "".join(c for c in normalize_ar(word) if not c.isspace())


def _align_chars(a: str, b: str):
    """Needleman–Wunsch-ish char align; returns list of (a_char_or_None, b_char_or_None)."""
    n, m = len(a), len(b)
    # DP
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
    for j in range(1, m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,
                dp[i][j - 1] + 1,
                dp[i - 1][j - 1] + cost,
            )
    # traceback
    i, j = n, m
    pairs = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (0 if a[i - 1] == b[j - 1] else 1):
            pairs.append((a[i - 1], b[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            pairs.append((a[i - 1], None))
            i -= 1
        else:
            pairs.append((None, b[j - 1]))
            j -= 1
    pairs.reverse()
    return pairs


def _align_words(heard_words: list[str], expected: list[tuple[str, str]]):
    """Greedy left-to-right word align by edit distance."""
    out = []
    hi = 0
    for exp_bare, label in expected:
        if hi >= len(heard_words):
            out.append((None, exp_bare, label))
            continue
        # pick best among remaining small window
        best_j, best_d = hi, 10**9
        for j in range(hi, min(len(heard_words), hi + 2)):
            d = _edit(_letters_only(heard_words[j]), exp_bare)
            if d < best_d:
                best_d, best_j = d, j
        # skip empties
        while hi < best_j:
            out.append((heard_words[hi], None, None))
            hi += 1
        out.append((heard_words[hi], exp_bare, label))
        hi += 1
    while hi < len(heard_words):
        out.append((heard_words[hi], None, None))
        hi += 1
    return out


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


def coach_from_heard(verse: int, heard_arabic: str) -> list[dict]:
    """
    Build CHECK cards: heard X instead of Y + how to fix.
    """
    expected = EXPECTED.get(verse)
    if not expected or not heard_arabic or not heard_arabic.strip():
        return []

    heard_words = [w for w in normalize_ar(heard_arabic).split() if w]
    if not heard_words:
        return []

    cards = []
    seen = set()  # dedupe identical tips

    for heard_w, exp_bare, label in _align_words(heard_words, expected):
        if not exp_bare or not label or not heard_w:
            continue
        h = _letters_only(heard_w)
        if h == exp_bare:
            continue
        for hc, ec in _align_chars(h, exp_bare):
            if not hc or not ec or hc == ec:
                continue
            tip = FIX.get((hc, ec))
            if not tip:
                # generic fallback for other swaps
                tip = {
                    "plain": f"Heard {hc} instead of {ec} in {label}.",
                    "fix": f"Aim for {ec} in {label} on your next try — listen to Al-Husary on this word.",
                }
            key = (hc, ec, label)
            if key in seen:
                continue
            seen.add(key)
            cards.append({
                "level": "error",
                "rule": "pronunciation",
                "plain": tip["plain"].format(word=label) + " " + tip["fix"].format(word=label),
                "scholarly": f"ASR letter swap on {label}: heard {hc}, expected {ec}.",
                "heard_letter": hc,
                "expected_letter": ec,
                "word": label,
            })

    return cards


def ahad_practice_tip(verse: int) -> dict:
    """Always-useful ahad coaching when qalqalah classifier is unsure."""
    word = "أَحَدٌ / ahad"
    if verse == 2:
        word = "ٱلصَّمَدُ / aṣ-ṣamad"
    elif verse == 3:
        word = "يَلِدْ / yalid"
    return {
        "level": "measured",
        "rule": "qalqalah_practice",
        "plain": (
            f"On {word}: end with a light bounce on the dal (د) — stop, then a small echo, "
            f"not a flat cut-off. Also keep ح / ḥa as a throat H (not soft ه) in ahad."
        ),
        "scholarly": "Practice tip when the bounce classifier is unsure.",
    }
