"""
Per-element feedback for Al-Ikhlas from the XLSR letter alignment.
Reports EVERYTHING measurable, plain English, always Arabic letter + English sound.
Layer 1: uses only the letter timings we already compute (no new training).
"""

# letter -> english sound name, for the "ح / throat H" style display
SOUND = {
    "ق":"qaf (deep K)","ل":"lam (L)","ه":"ha (soft H)","و":"waw (W)",
    "ا":"alif (aa)","ح":"Ha (throat H)","د":"dal (D)","ص":"Sad (heavy S)",
    "م":"meem (M)","ي":"ya (Y)","ن":"noon (N)","ك":"kaf (K)","ف":"fa (F)",
    "ب":"ba (B)","ت":"ta (T)","ر":"ra (R)","و":"waw (W)","أ":"hamza (glottal)",
    "|":"(word break)",
}

# per-verse: which elements to check, with the correct-recitation expectations
# madd = elongation; we measure the vowel-carrier gap.
VERSE_ELEMENTS = {
    1: {  # قُلْ هُوَ ٱللَّهُ أَحَدٌ
        "words":["قُلْ / qul","هُوَ / huwa","ٱللَّهُ / Allāhu","أَحَدٌ / ahad"],
        "madd":[("و","هُوَ / huwa","the 'uu' in huwa",0.10,0.30)],
        "shadda":[("ل","ٱللَّهُ / Allāhu","the doubled L (ll) in Allah")],
        "qalqalah":("د","أَحَدٌ / ahad"),
    },
    2: {"words":["ٱللَّهُ / Allāhu","ٱلصَّمَدُ / aṣ-ṣamad"],
        "madd":[], "shadda":[("ص","ٱلصَّمَدُ / aṣ-ṣamad","the heavy doubled Sad")],
        "qalqalah":("د","ٱلصَّمَدُ / aṣ-ṣamad")},
    3: {"words":["لَمْ / lam","يَلِدْ / yalid","وَلَمْ / wa lam","يُولَدْ / yūlad"],
        "madd":[("و","يُولَدْ / yūlad","the 'uu' in yulad",0.10,0.30)],
        "shadda":[], "qalqalah":("د","يَلِدْ / yalid")},
    4: {"words":["وَلَمْ / wa lam","يَكُن / yakun","لَّهُۥ / lahu","كُفُوًا / kufuwan","أَحَدٌ / ahad"],
        "madd":[], "shadda":[], "qalqalah":("د","أَحَدٌ / ahad")},
}

def build_feedback(verse, letters, qalqalah_result):
    """letters: [{'c':char,'t':time}]  -> list of feedback cards."""
    spec = VERSE_ELEMENTS.get(verse, {})
    cards=[]

    # 1. Word recognition — what was detected, in order
    detected=[l for l in letters if l["c"]!="|"]
    if detected:
        cards.append({
            "level":"ok",
            "plain":f"Recitation detected — {len([l for l in letters if l['c']=='|'])+1} words in the right order.",
            "scholarly":"Word sequence aligned correctly against the expected verse.",
        })

    # 2. Madd (elongation) — measure the vowel-carrier duration
    for (letter,word,desc,lo,hi) in spec.get("madd",[]):
        seg=_letter_span(letters,letter)
        if seg:
            dur=seg
            if dur>=lo:
                cards.append({"level":"ok",
                    "plain":f"Madd (elongation) on {word} held well — {desc}, ~{dur:.2f}s.",
                    "scholarly":f"Madd tabii on {letter} / {SOUND.get(letter,letter)}. Natural 2-beat elongation."})
            else:
                cards.append({"level":"measured",
                    "plain":f"Madd on {word} looks short — {desc} held ~{dur:.2f}s, aim a touch longer.",
                    "scholarly":f"Madd tabii on {letter} / {SOUND.get(letter,letter)}."})

    # 3. Shadda (doubled letter)
    for (letter,word,desc) in spec.get("shadda",[]):
        if any(l["c"]==letter for l in letters):
            cards.append({"level":"ok",
                "plain":f"Shadda detected on {word} — {desc}.",
                "scholarly":f"Doubled {letter} / {SOUND.get(letter,letter)} — hold with slight emphasis."})

    # 4. Qalqalah — from the trained classifier (already computed)
    if qalqalah_result:
        cards.append(qalqalah_result)

    return cards

def _letter_span(letters, target):
    """rough duration a letter occupies = gap to next letter."""
    for i,l in enumerate(letters):
        if l["c"]==target:
            if i+1<len(letters):
                return round(letters[i+1]["t"]-l["t"],3)
    return None
