"""The ق vs ك benchmark, run on real audio through the real probe.

This is the test that was missing. The previous rescue read its letters from
forced alignment against the expected ayah, so it answered "ق present, ك
absent" for the kaf benchmark, English "cool", white noise and digital
silence — and the Qul stage passed all of them on live.

Anything here that regresses means the app is accepting ك as ق again.
"""
from pathlib import Path

import numpy as np
import pytest

torch = pytest.importorskip("torch")
librosa = pytest.importorskip("librosa")

import coaching as coach
from analyze_xlsr import _load, onset_probe

SAMPLES = Path(__file__).resolve().parent / "static" / "samples"

# Clips whose onset really is ق, and which the acoustic model resolves.
# real_qul_minshawi is deliberately absent: XLSR does not resolve ق on that
# 0.55s cut, but Whisper reads it as قُلْ, so the take still has ق evidence
# without the rescue. Do not "fix" that by loosening the threshold.
QAF_CLIPS = [
    "bench_correct_qaf_letter_alnatiq.mp3",
    "stage_qul_husary.mp3",
    "qul_correct_male.mp3",
    "stage_qu_husary.mp3",
    "ku_correct.mp3",
]

# Must never be reported as ق. bench_incorrect_kaf_kul_fjmustak passed Qul on
# live before this guard existed.
KAF_CLIPS = [
    "bench_incorrect_kaf_kul_fjmustak.mp3",
    "bench_incorrect_kaf_letter_alnatiq.mp3",
    "cool_incorrect_male.mp3",
    "real_cool_grendelkhan.mp3",
    "ku_incorrect.mp3",
]

# Not Qul at all — no ق evidence should be manufactured for these.
NON_QUL_CLIPS = [
    "stage_ahad_husary.mp3",
    "stage_allahu_husary.mp3",
    "stage_huwa_word.mp3",
]


@pytest.fixture(scope="module")
def probe_fn():
    proc, model, _ = _load()

    def run(wav: np.ndarray) -> dict:
        iv = proc(wav, sampling_rate=16000, return_tensors="pt").input_values
        with torch.no_grad():
            emissions = torch.log_softmax(model(iv).logits, dim=-1)
        return onset_probe(emissions, proc, len(wav) / 16000)

    return run


def _load_clip(name: str) -> np.ndarray:
    y, _ = librosa.load(str(SAMPLES / name), sr=16000)
    return y


@pytest.mark.parametrize("name", QAF_CLIPS)
def test_real_qaf_is_detected(name, probe_fn):
    v = coach.onset_qaf_verdict(probe_fn(_load_clip(name)))
    assert v["has_qaf"] is True, f"{name}: lost ق evidence ({v})"
    assert v["has_kaf"] is False, f"{name}: reported ك ({v})"


@pytest.mark.parametrize("name", KAF_CLIPS)
def test_kaf_is_never_reported_as_qaf(name, probe_fn):
    v = coach.onset_qaf_verdict(probe_fn(_load_clip(name)))
    assert v["has_qaf"] is False, f"{name}: ك accepted as ق ({v})"


@pytest.mark.parametrize("name", NON_QUL_CLIPS)
def test_other_words_are_not_qaf(name, probe_fn):
    v = coach.onset_qaf_verdict(probe_fn(_load_clip(name)))
    assert v["has_qaf"] is False, f"{name}: invented ق ({v})"


def test_silence_and_noise_are_not_qaf(probe_fn):
    rng = np.random.default_rng(0)
    cases = {
        "digital silence": np.zeros(16000, dtype=np.float32),
        "white noise": (rng.standard_normal(16000) * 0.05).astype(np.float32),
    }
    for label, wav in cases.items():
        v = coach.onset_qaf_verdict(probe_fn(wav))
        assert v["has_qaf"] is False, f"{label} reported ق ({v})"
        assert v["has_kaf"] is False, f"{label} reported ك ({v})"
