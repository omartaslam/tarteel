# Tarteel — session handoff

Last updated: 2026-07-28 ~20:40 UTC

**Full:** `HANDOVER.md` · **Next agent start:** `CONTINUE.md`

## LIVE NOW
`/health` → **`b32755d1b0fa`**

Both of Omar's bugs are fixed and verified on live:
1. **Hear-only huwa** — Husary recites "Qul huwa" joined, so no slice works.
   Now an isolated word-by-word recording (`stage_huwa_word.mp3`, `?v=5`),
   level-matched. Decodes as هُوَ. Hard-refresh to clear the phone cache.
2. **Allāhu card blaming Qul** — whole-ayah alignment let قل eat the letters ال.
   Verified live end-to-end (session `20260728-203723-ae0329`): "Stage 6
   cleared: Allāhu", no wrong_stage card. aḥad was broken the same way.

## P0 next — ق/ك rescue gate is vacuous (pre-existing, needs Omar's go-ahead)
`align_onset_qaf` reads letters from forced alignment against the expected
ayah, so it reports ق-present/ك-absent for **any** audio — kaf benchmark,
English "cool", white noise, silence. The kaf benchmark passes Qul on live.
The ~70–80% Qul figure in HANDOVER is retracted until this is rebuilt.

## START HERE — English mouth cues
1. **QUALITY** — ق onset = QUAL / QUA like *quality*
2. **PULL** — ul = end of *pull* / *full*
Together → **Qul**. Labels stay **Qul/Qu**.

## Journey decisions (Omar 2026-07-28) — locked
1. First visit: whole-surah Listen once → current Say. Later: this ayah + Continue.
2. Compare under Hear only.
3. Qul ×3 then Qu rescue.
4. Header tap: clear practice **no confirm** + hard refresh.
5. Promo: ayah 1 first; full 112 later.
6. Ayah 2: Allāhu → aṣ-ṣamad → join; English cues.

## Freeze rule
ق pass / ك fail. The phone rescue is currently NOT enforcing this — see P0.

## Stack
Railway `main`. Practice `tarteel_practice_v7`. https://tarteel-production.up.railway.app
