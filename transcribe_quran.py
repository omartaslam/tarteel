"""
Quranic ASR for the "what the app heard" panel.

XLSR free CTC decode is trained on conversational Arabic (Common Voice) and
produces garbage on tilawah — even on clear Husary. Use a Whisper model
fine-tuned on Quranic recitation instead, then map to vocalized Arabic +
readable English phonetics the learner can verify against the ayah.
"""
import re
import unicodedata

import librosa
import torch
from transformers import WhisperForConditionalGeneration, WhisperProcessor

MID = "basharalrfooh/whisper-small-quran"

# Canonical display forms for Surah Al-Ikhlas (match the UI).
CANONICAL = {
    1: {
        "ar": "قُلْ هُوَ ٱللَّهُ أَحَدٌ",
        "ph": "Qul huwa Allāhu aḥad",
        "bare": "قل هو الله احد",
    },
    2: {
        "ar": "ٱللَّهُ ٱلصَّمَدُ",
        "ph": "Allāhu aṣ-ṣamad",
        "bare": "الله الصمد",
    },
    3: {
        "ar": "لَمْ يَلِدْ وَلَمْ يُولَدْ",
        "ph": "Lam yalid wa lam yūlad",
        "bare": "لم يلد ولم يولد",
    },
    4: {
        "ar": "وَلَمْ يَكُن لَّهُۥ كُفُوًا أَحَدٌ",
        "ph": "Wa lam yakun lahu kufuwan aḥad",
        "bare": "ولم يكن له كفوا احد",
    },
}

# Consonant → Latin for readable phonetics of whatever Whisper actually heard.
_CONS = {
    "ء": "ʾ", "أ": "ʾ", "إ": "ʾ", "ؤ": "ʾ", "ئ": "ʾ", "آ": "ʾā",
    "ا": "ā", "ٱ": "a", "ى": "ā", "ب": "b", "ت": "t", "ث": "th",
    "ج": "j", "ح": "ḥ", "خ": "kh", "د": "d", "ذ": "dh", "ر": "r",
    "ز": "z", "س": "s", "ش": "sh", "ص": "ṣ", "ض": "ḍ", "ط": "ṭ",
    "ظ": "ẓ", "ع": "ʿ", "غ": "gh", "ف": "f", "ق": "q", "ك": "k",
    "ل": "l", "م": "m", "ن": "n", "ه": "h", "ة": "h", "و": "w", "ي": "y",
}
_SHORT = {"َ": "a", "ُ": "u", "ِ": "i", "ً": "an", "ٌ": "un", "ٍ": "in"}
_SHADDA, _SUKUN, _MADDA = "\u0651", "\u0652", "\u0670"


def romanize_ar(text: str) -> str:
    """Readable English phonetics for arbitrary Arabic (incl. diacritics)."""
    if not text:
        return ""
    # word-by-word so article / hamza handling stays local
    words_out = []
    for word in text.strip().split():
        out = []
        i = 0
        s = word
        while i < len(s):
            c = s[i]
            if c in ("\u0640", "ۥ", "ۢ") or ("\u06d6" <= c <= "\u06ed"):
                i += 1
                continue
            base = _CONS.get(c)
            if base is None:
                i += 1
                continue
            i += 1
            geminate = False
            vowel = None  # None = unspecified; "" = explicit sukun
            while i < len(s) and s[i] in (_SHADDA, _SUKUN, _MADDA, *_SHORT):
                m = s[i]
                if m == _SHADDA:
                    geminate = True
                elif m == _SUKUN:
                    vowel = ""
                elif m == _MADDA:
                    vowel = "ā"
                elif m in _SHORT:
                    vowel = _SHORT[m]
                i += 1
            # word-initial alif/wasla before consonants → short 'a' (ال…)
            if c in ("ا", "ٱ") and not out:
                cons = "a"
                chunk = cons + (vowel or "")
                # avoid "aā"
                chunk = chunk.replace("aā", "ā").replace("aa", "a")
                out.append(chunk)
                continue
            if c == "آ":
                out.append("ā")
                continue
            if c in ("ا", "ى") and vowel is None and not geminate:
                out.append("ā")
                continue
            if c == "و" and vowel is None and not geminate:
                # long ū if previous chunk ended with a short vowel, else 'w'
                if out and out[-1] and out[-1][-1] in "aui":
                    out[-1] = out[-1][:-1] + "ū"
                else:
                    out.append("w")
                continue
            if c == "ي" and vowel is None and not geminate:
                if out and out[-1] and out[-1][-1] in "aui":
                    out[-1] = out[-1][:-1] + "ī"
                else:
                    out.append("y")
                continue
            cons = base
            # hamza carriers already include ʾ; drop lone long-vowel from أ/إ base
            if c in ("أ", "إ", "ؤ", "ئ"):
                cons = "ʾ"
            if geminate:
                if cons.startswith(("th", "kh", "dh", "sh", "gh")):
                    cons = cons + cons
                elif cons:
                    cons = cons + cons
            if vowel is None:
                vowel = ""
            # drop tanween-style trailing n sound; keep vowel letter only
            if vowel in ("an", "un", "in"):
                vowel = vowel[0]  # pause-friendly: aḥad not aḥadun
            # ال + shadda assimilation: don't keep a bare 'l' before 'll'
            if (
                geminate
                and out
                and out[-1] == cons[0]  # previous was same undiacritic consonant
                and len(cons) >= 2
            ):
                out[-1] = cons + vowel
            else:
                out.append(cons + vowel)
        w = "".join(out)
        w = w.replace("ʾa", "a").replace("ʾu", "u").replace("ʾi", "i")
        w = re.sub(r"aā", "ā", w)
        words_out.append(w)
    if not words_out:
        return ""
    words_out[0] = words_out[0][:1].upper() + words_out[0][1:]
    return " ".join(words_out)


# Letter-name fallback (legacy) — prefer romanize_ar for display.
SOUND = {
    "ق": "qaf", "ك": "kaf", "ل": "lam", "ه": "ha", "ة": "ha",
    "و": "waw", "ا": "alif", "أ": "hamza", "إ": "hamza", "آ": "aa",
    "ء": "hamza", "ؤ": "hamza", "ئ": "hamza", "ى": "alif", "ي": "ya",
    "ح": "Ha", "خ": "kha", "ع": "ayn", "غ": "ghayn", "د": "dal",
    "ذ": "dhal", "ر": "ra", "ز": "zay", "س": "seen", "ش": "sheen",
    "ص": "Sad", "ض": "Dad", "ط": "Ta", "ظ": "Za", "ف": "fa",
    "ب": "ba", "ت": "ta", "ث": "tha", "ج": "jeem", "م": "meem",
    "ن": "noon", "ٱ": "alif",
}

_proc = _model = None

# Arabic combining marks (tashkeel) + tatweel
_DIAC = re.compile(r"[\u064B-\u065F\u0670\u0640\u06D6-\u06ED]")


def _load():
    global _proc, _model
    if _model is None:
        _proc = WhisperProcessor.from_pretrained(MID)
        _model = WhisperForConditionalGeneration.from_pretrained(MID)
        _model.eval()
    return _proc, _model


def normalize_ar(text: str) -> str:
    """Strip diacritics / tatweel and fold common letter variants for matching."""
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
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _cer(a: str, b: str) -> float:
    """Character error rate (Levenshtein / len(ref))."""
    a, b = normalize_ar(a).replace(" ", ""), normalize_ar(b).replace(" ", "")
    if not b:
        return 1.0 if a else 0.0
    n, m = len(a), len(b)
    if n == 0:
        return 1.0
    prev = list(range(m + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins, delete, sub = cur[j - 1] + 1, prev[j] + 1, prev[j - 1] + (ca != cb)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[m] / m


def _letter_phonetics(text: str) -> str:
    """Deprecated display path — use romanize_ar for learner-facing phonetics."""
    return romanize_ar(text)


def match_ayah(heard: str, preferred_verse: int | None = None):
    """
    Map free ASR text onto Al-Ikhlas when close enough.
    Returns (verse_or_None, matched_arabic, matched_phonetics, match_quality).
    """
    if not heard or not heard.strip():
        return None, "", "", "empty"

    best_v, best_cer = None, 1.0
    for v, canon in CANONICAL.items():
        c = _cer(heard, canon["bare"])
        # slight preference for the ayah the learner selected
        score = c - (0.02 if preferred_verse == v else 0.0)
        if score < best_cer:
            best_cer, best_v = score, v

    if best_v is not None and best_cer <= 0.35:
        c = CANONICAL[best_v]
        quality = "exact" if best_cer <= 0.08 else "close"
        return best_v, c["ar"], c["ph"], quality

    return None, "", "", "raw"


def transcribe_path(path: str, verse: int | None = None) -> dict:
    """
    Transcribe a wav/mp3/m4a path with Quran Whisper.

    heard_arabic / heard_phonetic always reflect the literal capture (your voice).
    matched_* are optional ayah alignment for comparison.
    """
    proc, model = _load()
    wav, _ = librosa.load(path, sr=16000)
    if len(wav) < 1600:  # <0.1s
        return {
            "heard_arabic": "",
            "heard_phonetic": "",
            "heard_raw": "",
            "heard_match": "empty",
            "heard_verse": None,
            "matched_arabic": "",
            "matched_phonetic": "",
        }

    inputs = proc(wav, sampling_rate=16000, return_tensors="pt")
    # Clear stale generation_config values that fight with explicit kwargs
    gen = model.generation_config
    gen.forced_decoder_ids = None
    gen.suppress_tokens = None
    gen.begin_suppress_tokens = None
    gen.max_length = 128  # keep > max_new_tokens to avoid dual-limit warning
    with torch.no_grad():
        ids = model.generate(
            inputs.input_features,
            language="arabic",
            task="transcribe",
            max_new_tokens=64,
            do_sample=False,
            num_beams=1,
        )
    raw = proc.batch_decode(ids, skip_special_tokens=True)[0].strip()
    matched_v, matched_ar, matched_ph, quality = match_ayah(raw, preferred_verse=verse)
    raw_ph = romanize_ar(raw)
    return {
        # Primary "what I heard" = literal ASR of this take
        "heard_arabic": raw,
        "heard_phonetic": raw_ph,
        "heard_raw": raw,
        "heard_match": quality,
        "heard_verse": matched_v,
        "matched_arabic": matched_ar,
        "matched_phonetic": matched_ph,
    }
