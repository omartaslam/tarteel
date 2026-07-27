# Railway deploy steps (run on Kali)

## 1. Make sure the trained classifier is in models/
The XLSR classifier pickle MUST be committed - it's your trained model, not downloadable.
    ls ~/tarteel-app/models/qalqalah_clf_xlsr.pkl

## 2. Init git + commit (fresh repo, separate from Fred)
    cd ~/tarteel-app
    git init
    git add Dockerfile railway.json requirements.txt .dockerignore \
            server.py analyze_xlsr.py explanations.py \
            static/ models/qalqalah_clf_xlsr.pkl README.md
    git commit -m "Tarteel demo: XLSR aligner + qalqalah classifier, dockerized"

## 3. Push to a NEW GitHub repo
    # create repo 'tarteel' on github first, then:
    git remote add origin https://github.com/omartaslam/tarteel.git
    git branch -M main
    git push -u origin main

## 4. Railway
    - New Project -> Deploy from GitHub repo -> select 'tarteel'
    - Railway auto-detects the Dockerfile
    - Set no env vars needed (PORT is auto)
    - IMPORTANT: pick a plan with >= 4GB RAM (torch + XLSR model ~2-3GB)
    - Wait for build (the model bakes in at build time - build takes ~10-15 min)

## 5. Domain
    - Railway gives a *.up.railway.app URL automatically - that's your test URL
    - Later: point tarteel.co.uk at it via Cloudflare CNAME

## Notes
    - First build is slow (downloads XLSR + Whisper Quran ASR into image). Later deploys cache it.
    - If build OOMs, the model download step needs a bigger build instance.
    - Models load once at startup (warm() in server.py), so requests are fast.
    - "What the app heard" uses whisper-small-quran (tilawah ASR). XLSR is kept for
      forced-alignment / qalqalah only — its free CTC decode is unreliable on Quranic audio.
    - Prefer a plan with >= 4GB RAM (both models resident).
