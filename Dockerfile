FROM python:3.11-slim

# ffmpeg for audio conversion + git for any pip-from-source
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU torch first (smaller, no CUDA)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# pre-download the XLSR model at BUILD time so cold starts are fast
# and the model is baked into the image
RUN python -c "from transformers import Wav2Vec2ForCTC, AutoProcessor; \
    m='jonatasgrosman/wav2vec2-large-xlsr-53-arabic'; \
    AutoProcessor.from_pretrained(m); Wav2Vec2ForCTC.from_pretrained(m)"

ENV PORT=8000
CMD ["sh","-c","uvicorn server:app --host 0.0.0.0 --port ${PORT}"]
