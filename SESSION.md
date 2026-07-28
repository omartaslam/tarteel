# Tarteel — session handoff

Last updated: 2026-07-28 (Qu lock gate reverted to stable ASR letters)

## Stable Qu detection baseline
- **Tag / file:** `stable-qu-detection` / `STABLE.md`
- **Commit:** `e6878cde0424` — first successful Qu lock; no ك-as-pass.
- **Rule:** analyse each take — **ق passes, ك fails**. No `pass if ك OR ق`.

## This deploy — acoustic removed from Qu pass/fail
Hybrid acoustic cluster gated Qu locks poorly on phone takes (false defer / veto on ASR ق).

**Qu lock gate is ASR letters only again** (same as stable):
1. ASR ق → **PASS** (lock Qu → ul)
2. ASR ك / ku… → **FAIL** (show Ku)
3. Unclear → **FAIL** (unclear display — never invent Ku)

`qu_acoustic.py` + corpus model remain on disk for research; they are **not** consulted for lock/fail.

## Keep (UI / integrity)
- No “No L yet” on Qu; yellow-mark Qu/قُ on ayah lines
- Ghost REGRESSION fix (`locked_stages` + practice store v7)
- Literal Whisper under drill when different from onset display
- No inventing letters/passes on Qur’an

## Retest checklist
1. Hard-refresh (tap green header).
2. Qu: middle-K / incorrect ك → fail.
3. Qu: good Qu / Husary with ASR ق → **lock → ul** (must not stuck-defer).
4. Confirm `/health` build matches this deploy.

## Stack
Railway from `main`. Practice store `tarteel_practice_v7`.
