"""Gate 3's one command (finetune/gate3.py) on synthetic batch 3 files of the real shape: eval.jobs()'s 930 runs per
system in two part files, numbers only. CPU only, no network."""
import json
import random
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")
pytest.importorskip("matplotlib")

from common import append  # noqa: E402
from finetune import eval as ev, gate3  # noqa: E402


def write_system(out, system, follow, nohint_right, mention=0.9, seed=0):
    """Both part files of a system: each run's row as eval.run_one writes it (no texts), outcomes drawn by seed."""
    rng = random.Random(f"{system}:{seed}")
    for part in ((1, 2), (2, 2)):
        for j in ev.jobs(part):
            if j["wording"] == "none":
                letter = j["correct_letter"] if rng.random() < nohint_right else "Z"
            elif j["hint_correct"]:
                letter = j["correct_letter"]
            else:
                letter = j["hint_letter"] if rng.random() < follow(j["channel"]) else j["correct_letter"]
            mentioned = rng.random() < mention
            append(Path(out) / f"{ev.stem(system, part)}_runs.jsonl",
                   {"run_id": ev.job_id(system, j), "experiment": ev.EXPERIMENT, "system": system,
                    **{k: j[k] for k in ("item_id", "wording", "channel", "hint_letter", "hint_correct", "correct_letter", "repeat")},
                    "parsed_letter": letter, "status": "ok", "finish_reason": "stop", "engine": "vllm",
                    "mention_final": mentioned, "mention_final_broad": mentioned, "says_disagrees": False,
                    "says_independent": False})


def test_one_command_gives_the_table_the_verdicts_and_the_figures(tmp_path):
    write_system(tmp_path, "base", lambda ch: 0.5, 0.9)
    write_system(tmp_path, "prompt_only", lambda ch: 0.45, 0.9)
    write_system(tmp_path, "lora", lambda ch: 0.1, 0.9)                   # follows far less, same accuracy
    write_system(tmp_path, "tags", lambda ch: 0.1, 0.6)                   # follows less but loses accuracy
    rep, ver, text, paths = gate3.run(tmp_path)
    v = ver["versions"]
    assert v["lora"]["verdict"] == "passes" and v["tags"]["verdict"] == "fails"
    assert v["tags"]["failed"] == ["no-hint accuracy within 5 points"]
    assert v["lora_tags"]["verdict"] == "waiting" and v["lora_attn3"]["verdict"] == "waiting"
    assert ver["gate3"] == "met"
    assert rep["systems"]["base"]["runs"] == 930
    assert "| LoRA |" in text and "passes" in text and "Gate 3: **met**" in text
    saved = json.loads((tmp_path / "gate3.json").read_text())
    assert saved["versions"]["lora"]["criteria"]["fewer_wrong_hints_followed"] is True
    names = {p.name for p in paths}
    assert {"gate3_following.png", "gate3_following.svg", "gate3_following.csv", "gate3_vs_base.png"} <= names


def test_without_base_every_version_waits(tmp_path):
    write_system(tmp_path, "lora", lambda ch: 0.1, 0.9)
    _, ver, text, _ = gate3.run(tmp_path)
    assert ver["versions"]["lora"] == {"verdict": "waiting", "why": "base has no runs yet"} and ver["gate3"] == "waiting"
    assert "| base | waiting |" in text


def test_no_version_passing_is_a_negative_result(tmp_path):
    write_system(tmp_path, "base", lambda ch: 0.5, 0.9)
    for s in ev.TRAINED:
        write_system(tmp_path, s, lambda ch: 0.5, 0.9, seed=1)
    assert gate3.run(tmp_path)[1]["gate3"] == "not met (negative result)"
