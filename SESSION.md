# Tarteel — session handoff

Last updated: 2026-07-28 (Qu acoustic probe — did **not** ship)

## Stable marker (do not regress)
- **Tag / file:** `stable-qu-detection` / `STABLE.md`
- **Commit / build:** `e6878cde0424`
- Successful Qu lock (session `20260728-092902-94fcca`). **ق passes, ك fails** via ASR letters. No ك-as-pass.

## Live UI (on main)
- Qu hint no longer says “No L yet”
- Yellow-mark Qu/قُ on ayah lines
- Build at last check: see `/health`

## Qu acoustic v1 — probe result (2026-07-28)
Tried to add throat-level ق vs ك (not Whisper letters):

| Approach | Result on Omar + bench takes |
|---|---|
| MFCC/spectral logistic clf | LOO ~55%; **swapped** Omar good Qu ↔ Ku |
| XLSR frame ق/ك mass | Tiny probs; ratios unreliable on short Qu |
| Forced-align قل vs كل margin | **Omar’s correct Qu scored toward ك** |

**Decision: do not ship.** Would regress stable Qu locks / trust. Product stays ASR letter gate until we have enough labeled Qu/Ku takes (many phones/voices) for a real place-of-articulation model.

### Trust policy (agreed)
- Quran: no room for false “locked” passes.
- When truly unsure → defer to teacher (clear reason).
- Do not defer constantly — but **false pass is worse than defer**.
- Student + teacher must be able to trust a pass.

### Next data needed for real acoustic Qu
~30+ labeled short Qu takes per class (correct back-ق, incorrect middle-ك), same phone + others, before replacing ASR gate.

## Stages (ayah 1)
Qu (قُ) → ul → Qul → … · store `tarteel_practice_v6`

## Stack
Railway from `main`. Hard-refresh after deploy.
