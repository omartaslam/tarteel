# Tarteel — session handoff

Last updated: 2026-07-28 (freeze Qu · ship ayah-1 ul)

## Freeze rule (this cycle)
**Do not touch Qu detection** unless `/sessions` shows a real regression vs stable.
Stable rule: ASR ق pass / ك fail. Tag: `stable-qu-detection` (`e6878cd`).

## Where we are
- Qu gate restored + proven (Ku fail, Qu lock).
- Ladders exist for all 4 ayahs (24 stages) — scaffolding mostly done.
- Usage burn was Qu experiments; path forward is batch-test + blocker fixes only.

## Public-ready definition
Beginner can lock every stage through ayah 4 with honest pass/fail and clear next step.
Not a full phonetic examiner.

## Current focus — ayah 1 `ul`
Gate: clear L / “ul” → lock → `qul`. Onset-only (Qu/Ku without L) → stay.
Header tap asks before clearing history (Cancel = keep locked stages).

### Omar batch (do NOT clear between takes)
1. Hard-refresh → **Cancel** on clear prompt (keep Qu lock if you have it). If on Qu: one good Qu first.
2. Stage should say **ul**. Yellow mark on the L part of Qul.
3. Takes in one batch:
   - good `ul` → expect **Locked ul → Qul**
   - Qu-only (no L) → stay, ask for L
4. Reply `chk log` — I read `/sessions`, fix only blockers, one ship.

## Next after ul locks
`qul` (ك must fail → step back to Qu) → `huwa` → joins → `ahad` → `full` → ayah 2–4 smoke.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7`. Build via `/health`.
