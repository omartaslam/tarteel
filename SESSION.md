# Tarteel — session handoff

Last updated: 2026-07-28 (word-first Qul; live tester care)

## Live tester care
Mom is testing production. **Do not wipe practice on deploy or header tap.**
- Header = refresh only (progress kept)
- Deploy = keep `tarteel_practice_v7` progress
- Clear only via explicit “Clear practice history” button

## Freeze rule
**Qu letter gate unchanged:** ASR ق pass / ك fail. Tag: `stable-qu-detection`.

## Pedagogy (ayah 1) — word first
1. **Qul** (full word) — up to **3** tries. Pass with ق → lock qul (+qu,+ul) → **huwa**.
2. After 3 word fails → **syllable rescue**: Qu (×3) → ul → huwa.
3. After 3 Qu syllable fails → **ASK A TEACHER** (no fake lock).

Same pattern to roll out to later words/ayat once proven.

## Backlog (later)
- If Qul take has both ق and L clearly, already skips to huwa (done on word pass).
- Progress UI: ~17% stall then jump.
- Apply word-first ×3 → syllables ×3 → defer across rest of surah.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7` (do not bump without need).
