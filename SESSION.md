# Tarteel — session handoff

Last updated: 2026-07-28 (Qul live lock; QUALITY + PULL cues; phone ASR rescue)

Full handover (scholar summary + P0 + deploy): see `HANDOVER.md`.

## START HERE NEXT SESSION — English mouth cues (non-negotiable)
These two anchors unlocked adult-male **Qul** on phone. Lead with them every time:

1. **QUALITY** — onset of ق / Qu / Qul = **QUAL / QUA** like the start of *quality* (hollow **qh**). Never teach “Qul” as cull/cool (that’s ك). Not “ghwal” (drifts to غ).
2. **PULL** — ending **ul** = end of *pull* / *full* (short u + clear L).

**Together:** QUALITY onset + PULL ending → **Qul**.  
Split them when teaching; don’t mush into one vague “Quaull”.

Apply the same standard to later words (HOO-wa, Al-LAA-hu, a-ḤAD). See `STABLE.md`.

## Live tester care
Mom is testing production. **Do not wipe practice on deploy or header tap.**
Clear only via explicit “Clear practice history” button.

## Freeze rule
**Qu / Qul:** letter-track / ASR **ق** pass; **ك** fail.
**Phone rescue:** Whisper ك + XLSR onset ق (not ك) → pass.
**Qul lock** needs ق evidence — shape-near without ق does not advance.

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
Everyayah male murattal Qul cuts → pass when ق evidence present. Kaf bench fails.
Phone rescue live on build `4df95c7`+. Milestone: `20260728-163050` Qul → huwa (Whisper Kullu, letters قل).

## Backlog / P0 (see HANDOVER.md §6)
- Five UX decisions still open (first action, compare vs Record fold, fail×3, clear button, …).
- Formal male-adult % for Qul; then huwa / Allāhu / aḥad; target ≥80% across Surah 112 before scholar cohort.
- Mom / female voice = separate track.
- Incorrect clips; ayat 2–4 stage contract fill; progress ~17% stall.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7`. Live: https://tarteel-production.up.railway.app
