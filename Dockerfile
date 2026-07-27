FROM python:3.11-slim

# ffmpeg for audio conversion + git for any pip-from-source
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU torch first (smaller, no CUDA)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download ASR models BEFORE copying app code.
# That way routine code deploys reuse this cached layer and only push a small
# app delta — instead of re-exporting/pushing ~GBs of weights every time.
# XLSR = forced alignment / qalqalah; Whisper = "what I heard" on tilawah.
RUN python -c "from transformers import Wav2Vec2ForCTC, AutoProcessor, \
    WhisperForConditionalGeneration, WhisperProcessor; \
    m='jonatasgrosman/wav2vec2-large-xlsr-53-arabic'; \
    AutoProcessor.from_pretrained(m); Wav2Vec2ForCTC.from_pretrained(m); \
    w='basharalrfooh/whisper-small-quran'; \
    WhisperProcessor.from_pretrained(w); WhisperForConditionalGeneration.from_pretrained(w)"

# App source last — invalidate only this thin layer on code changes
COPY . .

# Never hit Hugging Face at runtime (models are baked into the image)
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1
ENV PORT=8000
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
