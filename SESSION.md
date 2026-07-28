# Tarteel — session handoff

Last updated: 2026-07-28 (QUAL English cue for ق; stage compare; Qu rescue play)

## Live tester care
Mom is testing production. **Do not wipe practice on deploy or header tap.**
Clear only via explicit “Clear practice history” button.

## Freeze rule
**Qu letter gate unchanged:** ASR ق pass / ك fail.
**Qul lock also requires ق** in the take — shape-near without ق does not advance.

## English phonetics — hard rule (this breakthrough)
Written labels ≠ mouth cues. If English spelling makes beginners say the wrong sound, the tip failed.
- ق / Qul → teach **QUAL / QUA like quality** (not cull/cool)
- Qu → **QUA like quality**
- ul → end of **pull / full**
- huwa → **HOO-wa** (who + wa)
- Allāhu → **Al-LAA-hu** (hold ll)
- aḥad → **a-ḤAD** (fog-mirror Ḥ, not soft “ahead”)
Apply on every future tip. See `STABLE.md`.

## Pedagogy (ayah 1) — word first
1. **Qul** ×3 → pass with ق → **huwa** (locks qu+ul).
2. After 3 word fails → syllable rescue **Qu** ×3 (not full Qul) → ul → huwa.
3. After 3 Qu syllable fails → ask a teacher.

## Pass / fail UX
- Every stage shows **Hear only {current}** + **Correct/Incorrect for {current}** (stage contract on `STAGE_LADDER`).
- Ayah 1 is the filled prototype; ayahs 2–4 use the same `hear` + `compare` shape (stubs until clips).
- Do **not** hard-code a Qul-only compare panel — replicate per stage and move on.
- Syllable rescue entry: banner **Say: Qu** + Hear only Qu (not mixed Qul copy).
- Card ayah snippet for Qu marks **Qu** inside Qul, not the whole word.
- **Heard vs target** on a word stage only shows that stage’s word(s) — never yellow the whole ayah for a one-word take.
- Fail tag **FOCUS**. Stage-clear still says NEXT STEP.

## Detection note (male Qul battery)
Everyayah male murattal Qul cuts (Alafasy, Basit, Ghamadi, Maher, Shaatree, Minshawi bench,
qul_correct_male) → pass when ASR shows ق. Kaf bench fails. Phone/mic takes that ASR as ك
still fail by design.

## Backlog
- Fill incorrect clips for huwa / Allāhu / aḥad (Incorrect row already stage-scoped).
- Fill `hear` + real `compare` clips for ayahs 2–4 using the same stage contract.
- Word-first ×3 → syllables across rest of surah.
- Progress UI ~17% stall.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7`.
