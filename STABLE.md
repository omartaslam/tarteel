# Deploy markers

## Hard rule — ق/ك must be decided from unconstrained audio (fixed `ebc810a`)
**Never** derive a letter identity from forced alignment. Forced alignment is
constrained to the expected ayah, so it can only emit the letters you asked
for. The old `align_onset_qaf` did exactly that and reported "ق present, ك
absent" for the kaf benchmark, English "cool", white noise and digital silence
— every take passed Qul.

Now `analyze_xlsr.onset_probe` reads the free emissions and
`coach.onset_qaf_verdict` requires p(ق) ≥ 0.60 with p(ك) ≤ 0.30 (and the
mirror). An ambiguous onset locks nothing. `test_qaf_kaf_benchmark.py` runs the
real clips: ق clips must pass, and the kaf pair, "cool", noise and silence must
all fail. Do not loosen those thresholds to make a single clip pass.

## Hard rule — do not ship unheard audio (2026-07-28 evening)
Hear-only / Compare clips must be verified after `/health` bumps before asking Omar to test.
RMS / md5 checks are not enough — huwa `?v=4` passed an RMS check and was still wrong.
Verify the **encoded, served bytes**: decode them, check level parity with the other
clips, speech duration, and silence bookends. Husary recites "Qul huwa" joined, so
huwa cannot be sliced from the ayah — it uses an isolated word recording.

## Hard rule — never change alignment without the detection matrix
Qul is the ayah's first word, so whole-ayah alignment never hurt it while Allāhu and
aḥad were silently broken. Run `test_stage_detection_matrix_no_regression` (documented
live takes, incl. `قَوْلَهُ`) before shipping any alignment change.

## Hard rule — stage UI prototype (2026-07-28)
**Every practice stage owns its own Hear only + Correct/Incorrect.**

Ayah 1 is the filled prototype. Replicate the same shape for every later step:

- `hear` — clip for **this** step only
- `compare` — `{note, ok:{src,title,sub}, bad:{src,title,sub}}` for **this** step
- UI always renders both for the **live** stage — never a hard-coded Qul-only pair
- `bad.src` may be empty until the incorrect clip exists; the Incorrect row still shows
- New stages: copy an ayah-1 stage object, swap say/hint/clips — do not invent a side map

See `STAGE CONTRACT` in `static/index.html` and `test_stage_contract.py`.

## Hard rule — English phonetics (learner lesson 2026-07-28)
**Every coaching cue must use English sounds a beginner can actually make.**

**Lead descriptors for ق / Qul (non-negotiable):**
- ***quality*** → onset **QUAL / QUA** (hollow qh)
- ***pull*** → ending **ul**
- Together (taught split): QUALITY + PULL → **Qul**

- Scholarly transliteration (Qul, Qu, aḥad) is a *label*, not always the mouth cue.
- If the English spelling reads as the *wrong* sound to a native English speaker, the tip has failed
  (example: teaching “Qul” → people say cull/cool/ك; correct cue was **QUAL** like *quality*).
- Prefer: familiar English word anchors (“quality”, “who”, “lot”, “ahead”) over abstract
  “deep / heavy / throat” jargon alone.
- Apply on **every** future tip — word, syllable, letter, join — big or small. Do not ship vague phonetics.

## stable-qu-detection — 2026-07-28

**Commit / build:** `e6878cde0424`  
**Git tag:** `stable-qu-detection`  
**Live health:** `{"ok":true,"build":"e6878cde0424"}`

### Why this is marked stable
Omar produced a successful **back ق (Qu)** lock on this build:

- Session `20260728-092902-94fcca`
- Display: `قُ` / `Qu`
- Action: **Locked Qu → ul**
- Middle-ك takes around it correctly **failed** (`ك→ق`)

Detection rule on this build: analyse each take — **ق passes, ك fails**. No “ك counts as pass” shortcut.

### Do not regress
Do not reintroduce `pass if ك OR ق` on the Qu drill, and do not demote full-word `ك→ق` to a non-blocking tip on the Qul stage.

### Phonetic breakthrough (same journey)
Lock succeeded when the English cue became **QUAL / QUA like quality**, not “Qul/cull/cool”.
Keep that cue in coaching. Extend the same standard to all later stages.
### Teach ↔ measure
- Written label: **Qul / Qu** (not “Qhul” on the ayah line).
- Mouth cue: **QUAL / QUA like *quality*** (hollow qh) — never cull/cool.
- Clear **qh / QUAL** phonetics can still pass Qu when Arabic ق is missing; **ك / cull** still never passes.
- **Phone ASR flatten:** Whisper often writes ك for real ق on phone mics. If XLSR letter-track onset shows **ق** (and not ك), **pass**.
- When ASR writes ك but the learner aimed for QUAL: coaching must say phone ASR often flattens ق→ك — do not pretend we “heard” hollow qh if the transcript is Kull *and* the letter track also lacks ق.
