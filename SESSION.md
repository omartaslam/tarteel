# Tarteel — session handoff

Last updated: 2026-07-28 (Qu / ul micro-stages)

## Where we left off
- **Omar stuck on Qul:** logs kept hearing `Kull`/`Kulla` (ك, English K) — never ق. Full-word stage was grinding.
- **Fix in flight:** split ayah-1 start into **Qu → ul → Qul** micro-stages.
  - `qu` / `ul` use syllable drill scoring (not full ayah alignment).
  - If full `qul` still shows ك→ق, step back to `qu`.
- **Practice store:** `tarteel_practice_v4` (clears v3 on load / new build).
- **Agreed product rules:** generic adult-male audience; no personal hardcoding; self-contained; clear practice on new deploy.

## How to resume
1. Hard-refresh live site after deploy (tap green header).
2. Stage 1 starts at **Qu** (قُ) only — deep Q + short u, no L yet.
3. Then **ul**, then join **Qul**.

## Stack reminder
- Railway deploys from `main`. Sessions wipe on redeploy.
- Practice mastery/stages live in device `localStorage` (`tarteel_practice_v4`).
