# Tarteel — session handoff

Last updated: 2026-07-28 (wrong-stage false-fail; FOCUS vs Hear only)

## Live tester care
Mom is testing production. **Do not wipe practice on deploy or header tap.**
Clear only via explicit “Clear practice history” button.

## Freeze rule
**Qu letter gate unchanged:** ASR ق pass / ك fail.

## Pedagogy (ayah 1) — word first
1. **Qul** ×3 → pass with ق → **huwa** (locks qu+ul).
2. After 3 word fails → syllable rescue Qu×3 → ul → huwa.
3. After 3 Qu syllable fails → ask a teacher.

## Pass / fail UX
- Pass: green **Stage N cleared · next step** + **Hear only {next word}**.
- Fail: **FOCUS** (not NEXT STEP). Hear only for the word you’re on.
- If you re-say a locked word (Qul again on huwa): **Wrong word for this step** — not a mystery huwa miss.
- Word/drill stages do not require final dal / qalqalah.

## If a “correct” take fails
1. Check the pink **what the app heard** line (Arabic + English).
2. If it shows **ك / Kul** — ASR heard middle K (stable fail).
3. If it shows **قل / Qul** but you’re on **huwa** — say only huwa now.
4. Hard-refresh keeps progress.

## Backlog
- Word-first ×3 → syllables ×3 → defer across rest of surah.
- Progress UI ~17% stall.
- More stage word clips for ayahs 2–4.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7`.
