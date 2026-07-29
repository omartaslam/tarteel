# Tarteel — session handoff

Last updated: 2026-07-28 ~20:58 UTC

**Full:** `HANDOVER.md` · **Next agent start:** `CONTINUE.md`

## LIVE NOW
`/health` → **`ebc810a79b9c`** — hard-refresh the phone before testing.

Three fixes, all verified against live:

1. **Hear-only huwa** — Husary recites "Qul huwa" joined, so no slice works.
   Now an isolated word-by-word recording (`stage_huwa_word.mp3`, `?v=5`),
   level-matched to the other clips. Decodes as هُوَ.
2. **Allāhu card blaming Qul** — whole-ayah alignment let قل eat the letters ال,
   so Allāhu missed on its own stage. aḥad was broken the same way. Both pass now.
3. **ق vs ك gate** — was read from forced alignment, which can only emit the
   expected letters, so silence "contained" ق and everything passed Qul. Now read
   from an unconstrained decode of the onset. On live: real Qul passes; kaf
   benchmark, kaf letter and English "cool" fail.

## Next
Re-measure Qul accuracy from scratch (N≥30, teacher-labelled, ق/ك confusion
matrix). The old ~70–80% figure was scored by the broken gate and is void.

## START HERE — English mouth cue (measured 2026-07-29, replaces QUALITY)
> **throat from "CALL" + vowel from "PULL" = Qul**

Say **CAW-l**, freeze the throat, change only the vowel to the short u in *pull*.

Measured in Omar's own voice, same session, stable across 4 cut boundaries:
his "call" produces real deep-throat-K, "qaf" (ق), at **0.93**; his "quality"
produces the normal English K, "kaf" (ك). **QUALITY is retired as a cue** — it
was making him say KWOL. Labels stay **Qul/Qu**.

## Journey decisions (Omar 2026-07-28) — locked
1. First visit: whole-surah Listen once → current Say. Later: this ayah + Continue.
2. Compare under Hear only.
3. Qul ×3 then Qu rescue.
4. Header tap: clear practice **no confirm** + hard refresh.
5. Promo: ayah 1 first; full 112 later.
6. Ayah 2: Allāhu → aṣ-ṣamad → join; English cues.

## Freeze rule
ق pass / ك fail — now actually enforced, guarded by `test_qaf_kaf_benchmark.py`.
Never decide a letter from forced alignment.

## Stack
Railway `main`. Practice `tarteel_practice_v7`. https://tarteel-production.up.railway.app
