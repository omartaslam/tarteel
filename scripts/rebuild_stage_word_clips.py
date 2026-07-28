#!/usr/bin/env python3
"""
Rebuild ayah-1 stage word clips from real_ikhlas1_husary_full.

Teaching clips must contain the *whole* target word (not a mid-word slice).
Windows are verified against Quran ASR (transcribe_quran).

Usage (from repo root, venv active):
  python scripts/rebuild_stage_word_clips.py
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "static/samples/real_ikhlas1_husary_full.wav"
OUT = ROOT / "static/samples"

# Seconds into SRC — chosen so ASR hears the full word clearly.
WINDOWS = {
    "qul": (0.72, 1.28),
    "qu": (0.72, 1.12),    # Qu onset for syllable rescue — Hear only Qu
    "ul": (1.05, 1.32),    # ul ending model for syllable rescue
    "huwa": (1.15, 1.95),   # was 0.5s mid-cut → garbled; must cover full هُوَ
    "allahu": (1.95, 3.60),
    "ahad": (3.40, 4.75),
}

PAD_S = 0.08
FADE_S = 0.025


def extract(y: np.ndarray, sr: int, a: float, b: float) -> np.ndarray:
    seg = y[int(a * sr) : int(b * sr)].astype(np.float32)
    peak = float(np.abs(seg).max()) or 1.0
    if peak > 0.05:
        seg = seg * min(0.92 / peak, 2.5)
    pad = np.zeros(int(PAD_S * sr), dtype=np.float32)
    out = np.concatenate([pad, seg, pad])
    n = int(FADE_S * sr)
    if len(out) > 2 * n:
        out[:n] *= np.linspace(0, 1, n, dtype=np.float32)
        out[-n:] *= np.linspace(1, 0, n, dtype=np.float32)
    return out


def main() -> None:
    y, sr = librosa.load(str(SRC), sr=16000)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (a, b) in WINDOWS.items():
        audio = extract(y, sr, a, b)
        wav = OUT / f"stage_{name}_husary.wav"
        mp3 = OUT / f"stage_{name}_husary.mp3"
        sf.write(str(wav), audio, sr)
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(wav),
                "-codec:a", "libmp3lame", "-q:a", "4",
                "-ar", "16000", "-ac", "1", str(mp3),
            ],
            capture_output=True,
            check=True,
        )
        wav.unlink(missing_ok=True)
        print(f"{name}: {a:.2f}-{b:.2f}s → {len(audio)/sr:.2f}s → {mp3.name}")


if __name__ == "__main__":
    main()
