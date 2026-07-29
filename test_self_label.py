"""The learner's own verdict is the only ground truth we have.

Without it there is no accuracy number, only a demo — so the capture path is
worth testing even though it is a handful of lines.
"""
import json
import os
import shutil
import tempfile

import pytest

pytest.importorskip("fastapi.testclient")
from fastapi.testclient import TestClient

import server
import storage


@pytest.fixture()
def client(monkeypatch):
    tmp = tempfile.mkdtemp()
    monkeypatch.setattr(storage, "STORE", tmp)
    yield TestClient(server.app), tmp
    shutil.rmtree(tmp, ignore_errors=True)


def _seed(store, sid, *, stage="qul", passed=True):
    d = os.path.join(store, sid)
    os.makedirs(d, exist_ok=True)
    meta = {
        "session": sid,
        "verse": 1,
        "stage_id": stage,
        "when": "2026-07-29 12:00:00",
        "results": [{
            "stage_passed": passed,
            "sound_letters": "قول",
            "heard_arabic": "قَوْلٌ",
            "key": "stage:qul:clear",
            "onset_probe": {"p_qaf": 0.9, "p_kaf": 0.0},
        }],
    }
    json.dump(meta, open(os.path.join(d, "data.json"), "w", encoding="utf-8"))
    return meta


def test_label_is_stored_against_the_take(client):
    c, store = client
    _seed(store, "s1")
    r = c.post("/label", data={"session": "s1", "label": "correct", "stage_id": "qul"})
    assert r.status_code == 200 and r.json()["self_label"] == "correct"
    saved = json.load(open(os.path.join(store, "s1", "data.json"), encoding="utf-8"))
    assert saved["self_label"] == "correct"
    assert saved["self_label_stage"] == "qul"
    assert saved["self_label_at"]


def test_only_the_three_answers_are_accepted(client):
    c, store = client
    _seed(store, "s1")
    for good in ("correct", "think_correct", "think_wrong", "wrong", "unsure"):
        assert c.post("/label", data={"session": "s1", "label": good}).status_code == 200
    # Rejected either by our check (400) or by form validation (422 for empty).
    for bad in ("yes", "", "pass", "true"):
        assert c.post("/label", data={"session": "s1", "label": bad}).status_code >= 400


def test_unknown_session_is_rejected(client):
    c, _ = client
    assert c.post("/label", data={"session": "nope", "label": "correct"}).status_code == 404


def test_labels_endpoint_scores_agreement(client):
    c, store = client
    # app passed + learner says correct -> agree
    _seed(store, "a1", passed=True)
    c.post("/label", data={"session": "a1", "label": "correct"})
    # app passed + learner says wrong -> disagree (a false pass)
    _seed(store, "a2", passed=True)
    c.post("/label", data={"session": "a2", "label": "wrong"})
    # app failed + learner says correct -> disagree (a false fail)
    _seed(store, "a3", passed=False)
    c.post("/label", data={"session": "a3", "label": "correct"})
    # "can't tell" must not be counted as ground truth either way
    _seed(store, "a4", passed=False)
    c.post("/label", data={"session": "a4", "label": "unsure"})
    # unlabelled takes are excluded entirely
    _seed(store, "a5", passed=True)

    body = c.get("/labels").json()
    assert body["labelled"] == 4
    assert body["scored"] == 3
    assert body["agreement"] == pytest.approx(33.3, abs=0.1)
    by = {t["session"]: t for t in body["takes"]}
    assert by["a1"]["agree"] is True
    assert by["a2"]["agree"] is False
    assert by["a3"]["agree"] is False
    assert by["a4"]["agree"] is None
    assert "a5" not in by
