"""Real-audio benchmark for the two sounds added after ق/ك.

Same design as test_qaf_kaf_benchmark: labelled clips of native adult male
speakers, run through the real acoustic read, so a future change that quietly
stops hearing a letter fails here instead of on a learner's phone.

Strong throat H, "haa" (ح) — measured 1.000 in every ح word and 0.000 in every
soft-H word across 12 clips from 3 male speakers, so it blocks the aḥad stage.

Heavy S, "saad" (ص) — detected in 7 of 9 native male words. Both misses were
word-final (حمص, and مصر for one speaker). In the doubled syllable-initial
position that aṣ-ṣamad needs it scored 6 of 6, which is why it blocks there.
Do not extend this gate to word-final ص without gathering new evidence.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
librosa = pytest.importorskip("librosa")

from analyze_xlsr import _load, free_read

SAMPLES = Path(__file__).resolve().parent / "static" / "samples"

# Same speaker on both sides of each pair — a within-speaker contrast, because
# comparing formants across different vocal tracts is far noisier.
HAS_LETTER = [
    ("ح", "bench_correct_haa_ahad_fjmustak.mp3"),
    ("ح", "stage_ahad_husary.mp3"),
    ("ص", "bench_correct_saad_sadiq_fjmustak.mp3"),
    ("ص", "stage_samad_husary.mp3"),
]
LACKS_LETTER = [
    ("ح", "bench_incorrect_ha_hadha_fjmustak.mp3"),
    ("ح", "stage_huwa_word.mp3"),
    ("ص", "bench_incorrect_seen_suriya_fjmustak.mp3"),
    ("ص", "bench_correct_haa_ahad_fjmustak.mp3"),
]

MIN_EVIDENCE = 0.45


def _as_the_app_hears_it(path: Path) -> np.ndarray:
    """Apply the same gain/compression/loudness chain as analyze_xlsr.

    Without it this measures something the app never sees: the Husary aṣ-ṣamad
    clip is quiet enough that its heavy S reads below threshold raw and at 1.0
    once levelled.
    """
    out = Path(tempfile.gettempdir()) / f"bench_{path.stem}.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(path), "-af",
         "volume=14dB,acompressor=threshold=-24dB:ratio=4:makeup=6,"
         "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-ar", "16000", "-ac", "1", str(out)],
        capture_output=True, check=True,
    )
    y, _ = librosa.load(str(out), sr=16000)
    return y


@pytest.fixture(scope="module")
def evidence():
    proc, model, _ = _load()

    def run(name: str) -> dict:
        y = _as_the_app_hears_it(SAMPLES / name)
        iv = proc(y, sampling_rate=16000, return_tensors="pt").input_values
        with torch.no_grad():
            em = torch.log_softmax(model(iv).logits, dim=-1)
        return free_read(em, proc)["evidence"]

    return run


@pytest.mark.parametrize("letter,name", HAS_LETTER)
def test_letter_is_heard_where_it_belongs(letter, name, evidence):
    got = float(evidence(name).get(letter) or 0.0)
    assert got >= MIN_EVIDENCE, f"{name}: lost {letter} ({got})"


@pytest.mark.parametrize("letter,name", LACKS_LETTER)
def test_letter_is_not_invented_where_it_is_absent(letter, name, evidence):
    got = float(evidence(name).get(letter) or 0.0)
    assert got < MIN_EVIDENCE, f"{name}: invented {letter} ({got})"


def test_silence_and_noise_have_no_letters(evidence):
    """Guard against the failure mode that made the old ق/ك gate vacuous."""
    proc, model, _ = _load()
    rng = np.random.default_rng(0)
    for label, wav in {
        "digital silence": np.zeros(16000, dtype=np.float32),
        "white noise": (rng.standard_normal(16000) * 0.05).astype(np.float32),
    }.items():
        iv = proc(wav, sampling_rate=16000, return_tensors="pt").input_values
        with torch.no_grad():
            em = torch.log_softmax(model(iv).logits, dim=-1)
        ev = free_read(em, proc)["evidence"]
        for letter in ("ح", "ص"):
            assert float(ev.get(letter) or 0.0) < MIN_EVIDENCE, f"{label} -> {letter}"
