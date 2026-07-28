# Deploy markers

## stable-qu-detection — 2026-07-28

**Commit / build:** `e6878cde0424`  
**Git tag:** `stable-qu-detection`  
**Live health:** `{"ok":true,"build":"e6878cde0424"}`

### Why this is marked stable
Omar produced a successful **back ق (Qu)** lock on this build:

- Session `20260728-092902-94fcca`
- Display: `قُ` / `Qu`
- Action: **Locked Qu → ul**
- Middle-ك takes around it correctly **failed** (`ك→ق`)

Detection rule on this build: analyse each take — **ق passes, ك fails**. No “ك counts as pass” shortcut.

### Do not regress
Do not reintroduce `pass if ك OR ق` on the Qu drill, and do not demote full-word `ك→ق` to a non-blocking tip on the Qul stage.
