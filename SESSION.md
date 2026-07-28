# Tarteel — session handoff

Last updated: 2026-07-28 (Qu acoustic corpus cluster — hybrid gate)

## Stable Qu detection baseline
- **Tag / file:** `stable-qu-detection` / `STABLE.md`
- **Commit:** `e6878cde0424` — first successful Qu lock; no ك-as-pass.

## Qu acoustic v1 (this deploy)
Hybrid gate on Qu drill only:

1. **Acoustic cluster** trained on adult male EveryAyah Qul onsets (correct ق) vs middle-ك / Kul clips (`data/qu_corpus/`, model `models/qu_qaf_cluster.pkl`).
2. **PASS** only if ASR shows ق **and** acoustic matches the correct cluster.
3. **FAIL** if ASR shows ك (never lock Qu on kaf).
4. **DEFER** (clear reason, no lock) if ASR ق but acoustic unsure / disagrees.

False lock is worse than an occasional defer. Ul / later stages unchanged.

## UI (already on main)
- No “No L yet” on Qu; yellow-mark Qu/قُ on ayah lines.

## Retest checklist
1. Hard-refresh (tap green header).
2. Qu: your middle-K → fail.
3. Qu: incorrect ك sample → fail.
4. Qu: your good back-ق → lock → ul (or defer if unsure — try again).
5. Confirm `/health` build matches this deploy.

## Stack
Railway from `main`. Practice store `tarteel_practice_v6`.
