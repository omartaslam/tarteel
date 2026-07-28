"""Stage word clips must be long enough to teach the whole word (not mid-cuts)."""
from pathlib import Path
import subprocess

SAMPLES = Path(__file__).resolve().parent / "static" / "samples"

# Minimum durations after rebuild (seconds). Old huwa was 0.5s and unusable.
MIN_DUR = {
    "stage_qul_husary.mp3": 0.65,
    "stage_qu_husary.mp3": 0.45,
    "stage_ul_husary.mp3": 0.35,
    "stage_huwa_husary.mp3": 0.75,  # clean هو only (~0.43s) + silence bookends
    "stage_allahu_husary.mp3": 1.4,
    "stage_ahad_husary.mp3": 1.2,
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


def test_stage_word_clips_long_enough_to_teach():
    for name, min_s in MIN_DUR.items():
        p = SAMPLES / name
        assert p.exists(), f"missing {name}"
        dur = _duration(p)
        assert dur >= min_s, f"{name} too short for teaching ({dur:.3f}s < {min_s}s)"
