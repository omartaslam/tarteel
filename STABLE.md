# Deploy markers

## Hard rule — English phonetics (learner lesson 2026-07-28)
**Every coaching cue must use English sounds a beginner can actually make.**

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
### Teach ↔ measure (qhul)
- Romanize **ق → qh** so heard display shows **Qhul / Qhu** (the hollow h learners feel) — not bare “Qul/Qu”.
- Clear **qh / QUAL** phonetics can pass Qu when Arabic ق is missing; **ك / cull** still never passes.
- When ASR writes ك but the learner aimed for QUAL: coaching must say phone ASR often flattens ق→ك — do not pretend we “heard” the hollow qh if the transcript is Kull.
