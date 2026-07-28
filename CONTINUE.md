# CONTINUE HERE — next agent (P0)

**Owner:** Omar (`omartanveeraslam@gmail.com`)  
**Live:** https://tarteel-production.up.railway.app  
**Deploy:** push/`main` → Railway. Feature branches do **not** count.  
**Live build at this handoff:** `2aa0cd0c406d` (`GET /health`)

Omar is angry for good reason: agents shipped broken Hear-only **huwa** and asked him to test. **Do not ask Omar to test until you have verified on live yourself** (play the clip; confirm `/health` build).

---

## P0 — RIGHT NOW (block everything else)

### Hear-only **huwa** is STILL WRONG on live
Omar (2026-07-28 ~20:13): *“the huwa is even worse”* — he will **not** test the Allāhu bug until this is fixed.

| Item | Value |
|------|--------|
| URL | `/samples/stage_huwa_husary.mp3?v=4` |
| Source | cut from `static/samples/real_ikhlas1_husary_full.wav` |
| Rebuild script | `scripts/rebuild_stage_word_clips.py` |
| UI refs | `static/index.html` stage `huwa` `hear` + `compare` (bump `?v=` on every replace) |

**What went wrong (do not repeat):**
1. Window **1.22–1.95** (`?v=3`) started in **Qul leftover** energy — not a clear هو start.
2. Window **1.45–1.88** (`?v=4`, live now) was an energy/XLSR guess with silence pads — Omar says **worse**. Likely truncated / wrong slice; **0.43s of speech is too aggressive** if it clips ه or و.
3. Agent “verified” with RMS bookends + md5 vs live — **never actually listened**. Energy ≠ audible هو.

**XLSR letter times on full Husary ayah 1** (forced align, for reference only — letters are short hits, not full word duration):
```
قل  0.801–1.061
|   1.161–1.181
ه   1.481–1.501
و   1.621–1.641
|   1.782–1.822
ا   2.142–…   ← Allāhu starts
```

**Required bar for “fixed”:**
- Clear audible **start** of **HOO-wa** (ه), not mid-Qul / not silence then a stub.
- Clear audible **end** of **wa** (و), not chopped, not bleeding into Allāhu.
- Play it yourself (browser / `ffplay` / computerUse) on the **live** URL after deploy.
- Then bump cache `?v=5` (or higher), merge **main**, wait `/health`, hard-refresh, play live again.
- Only then tell Omar.

**Ideas if cut from full ayah keeps failing:**
- Wider window around 1.40–2.05 but fade/trim Allāhu onset carefully.
- Separate clean Husary **هو** asset (EveryAyah / single-word) if ayah cut cannot sound clean.
- Compare against qul clip quality as the bar.

---

## P1 — after huwa is truly fixed (Omar blocked this)

### False `wrong_stage:allahu:qul` (code shipped on `2aa0cd0`, **untested by Omar**)
**Root cause (real, not stale audio):** full-ayah left-align ate **الله** as near-**قل** via letters **ال**, then Allāhu = miss → `detect_repeated_earlier_word` → “sounded like Qul”.

**Fix already on main** (`coaching.py`):
- `_align_stage` / `_filter_expected` — stage-scoped align
- Single-word stages = whole-take vs that word (no prefix cherry-pick)
- Earlier-word detect requires **ok**, not near
- Regression: `test_allahu_is_not_false_wrong_stage_qul` in `test_qul_drills.py`

**Omar has not retested** — he stopped when huwa got worse. After huwa is good, ask him to hard-refresh and retry Allāhu only.

---

## Hard operator rules (Omar)

1. **Live only** — `/health` build must bump before claiming fixed.
2. **Never ask Omar to test broken audio** — listen first.
3. **Hard-refresh** after sample/`?v=` changes (phones cache aggressively).
4. Header tap clears practice **with no confirm** (Omar chose 4C). Mom: careful.
5. ق pass / ك fail + phone rescue (Whisper ك + XLSR onset ق → pass). Never `ك OR ق`.

---

## English mouth cues (START HERE every session)

1. **QUALITY** — ق = QUAL / QUA like *quality*
2. **PULL** — ul = end of *pull* / *full*
3. huwa = **HOO-wa**
4. Allāhu = **Al-LAA-hu**
5. aḥad = **a-ḤAD**

Labels stay **Qul/Qu** (not Qhul). Cue stays QUALITY+PULL.

---

## Journey decisions (locked 2026-07-28)

1. First visit: Listen = **whole surah** once → then current Say. Later: Listen = this ayah; Continue banner.
2. Compare under Hear only.
3. Qul ×3 then Qu rescue.
4. Header clears practice no confirm + hard refresh.
5. Promo: ayah 1 first; full 112 later.
6. Ayah 2: Allāhu → aṣ-ṣamad → join; English cues.

Practice store: `tarteel_practice_v7`. Resume: `tarteel_last_verse_v1`.

---

## Key files

| Path | Why |
|------|-----|
| `CONTINUE.md` | **This file — start here** |
| `HANDOVER.md` | Full project / scholar-facing |
| `SESSION.md` | Short session log |
| `STABLE.md` | Hard rules / freeze |
| `scripts/rebuild_stage_word_clips.py` | Ayah-1 word clip windows |
| `static/samples/real_ikhlas1_husary_full.wav` | Source for cuts |
| `static/samples/stage_huwa_husary.mp3` | Broken live Hear-only |
| `static/index.html` | `STAGE_LADDER`, `?v=` cache |
| `coaching.py` | Align / wrong_stage / compare |
| `elements.py` | `build_feedback`, wrong_stage insert |
| `stages.py` | Stage ladder |
| `test_qul_drills.py` | Allāhu regression + Qul tests |
| `test_stage_clips.py` | Min clip durations |

---

## Do not

- Ship huwa without listening.
- Claim live before `/health` shows new SHA.
- Leave fixes on feature branches and ask Omar to test live.
- Inflate accuracy claims (Qul phone ~70–80% directional only; rest unproven).
- Wipe mom’s practice casually.

---

## Done when

1. Omar agrees Hear-only huwa has clear start + end (HOO-wa).  
2. Omar confirms Allāhu no longer says Qul/Kul.  
3. Both verified on live `/health` build you document here.
