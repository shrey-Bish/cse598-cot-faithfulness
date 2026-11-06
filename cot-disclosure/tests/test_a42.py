"""A42 (Nov 6; archive/sessions/2026-11-06/2026-11-06_1122_A_a42-prereg.md): A40 + the note on E2. The system a40_note
(A40's merged model with prompt_only's note in every round), served by A39's lean design like a40; every other
system's prompts byte for byte as before; eval_job and submit.sh take it; finetune/a42.py's readings on planted runs;
a39.py and a40.py never read its runs. No GPU, no network."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))

pytest.importorskip("transformers")

from finetune import a39, a40, a42  # noqa: E402
from finetune import eval as ev  # noqa: E402
from finetune.gpu import eval_job as ej  # noqa: E402
from test_a39 import ALL, HALF, NONE, plant  # noqa: E402
from test_trackA_gpu_kit import fake_sbatch, sbatch_args, submit  # noqa: E402

# every A39-design prompt on E2, hashed before A42's code (Nov 6, 11:3x): A42 changes none of them
BEFORE = {"base": "6043dd75fc057568208874d2fc535935ca59cad92cf613d812bc6d0a432b4e7c",
          "prompt_only": "e9466c12da8291282ff9d0ccabd78aef3ae9a82e471467e8065ae9f57816bbe5",
          "lora": "6043dd75fc057568208874d2fc535935ca59cad92cf613d812bc6d0a432b4e7c",
          "lora_note": "e9466c12da8291282ff9d0ccabd78aef3ae9a82e471467e8065ae9f57816bbe5",
          "wrap": "8cf51f7b1f63d08c4523092030a9c6edcc9936fc67814221cc1f7a2b94bec5c9",
          "wrap_note": "db420c82274fa33b2ebc823a1f16bedb2b0e929c4e77a6f7c44e5b713bc4e0d2",
          "lora_wrap": "8cf51f7b1f63d08c4523092030a9c6edcc9936fc67814221cc1f7a2b94bec5c9",
          "a40": "6043dd75fc057568208874d2fc535935ca59cad92cf613d812bc6d0a432b4e7c"}


def prompts_hash(system):
    h, render = hashlib.sha256(), ev.renderer(system)
    for j in ev.jobs(qset="e2", design="a39", system=system):
        h.update(render(j["messages"], j["tools"]).encode())
    return h.hexdigest()


def test_every_existing_system_renders_byte_for_byte_as_before():
    assert {s: prompts_hash(s) for s in BEFORE} == BEFORE


def test_a40_note_is_a40_with_prompt_only_s_note_in_every_round():
    js = ev.jobs(qset="e2", design="a39", system="a40_note")
    assert [ev.job_id("a40_note", j) for j in js] != [ev.job_id("a40", j) for j in js]             # its own run ids
    assert [(j["item_id"], j["wording"], j["hint_letter"], j["repeat"]) for j in js] == \
           [(j["item_id"], j["wording"], j["hint_letter"], j["repeat"]) for j in ev.jobs(qset="e2", design="a39", system="a40")]
    assert prompts_hash("a40_note") == BEFORE["prompt_only"]       # the note as prompt_only's, every round
    one = js[0]
    assert ev.NOTE in ev.renderer("a40_note")(one["messages"], one["tools"])
    assert ev.NOTE not in ev.renderer("a40")(one["messages"], one["tools"])


def test_a40_note_runs_on_a40_s_merged_model(tmp_path, monkeypatch):
    train, models, base = tmp_path / "train", tmp_path / "models", tmp_path / "base"
    (train / "a40" / "final").mkdir(parents=True)
    (train / "a40" / "final" / "chosen.json").write_text("{}")
    monkeypatch.setattr(ej, "merge_lora", lambda b, adapter, out: out)
    assert ej.MODEL_OF["a40_note"] == "a40"
    assert ej.prepare("a40_note", base, train, models) == ej.prepare("a40", base, train, models) == (models / "a40_merged", None)


def test_submit_takes_a40_note_for_a39_jobs_only(tmp_path):
    env, log = fake_sbatch(tmp_path)
    r = submit(env, "a39_1gpu", "--estimate", "1.5", "--", "a40_note", "e2", "1/16")
    assert r.returncode == 0 and sbatch_args(log)[-3:] == ["a40_note", "e2", "1/16"], r.stderr
    r = submit(env, "train", "--estimate", "1.5", "--", "a40_note")
    assert r.returncode == 1 and "needs one of" in r.stderr


# ---------------------------------------------------------------- the readings, on planted runs
Q = 8


def four(out, follows=NONE, accepts=ALL, right=lambda i: True, mention=True, a40_follows=HALF):
    Path(out).mkdir(parents=True, exist_ok=True)
    plant(out, "base", follows=ALL)
    plant(out, "prompt_only", follows=HALF)
    plant(out, "a40", follows=a40_follows)
    plant(out, "a40_note", follows=follows, accepts=accepts, right=right, mention=mention)


def test_a42_beats_the_instruction_and_adds_to_both(tmp_path):
    four(tmp_path)
    res = a42.report(tmp_path, "e2")
    p = res["primary"]
    assert p["reading"] == a40.BEATS.format(ref="the instruction") and p["accuracy_label"] is None
    assert res["r3"]["reading"] == "adds to both" and res["r3"]["against"] == ["a40", "prompt_only"]
    assert res["r1"]["verdict"] == "passes" and res["questions"] == Q
    assert set(res["vs_a40"]["by_channel"]) == set(a39.CHANNELS)
    assert json.loads((tmp_path / "a42_e2.json").read_text())["primary"]["reading"] == p["reading"]
    assert "beats the instruction" in a42.text(res) and "adds to both" in a42.text(res)


def test_the_other_four_readings_and_r3_s_other_categories(tmp_path):
    four(tmp_path / "c", accepts=lambda i, ch: i % 2 == 0)
    res = a42.report(tmp_path / "c", "e2")
    assert res["primary"]["reading"] == a40.ACCEPTANCE_COST and res["r3"]["reading"] == "adds, costs acceptance"
    four(tmp_path / "m", follows=HALF)
    res = a42.report(tmp_path / "m", "e2")
    assert res["primary"]["reading"] == a40.MATCHES.format(ref="the instruction")
    assert res["r3"]["reading"] == "no better than the better one alone"
    four(tmp_path / "w", follows=ALL)
    res = a42.report(tmp_path / "w", "e2")
    assert res["primary"]["reading"] == a40.WORSE.format(ref="the instruction") and res["r3"]["reading"] == "worse than one alone"
    h = tmp_path / "h"
    h.mkdir()
    plant(h, "base", follows=ALL)
    plant(h, "prompt_only", follows=ALL)
    plant(h, "a40", follows=ALL)
    plant(h, "a40_note", follows=lambda i, ch: i < 4, mention=False)
    assert a42.report(h, "e2")["primary"]["reading"] == a40.HIDES_MORE


def test_an_accuracy_cost_is_a_label_and_r3_s_accuracy_category(tmp_path):
    four(tmp_path, right=lambda i: i % 2 == 0)
    res = a42.report(tmp_path, "e2")
    assert res["primary"]["accuracy_label"] == a40.ACCURACY_COST and res["r3"]["reading"] == "adds, costs accuracy"


def test_partial_and_the_two_not_run_labels(tmp_path):
    four(tmp_path)
    p = tmp_path / f"{ev.stem('a40_note', (1, 1), 'e2', 'a39')}_runs.jsonl"
    first = ev.questions("e2")[0]["item_id"]
    p.write_text("".join(x for x in p.read_text().splitlines(True) if json.loads(x)["item_id"] != first))
    assert a42.report(tmp_path, "e2")["label"].startswith("INCOMPLETE")
    res = a42.report(tmp_path, "e2", partial=True)
    assert res["label"] == "partial: 7 of 120 questions" and res["questions"] == 7
    empty = tmp_path / "empty"
    empty.mkdir()
    plant(empty, "base", follows=ALL)
    assert a42.report(empty, "e2", partial=True)["label"] == "not run: no GPU time by Nov 15"
    assert a42.report(empty, "e2", a40_not_trained=True)["label"] == "not run: A40 not trained"
    assert "primary" not in a42.report(empty, "e2", a40_not_trained=True)


def test_a39_and_a40_never_read_a40_note_s_runs(tmp_path):
    four(tmp_path)
    plant(tmp_path, "lora", follows=HALF)
    r = a39.report(tmp_path, "e2")
    assert "a40_note" not in r["systems"] and "a40_note" not in r["completeness"]
    assert set(a40.systems(tmp_path, "e2")) == {"base", "prompt_only", "lora", "a40"}
    assert set(a42.systems(tmp_path, "e2")) == {"base", "prompt_only", "a40", "a40_note"}
