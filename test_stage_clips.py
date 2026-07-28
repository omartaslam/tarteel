"""Stage word clips must be teachable: whole word, audible, clean bookends.

Real live failures guarded here:
  * ?v=3 huwa started inside Qul leftover audio.
  * ?v=4 huwa cut the ه onset (0.43s stub) and shipped ~7 dB under the other
    clips, so it was barely audible on a phone.
Huwa now comes from an isolated word recording rather than an ayah slice,
because Husary recites "Qul huwa" joined.
"""
import re
from pathlib import Path
import subprocess

import librosa
import numpy as np
import pytest

SAMPLES = Path(__file__).resolve().parent / "static" / "samples"

# Minimum durations after rebuild (seconds). Old huwa was 0.5s and unusable.
MIN_DUR = {
    "stage_qul_husary.mp3": 0.65,
    "stage_qu_husary.mp3": 0.45,
    "stage_ul_husary.mp3": 0.35,
    "stage_huwa_word.mp3": 0.80,
    "stage_allahu_husary.mp3": 1.4,
    "stage_ahad_husary.mp3": 1.2,
    "stage_huwa_incorrect_no_waw.mp3": 0.40,
    "stage_allahu_incorrect_single_l.mp3": 0.40,
    "stage_ahad_incorrect_soft_h.mp3": 0.50,
}

# A teaching clip nobody can hear is a broken clip.
MIN_SPEECH_RMS = 0.11
MIN_PEAK = 0.35

# Speech (silence stripped) must cover the whole word, not a clipped stub.
MIN_SPEECH_DUR = {
    "stage_huwa_word.mp3": 0.55,
}


def _duration(path: Path) -> float:
    out = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    ).strip()
    return float(out)


def _speech_region(y: np.ndarray) -> np.ndarray:
    thr = 0.03 * float(np.abs(y).max() or 1.0)
    nz = np.where(np.abs(y) > thr)[0]
    return y[nz[0] : nz[-1] + 1] if len(nz) else y


def test_stage_word_clips_long_enough_to_teach():
    for name, min_s in MIN_DUR.items():
        p = SAMPLES / name
        assert p.exists(), f"missing {name}"
        dur = _duration(p)
        assert dur >= min_s, f"{name} too short for teaching ({dur:.3f}s < {min_s}s)"


@pytest.mark.parametrize("name", sorted(MIN_DUR))
def test_stage_word_clips_are_audible(name):
    y, sr = librosa.load(str(SAMPLES / name), sr=16000)
    peak = float(np.abs(y).max())
    rms = float(np.sqrt(np.mean(_speech_region(y) ** 2)))
    assert peak >= MIN_PEAK, f"{name} peak too low ({peak:.3f})"
    assert rms >= MIN_SPEECH_RMS, f"{name} too quiet to hear ({rms:.4f})"


@pytest.mark.parametrize("name", sorted(MIN_SPEECH_DUR))
def test_stage_word_clips_are_not_clipped_stubs(name):
    y, sr = librosa.load(str(SAMPLES / name), sr=16000)
    speech = _speech_region(y)
    dur = len(speech) / sr
    assert dur >= MIN_SPEECH_DUR[name], (
        f"{name} speech only {dur:.3f}s — word onset likely cut"
    )


def test_every_ayah1_stage_shows_a_correct_and_an_incorrect_example():
    """Compare is a teaching aid — an empty Incorrect row teaches nothing."""
    html = (Path(__file__).resolve().parent / "static" / "index.html").read_text()
    ladder = re.search(r"const STAGE_LADDER\s*=\s*\{(.*?)\n\s*\};", html, re.S).group(1)
    v1 = re.search(r"\n\s*1:\s*\[(.*?)\n\s*\],\n\s*2:\s*\[", ladder, re.S).group(1)
    empty = []
    for chunk in re.split(r"\n\s*\{\s*\n?\s*(?=id:')", v1):
        sid = re.search(r"id:'([a-z_]+)'", chunk)
        pair = re.search(r"stageComparePair\((.*?)\n\s*\),", chunk, re.S)
        if not sid or not pair:
            continue
        args = re.findall(r"'((?:[^'\\]|\\.)*)'", pair.group(1))
        if len(args) >= 8 and not args[5].strip():
            empty.append(sid.group(1))
    assert not empty, f"ayah-1 stages with no Incorrect example: {empty}"


def test_every_clip_referenced_by_the_ui_exists():
    """A renamed clip must never reach live as a 404 Hear only button."""
    html = (Path(__file__).resolve().parent / "static" / "index.html").read_text()
    missing = [
        ref
        for ref in sorted(set(re.findall(r"/samples/([A-Za-z0-9_.-]+\.mp3)", html)))
        if not (SAMPLES / ref).exists()
    ]
    assert not missing, f"index.html references missing clips: {missing}"


@pytest.mark.parametrize("name", sorted(MIN_DUR))
def test_stage_word_clips_have_clean_start_and_end(name):
    y, sr = librosa.load(str(SAMPLES / name), sr=16000)
    edge = int(0.03 * sr)
    rms = float(np.sqrt(np.mean(_speech_region(y) ** 2)))
    lead = float(np.sqrt(np.mean(y[:edge] ** 2)))
    trail = float(np.sqrt(np.mean(y[-edge:] ** 2)))
    assert lead < rms * 0.5, f"{name} starts mid-sound (lead {lead:.4f})"
    assert trail < rms * 0.5, f"{name} ends mid-sound (trail {trail:.4f})"
