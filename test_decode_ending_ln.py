"""Regression: phone m4a must not flip an L ending into N via ffmpeg filters.

Session 20260729-220246-affdf3 — Omar heard L on playback; Whisper wrote كُلًّا;
loudnorm-on-AAC reported N; loudnorm-on-PCM reported L. Always normalize the
decoded wav, never the container.
"""
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

from analyze_xlsr import analyze_verse

FIXTURE = Path(__file__).resolve().parent / "testdata" / "20260729-220246-affdf3.m4a"


@pytest.mark.skipif(not FIXTURE.exists(), reason="affdf3 fixture missing")
def test_affdf3_m4a_ending_is_l_not_n():
    cards = analyze_verse(str(FIXTURE), verse=1, stage_id="qul")
    assert cards, "expected analysis cards"
    c = cards[0]
    ev = c.get("sound_evidence") or {}
    pl = float(ev.get("ل") or 0.0)
    pn = float(ev.get("ن") or 0.0)
    assert pl > pn, f"expected L>N on affdf3, got L={pl} N={pn} letters={c.get('sound_letters')!r}"
    assert pl >= 0.45, f"expected clear L, got {pl}"
    summary = (c.get("heard_summary_en") or "").lower()
    assert "ending l" in summary or "l ✓" in summary, summary
    assert "more like n" not in summary, summary
