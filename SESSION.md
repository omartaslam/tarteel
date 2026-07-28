# Tarteel — session handoff

Last updated: 2026-07-28 (stage-clear UX; word-first; live tester care)

## Live tester care
Mom is testing production. **Do not wipe practice on deploy or header tap.**
Clear only via explicit “Clear practice history” button.

## Freeze rule
**Qu letter gate unchanged:** ASR ق pass / ك fail.

## Pedagogy (ayah 1) — word first
1. **Qul** ×3 → pass with ق → **huwa** (locks qu+ul).
2. After 3 word fails → syllable rescue Qu×3 → ul → huwa.
3. After 3 Qu syllable fails → ask a teacher.

## Pass / fail UX (this deploy)
- Pass: green **Stage N cleared · next step** banner with **Hear only {word}** (Husary clip), not full-ayah “Hear it right”.
- Fail: pink “what the app heard”; retry = **Try {current} again** (not “try this ayah again”).
- Top “Listen first” stays full-ayah Husary.

## Backlog
- Word-first ×3 → syllables ×3 → defer across rest of surah.
- Progress UI ~17% stall.
- More stage word clips for ayahs 2–4.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7`.
