# CONTINUE HERE — next agent

**Owner:** Omar (`omartanveeraslam@gmail.com`)
**Live:** https://tarteel-production.up.railway.app
**Deploy:** `main` → Railway. A branch is not live. Check `GET /health`.
**Live build:** `ebc810a79b9c`

---

## Status — three fixes, all verified on live

### 3. ق vs ك gate — FIXED (`ebc810a`)
The rescue used to read letters from **forced alignment against the expected
ayah**, which can only emit the letters you ask for. It reported "ق present, ك
absent" for the kaf benchmark, English "cool", white noise and **digital
silence**, so the Qul stage passed anything.

Now `analyze_xlsr.onset_probe` reads the **free** emissions and
`coach.onset_qaf_verdict` needs p(ق) ≥ 0.60 with p(ك) ≤ 0.30. Live results:

| Input | live | p(ق) / p(ك) |
|-------|------|-------------|
| Husary Qul / male Qul | pass | 1.00 / 0.00 |
| Minshawi Qul | pass (Whisper reads قُلْ; no rescue needed) | 0.00 / 0.00 |
| kaf benchmark | **fail** | 0.00 / 1.00 |
| kaf letter | **fail** | 0.00 / 1.00 |
| English "cool" | **fail** | 0.00 / 0.98 |
| white noise / silence | **fail** | 0.00 / 0.00 |

Guarded by `test_qaf_kaf_benchmark.py`. **Do not loosen the thresholds** to make
one clip pass — `real_qul_minshawi` is deliberately excluded from the acoustic
list because XLSR does not resolve ق on that 0.55s cut, and Whisper covers it.

---

## Status of the two things Omar was chasing — both fixed and verified on live

### 1. Hear-only huwa — FIXED
Root cause: Husary recites **"Qul huwa" joined** — in his murattal *and* in his
Muallim (teaching) recitation. There is no silence between the words, so every
slice was wrong in one of two ways:

| Attempt | Window | What Omar heard |
|---------|--------|-----------------|
| `?v=3` | 1.22–1.95 | started inside Qul leftover |
| `?v=4` | 1.45–1.88 | ه onset cut off, and ~7 dB quieter than every other clip (a 2.5× gain cap) |

Fix: stop slicing. `stage_huwa_word.mp3` is an **isolated word-by-word
recording** (`audio.qurancdn.com/wbw/112_001_002.mp3`), normalized to the
ladder's loudness. XLSR decodes the whole encoded file as **هُوَ** with no
ق/ل/ا. Attribution is in `static/samples/SOURCES.txt` — it is *not* Husary,
so the UI sub-label says "Word-by-word recitation".

### 2. Allāhu card reading previous Qul results — FIXED
Not stale audio and not a previous recording. Aligning a lone **الله** against
the whole ayah let **قل** consume the letters **ال** and **هو** consume **ه**,
so Allāhu scored a miss on its own stage and `detect_repeated_earlier_word`
then blamed Qul. **aḥad was silently broken the same way.**

Verified live end-to-end (session `20260728-203723-ae0329`): a real Allāhu take
returns "Stage 6 cleared: Allāhu", no `wrong_stage` card.

---

## P0 next — re-measure Qul accuracy from scratch

The gate is fixed, but every take that produced the old "~70–80%" figure was
scored by the broken gate, so **that number is void** (retracted in
`HANDOVER.md` §1). Nothing may be quoted to a scholar or backer until it is
re-measured on the current build:

- N ≥ 30 adult-male phone takes, teacher-labelled, ق vs ك confusion matrix.
- Report per stage, not just Qul.
- Re-check how often the rescue is actually needed now — if Whisper's ق is
  usually present, the rescue should be rare, and a rescue that fires
  constantly is a warning sign that it has gone vacuous again.

Then extend the benchmark battery to the other confusable pairs: و/ف on huwa,
ح/ه on aḥad, doubled ل on Allāhu.

---

## A regression I introduced and reverted — read this before touching alignment

The first Allāhu fix also made single-word stages compare the **whole take**
against that word. That turned the documented live pass **`قَوْلَهُ`**
(HANDOVER §1, session `20260728-140251`) into a miss on Qul, because Whisper's
extra letters no longer had anywhere to go.

Reverted. `_align_stage` now only **scopes** the expected list to the stage and
still calls `_align_words`, so partial takes stay a tolerant `near`. The
wrong-stage card is gated on a clear `ok` instead. Covered by
`test_stage_detection_matrix_no_regression` in `test_qul_drills.py`.

**Lesson:** Qul is the first word, so whole-ayah alignment never hurt it — that
is why it felt stable while Allāhu and aḥad were broken. Any alignment change
must be run against the documented takes before shipping.

---

## Hard operator rules (Omar)

1. **Live only.** `/health` must show your SHA before you claim anything.
2. **Never ship audio you have not verified**, and say plainly that an agent
   cannot hear — verify by decoding the *encoded, served* bytes, plus level and
   silence bookends. RMS alone is not enough; `?v=4` passed an RMS check.
3. **Bump `?v=`** on any sample change; phones cache hard.
4. Header tap clears practice with no confirm (Omar chose 4C). Mom: careful.
5. Do not change detection thresholds/gates without justification and evidence.

---

## English mouth cues (START HERE every session)

1. **QUALITY** — ق = QUAL / QUA like *quality*
2. **PULL** — ul = end of *pull* / *full*
3. huwa = **HOO-wa** · Allāhu = **Al-LAA-hu** · aḥad = **a-ḤAD**

Labels stay **Qul/Qu** (not Qhul).

---

## Journey decisions (locked 2026-07-28)

1. First visit: Listen = whole surah once → then current Say. Later: this ayah + Continue.
2. Compare under Hear only.
3. Qul ×3 then Qu rescue.
4. Header clears practice, no confirm, hard refresh.
5. Promo: ayah 1 first; full 112 later.
6. Ayah 2: Allāhu → aṣ-ṣamad → join.

Practice store `tarteel_practice_v7`; resume `tarteel_last_verse_v1`.

---

## Tests

```bash
python -m pytest -q          # 75 tests
```

- `test_qaf_kaf_benchmark.py` — real audio: ق passes, ك / "cool" / noise /
  silence fail. **The guard that was missing.**
- `test_qul_drills.py` — detection matrix, Qul ق/ك, Allāhu/aḥad regressions
- `test_stage_clips.py` — clip duration, **audible level**, speech length,
  clean bookends, and that every clip the UI references exists
- `test_stage_contract.py` — every stage owns hear + compare

---

## Key files

| Path | Why |
|------|-----|
| `CONTINUE.md` | this file |
| `HANDOVER.md` | full project / scholar-facing |
| `SESSION.md` | short live status |
| `STABLE.md` | hard rules |
| `coaching.py` | `_align_stage`, `onset_qaf_verdict` (ق/ك thresholds), compare |
| `analyze_xlsr.py` | `onset_probe` — free-emission ق/ك evidence |
| `elements.py` | `build_feedback`, stage pass/fail, rescue wiring |
| `test_qaf_kaf_benchmark.py` | real-audio ق/ك guard — keep it green |
| `scripts/rebuild_stage_word_clips.py` | ayah-1 slices (no huwa — isolated source) |
| `static/samples/SOURCES.txt` | provenance, incl. why huwa is not Husary |
