"""Every ladder stage must own Hear only + Correct/Incorrect (stage contract)."""
from pathlib import Path
import re

INDEX = Path(__file__).resolve().parent / "static" / "index.html"
STAGES_PY = Path(__file__).resolve().parent / "stages.py"

AYAH1_IDS = [
    "qu", "ul", "qul", "hu", "wa", "huwa", "allahu", "ahad", "full",
]


def test_stage_contract_helpers_exist():
    html = INDEX.read_text(encoding="utf-8")
    assert "STAGE CONTRACT" in html
    assert "function resolveStageCompare" in html
    assert "function stageComparePair" in html
    assert "function stageStubCompare" in html
    # Old Qul-only side map must stay gone — compare lives on each stage.
    assert "const STAGE_COMPARE=" not in html


def test_ayah1_every_stage_owns_hear_and_compare():
    html = INDEX.read_text(encoding="utf-8")
    # Slice verse-1 ladder roughly: from "1:[" after STAGE_LADDER to "2:["
    m = re.search(
        r"const STAGE_LADDER=\{.*?1:\[(.*?)\],\s*2:\[",
        html,
        re.S,
    )
    assert m, "could not find ayah-1 STAGE_LADDER block"
    block = m.group(1)
    for sid in AYAH1_IDS:
        assert re.search(rf"id:\s*'{sid}'", block), f"missing stage {sid}"
        # Each stage object that declares this id must also declare hear + compare nearby.
        # Find the object starting at id:'sid' and ending at the next id:' or end.
        objs = list(re.finditer(rf"\{{\s*id:\s*'{sid}'", block))
        assert objs, f"no object for {sid}"
        start = objs[0].start()
        nxt = re.search(r"\{\s*id:\s*'", block[start + 1 :])
        end = start + 1 + nxt.start() if nxt else len(block)
        obj = block[start:end]
        assert "hear:" in obj, f"{sid} missing hear"
        assert "compare:" in obj, f"{sid} missing compare"


def test_stages_py_documents_ui_contract():
    text = STAGES_PY.read_text(encoding="utf-8")
    assert "hear" in text and "compare" in text
    assert "STAGE_LADDER" in text or "static/index.html" in text
