# CONTINUE HERE — next agent

**Owner:** Omar (`omartanveeraslam@gmail.com`)
**Live:** https://tarteel-production.up.railway.app
**Deploy:** `main` → Railway. A branch is not live. Check `GET /health`.
**Live build:** `b32755d1b0fa`

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

## P0 — the phone-ASR rescue gate is vacuous (PRE-EXISTING, still live)

**This is now the most important accuracy issue in the project.**

`coach.align_onset_qaf` decides the phone rescue: "if the XLSR letter track
shows ق and not ك, pass". But the letters it reads come from **forced
alignment against the expected ayah text** (`VTEXT[1] = "قل هو الله احد"`).
Forced alignment is constrained to emit the target letters, so it can only ever
produce ق and can never produce ك — **whatever the audio contains.**

Measured on build `b32755d` (identical on the pre-change build `54460c9`, so
this is not from the recent alignment work):

| Input | `align_onset_qaf` |
|-------|-------------------|
| real ق Qul | `has_qaf=True, has_kaf=False` |
| kaf benchmark `bench_incorrect_kaf_kul_fjmustak` | `has_qaf=True, has_kaf=False` |
| English "cool" | `has_qaf=True, has_kaf=False` |
| aḥad / Allāhu (wrong word entirely) | `has_qaf=True, has_kaf=False` |
| **white noise** | `has_qaf=True, has_kaf=False` |
| **digital silence** | `has_qaf=True, has_kaf=False` |

Consequence: the rescue fires on every take, so **the Qul stage passes the kaf
benchmark on live** — confirmed by POSTing it to `/analyze`. That directly
violates the `STABLE.md` rule "ك must not pass as ق", and it means the
"~70–80% male-adult Qul" figure in `HANDOVER.md` cannot be trusted: we do not
know how much of that was the gate passing everything.

**Deliberately not fixed in this session.** Omar asked that the audio analysis
not be changed without justification, and repairing this changes pass/fail for
the stage he is actively testing. It needs his go-ahead.

Fix direction when approved:
- Judge ق vs ك from **free CTC decoding** of the onset (unconstrained), or from
  the acoustic classifier — never from forced alignment against expected text.
- Re-run the ق/ك benchmark pair as an automated test: `bench_correct_*` must
  pass, `bench_incorrect_*` must fail. Add white noise and silence as must-fail.
- Only then re-state any accuracy number.

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
python -m pytest -q          # 58 tests
```

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
| `coaching.py` | `_align_stage`, `align_onset_qaf` (**vacuous — see P0**), compare |
| `elements.py` | `build_feedback`, stage pass/fail, rescue wiring |
| `scripts/rebuild_stage_word_clips.py` | ayah-1 slices (no huwa — isolated source) |
| `static/samples/SOURCES.txt` | provenance, incl. why huwa is not Husary |
