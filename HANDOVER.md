# Tarteel — Full Project Handover

**Document owner:** Omar Tanveer Aslam (`omartanveeraslam@gmail.com`)  
**Last updated:** 2026-07-28  
**Live app:** https://tarteel-production.up.railway.app  
**Repo:** https://github.com/omartaslam/tarteel  
**Branch that deploys:** `main` (Railway)  
**Live build at handoff:** `4df95c7e97c8` (`/health` → `{"ok":true,"build":"…"}`)

If you are new: read **§0 Summary** first, then **§1 Accuracy**, then **§8 Do not break**, then start on **§6 P0**.

---

## 0. Summary (shareable with a tajweed scholar / partner)

### What this is
**Tarteel** is an English-first beginner practice aid for **Surah Al-Ikhlas (112)**, Hafs ‘an ‘Asim.  
It is **not a replacement for a teacher**. It locks one piece at a time (word → join → full ayah), with mouth cues a native English speaker can actually produce.

### Headline status (honest)
| Scope | Status | Confidence (male adults, phone) |
|------|--------|----------------------------------|
| **Ayah 1 — word Qul (قُلْ)** | Working on live after phone-ASR rescue | **~70–80% directionally** on Omar’s adult-male phone takes when QUAL cue is used; **not** a formal published accuracy study |
| **Ayah 1 — rest (huwa → full)** | Pedagogue + UI scaffold live; detection not battle-tested | **Low / unproven** |
| **Ayahs 2–4** | Ladder stubs only | **Not ready** |
| **Whole Surah 112** | Partnership goal, not current claim | **Target: ≥80% accurate, male adults, before scholar live cohort** |

**One line for outreach:**  
> We have a live English-first prototype that can lock beginner **Qul** on phone for an adult male when taught as **QUAL** (as in *quality*), including when phone speech-to-text wrongly writes ك. We are **not** yet at 80% across all four ayat of Al-Ikhlas. We want a respected UK tajweed scholar as partner for **real-world validation** once detection is tea-bone accurate across the surah.

### Breakthrough that unlocked Qul (keep forever)
**Key descriptors for English-speaking students (lead every session):**
1. ***quality*** — onset **QUAL / QUA** (hollow **qh**) for ق  
2. ***pull*** — ending **ul** (short u + clear L)

- Label “Qul” alone made English speakers say **cull/cool → ك**.  
- Formula: **QUALITY** onset + **PULL** ending → **Qul** (teach split, not one mush).  
- **Not** “ghwal” (that drifts toward **غ**).  
- Next session must open with these two anchors (`SESSION.md` START HERE).

### Phone ASR problem (why scholars should care)
Phone Whisper often **flattens ق → ك** (“Kull”) even when the learner produced back ق.  
Live fix (`4df95c7`): if XLSR letter-track **onset shows ق** (and not ك), **pass** — otherwise we lock out half the audience (phone users).

### Live milestone (celebration)
- Session `20260728-163050-014995` — **Qul locked → huwa**  
- Whisper still wrote `كُلٌّ` / `Kullu`; letter track `قل…`; rescue passed.  
- Earlier celebrate Qu lock take: `static/takes/2_correct_Qu_locked.*`  
- Stable Qu tag (historical): `stable-qu-detection` @ `e6878cd` (session `20260728-092902-94fcca`)

### Mom / female voice
Live tester (Omar’s mother). **Special case — not measured.** Do not claim accuracy for her voice yet. Next discussion: female / elder / UK accent cohort. **Never wipe her practice** on deploy or header tap.

### Partnership ask (when ready)
Invite scholar partnership for **blind / live testing** of Surah 112 once internal male-adult accuracy is **≥80% across all four ayat**, letter-faithful (especially ق/ك, و/ف, ح/ه, doubled ل, etc.) — not marketing demos.

---

## 1. Accuracy & evidence (do not inflate)

### What “accuracy” means here
A **stage pass** = app advances (or locks) when the take deserves it for that stage’s target, and **fails** clear wrong place (e.g. middle ك for ق).

### Male adult (Omar) — known evidence
| Evidence | Result |
|----------|--------|
| Male murattal Qul cuts (EveryAyah battery) | Pass when ASR/letter evidence shows ق; kaf bench fails |
| Phone Qu lock (`2_correct_Qu_locked`) | Pass Qu → ul |
| Phone Qul `20260728-140251` (`قَوْلَهُ`) | Pass Qul → huwa |
| Phone Qul fails pre-rescue (Whisper ك, letters قل) | Failed wrongly until `4df95c7` |
| Phone Qul `20260728-163050` post-rescue (Whisper ك, letters قل) | Pass Qul → huwa |

**Working claim for sharing:** adult-male **Qul-on-phone** is in a **promising ~70–80% band** under QUAL teaching + letter-track rescue — **pending formal protocol** (N takes, labeled by teacher, confusion matrix ق vs ك).

**Not claimed:** 80% on huwa / Allāhu / aḥad / joins / full ayah / whole surah / female voices.

### Path to “80% across Surah 112”
1. Formal male-adult battery per stage (correct / incorrect minimal pairs).  
2. Scholar labels ground truth.  
3. Confusion matrices per letter pair.  
4. Only then invite wider live cohort.

---

## 2. Product intent & pedagogy

- **Audience:** Native English-speaking beginners (adults first).  
- **Surah:** 112 Al-Ikhlas, 4 ayat.  
- **Riwayah:** Hafs ‘an ‘Asim.  
- **Pedagogy (ayah 1, word-first):**  
  1. Full **Qul** ×3 → pass with ق → **huwa** (also locks qu+ul).  
  2. After 3 Qul fails → syllable rescue **Qu** ×3 → **ul** → huwa.  
  3. After 3 Qu fails → ask a teacher (defer).  
- **Stage contract (replicate everywhere):** every stage owns `hear` + `compare` (Correct vs Incorrect for **this** step). Ayah 1 is the filled prototype.

### English mouth cues (hard rule)
| Target | Cue |
|--------|-----|
| ق / Qul onset | **QUAL / QUA** like *quality* |
| ul | end of *pull* / *full* |
| huwa | **HOO-wa** |
| Allāhu | **Al-LAA-hu** (hold ll) |
| aḥad | **a-ḤAD** (fog-mirror Ḥ, not soft “ahead”) |

---

## 3. Live deployment

| Item | Value |
|------|--------|
| URL | https://tarteel-production.up.railway.app |
| Health | `GET /health` → `{ok, build}` |
| Deploy source | GitHub `main` → Railway |
| Practice store (client) | `localStorage` key `tarteel_practice_v7` |
| Clear history | **Only** explicit “Clear practice history” button |
| Header tap | Hard-refresh; **must keep progress** |

**Operator habit:** Omar / mom test **only on live**. Feature branches do not count until merged to `main` and `/health` shows the new build. Hard-refresh after deploy.

---

## 4. Codebase map

| Path | Role |
|------|------|
| `server.py` | FastAPI: analyze jobs, sessions, husary, static |
| `analyze_xlsr.py` | Pipeline: decode → Whisper ASR → XLSR align → feedback |
| `transcribe_quran.py` | Quran ASR + romanize (ق → q → Qul/Qu); mouth cue stays QUAL |
| `coaching.py` | Tips, compare HTML, drills, `align_onset_qaf`, QUAL copy |
| `elements.py` | Stage pass/fail, Qul ق gate + phone rescue, cards |
| `stages.py` | Ladder definition (ids/hints; UI hear/compare in HTML) |
| `static/index.html` | Entire beginner UI + `STAGE_LADDER` contract |
| `static/samples/` | Husary stage clips + ق/ك bench |
| `static/takes/` | Omar labeled phone takes (celebrate Qu lock) |
| `STABLE.md` | Hard rules / stable markers |
| `SESSION.md` | Short live-tester handoff |
| `test_qul_drills.py` | ق/ك + phone rescue tests |
| `test_stage_contract.py` | Every ayah-1 stage has hear+compare |

### Detection rules (current live)
1. Qu drill: Whisper **ق** pass; Whisper **ك** fail; **qh/QUAL** phonetics can pass if no Arabic ك.  
2. **Phone rescue:** XLSR onset **ق** (not ك) → pass even if Whisper wrote ك.  
3. Qul word: same spirit — require ق evidence; rescue via align onset; never skip to huwa on shape-near garbage without ق.  
4. Acoustic Qu cluster: **not** in live lock path (reverted earlier).

---

## 5. Working practices

- **Live is source of truth** for Omar’s testing.  
- Do not wipe mom’s practice.  
- Prefer **evidence** (session ids, `/sessions`, re-analyze audio) over tip/regex whack-a-mole.  
- English cues over scholarly jargon when teaching beginners.  
- UI: no schoolboy layout regressions; Hear only + Compare always for **current** stage.  
- After detection/UX changes: merge to `main`, wait for `/health` build bump, hard-refresh, then test.  
- Tests: `pytest test_qul_drills.py test_stage_contract.py test_stage_clips.py` (and related).

### Useful live APIs
- `GET /health`  
- `GET /sessions` — recent analyses  
- `GET /sessions/{id}/audio` — raw take  
- `GET /sessions/{id}/play` — playback page  

---

## 6. P0 — open decisions & next work

### P0 UX decisions (Omar locked 2026-07-28)
1. **First visit:** whole-surah Listen once → then current task (Qul). Resume saved stage/ayah.  
2. **Compare:** under Hear only.  
3. **Qul fails:** ×3 then Qu rescue.  
4. **Header tap:** clear practice, no confirm + refresh.  
5. **Promo:** ayah 1 first; full 112 later.  
6. **Ayah 2:** word isolate → join (English cues); ×3 rescue optional later.

### P0 product / detection
- [ ] Formal male-adult accuracy protocol for Qul (N≥30).  
- [ ] Huwa / Allāhu / aḥad batteries; ayah 2 aṣ-ṣamad.  
- [ ] Mobile Chrome UX pass on live.  
- [ ] Incorrect clips where still TBD.  
- [ ] Ayat 3–4 stage contract fill.  
- [ ] Mom / female voice study (separate).  
- [ ] Scholar partnership at ≥80% surah-level male-adult.

### P1
- True audio ق-vs-ك detector beyond Whisper+XLSR onset (research).  
- Richer join-stage Hear clips (not only full ayah fallback).

---

## 7. Milestone log (2026-07-28)

| When (UTC) | What |
|------------|------|
| ~09:29 | Qu lock celebrate — `stable-qu-detection` / take `2_correct_Qu_locked` |
| ~12:13 | Word-first Qul pedagogy on main |
| ~12:31 | Stage-clear UX on main (`c9e161a`) |
| ~14:02 | Qul pass `Qawlahu` on live (same build) |
| ~16:07 | Corrected QUAL takes failed — Whisper ك, letters قل |
| ~16:20 | Phone rescue merged to `main` |
| ~16:26 | Live health `4df95c7` |
| ~16:30 | Qul pass again `Kullu`+letters قل → **huwa** (`20260728-163050`) |

---

## 8. Do not break

1. **QUAL** cue for ق — never teach cull/cool as the model.  
2. **ك must not pass** as ق (no “ك OR ق” cheat).  
3. **Phone rescue:** Whisper ك + align onset ق → pass.  
4. **Mom’s practice store** — no wipe on deploy/header.  
5. **Stage contract:** Hear + Compare for current step; ayah 1 is the prototype.  
6. Deploy only counts when **`/health` build** matches `main`.

---

## 9. How a new engineer gets running

```bash
git clone https://github.com/omartaslam/tarteel
cd tarteel
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 127.0.0.1 --port 8000
# open http://127.0.0.1:8000
pytest test_qul_drills.py test_stage_contract.py -q
curl -s https://tarteel-production.up.railway.app/health
```

Read: this file → `STABLE.md` → `SESSION.md` → `static/index.html` (`STAGE CONTRACT`) → `elements.py` / `coaching.py`.

---

## 10. Scholar one-pager (copy block)

**Tarteel — Surah Al-Ikhlas practice prototype (Hafs)**  
English-first, phone-friendly, stage ladder (isolate → lock → join).  

**Now:** Reliable direction on **ayah 1 Qul** for an adult male on phone, using **QUAL** (*quality*) teaching and a dual check (speech text + letter alignment) so ق is not failed when the phone text wrongly writes ك.  

**Not yet:** ≥80% tea-bone accuracy across all four ayat; female/elder voices; replacement for a teacher.  

**Ask:** Partner with a UK tajweed scholar to design live validation and only scale testing when whole-surah male-adult accuracy reaches **≥80%**.  

**Live:** https://tarteel-production.up.railway.app  
**Contact:** Omar Tanveer Aslam — omartanveeraslam@gmail.com  

---

*End of handover. Update this file whenever live build, accuracy claims, or P0 decisions change.*
