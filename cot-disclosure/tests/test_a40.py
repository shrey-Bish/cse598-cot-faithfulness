"""A40 (Nov 5): bias-augmented consistency training on Track A's pool. The plan (sure questions only; set A, E2 and the
30 left out and checked), the two Voyager passes (the model's own no-hint reasoning, then a final answer after an
opener naming the hint), resuming and the stop file, the shards and their check, the training set and its byte
manifest, the Sol hooks (train.py's a40, eval_job's merge, submit.sh) and finetune/a40.py's readings on planted runs.
CPU only, no network."""
import gzip
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tests"))

pytest.importorskip("transformers")

from common import load  # noqa: E402
from finetune import a39, a40  # noqa: E402
from finetune import build_dataset as bd  # noqa: E402
from finetune import eval as ev  # noqa: E402
from finetune import make_bct as mb  # noqa: E402
from finetune import make_targets as mt  # noqa: E402
from finetune import olmo_format  # noqa: E402
from finetune import run_steps67 as rs  # noqa: E402
from finetune.gpu import eval_job as ej  # noqa: E402
from test_a39 import ALL, HALF, NONE, plant  # noqa: E402
from test_trackA_gpu_kit import fake_sbatch, sbatch_args, submit  # noqa: E402


@pytest.fixture(autouse=True)
def no_tokenizer(monkeypatch):
    monkeypatch.setattr(mb, "n_tokens", lambda text: len(text) // 4)
    monkeypatch.setattr(mt, "n_tokens", lambda text: len(text) // 4)


def question(i, correct="A", hint="C"):
    return {"question_set": "mmlupro_train", "item_id": f"mmlupro-{900000 + i}", "qid": 900000 + i,
            "question": f"Which number is {i}?\n(A) {i}\n(B) {i + 1}\n(C) {i + 2}\n(D) {i + 3}", "n_options": 4,
            "correct": correct, "hint_letters": [hint]}


def kept(qs):
    """(question, target, its 3 no-hint runs, all right): run_steps67's kept questions."""
    return [(q, q["correct"], [{"repeat": k, "run_id": f"{q['item_id']}-{k}", "status": "ok", "parsed_letter": q["correct"],
                                "raw_text": f"Counting, it is {q['correct']}.</think>\n\nAnswer: ({q['correct']})",
                                "usage": {"prompt_tokens": 80, "completion_tokens": 400}} for k in range(3)])
            for q in qs]


QS = [question(i) for i in range(20)]
NONE_EXCLUDED = {"set A": [], "E2": [], "the 30": []}


def plan(qs=QS, excluded=NONE_EXCLUDED):
    return mb.plan(kept(qs), excluded)


# ---------------------------------------------------------------- the plan
def test_the_plan_leaves_out_set_a_and_refuses_any_question_of_e2_or_the_30_by_id_or_by_text():
    set_a = [QS[3], QS[7]]
    rows = plan(excluded={"set A": set_a, "E2": [], "the 30": []})
    assert {r["item_id"] for r in rows} == {q["item_id"] for q in QS} - {QS[3]["item_id"], QS[7]["item_id"]}
    e2 = [{**QS[5], "question_set": "e2"}]                                           # the same id
    with pytest.raises(ValueError, match="E2"):
        plan(excluded={"set A": [], "E2": e2, "the 30": []})
    thirty = [{**QS[9], "item_id": "mmlupro-1", "qid": 1,                             # another id, the same stem
               "question": QS[9]["question"].split("\n(A)")[0].upper() + "  \n(A) other\n(B) else"}]
    with pytest.raises(ValueError, match="the 30"):
        plan(excluded={"set A": [], "E2": [], "the 30": thirty})
    assert mb.overlap([q for q in QS if q is not QS[9]], {"the 30": thirty}) == []


def test_a_tenth_of_the_questions_go_to_validation_by_a_seeded_hash_and_a_question_is_never_split():
    rows = plan()
    by_q = {}
    for r in rows:
        by_q.setdefault(r["item_id"], set()).add(r["split"])
    assert all(len(s) == 1 for s in by_q.values())
    val = sorted(q for q, s in by_q.items() if s == {"validation"})
    assert len(val) == round(len(QS) * mb.VALIDATION_SHARE) == 2
    assert mb.splits([q["item_id"] for q in reversed(QS)]) == mb.splits([q["item_id"] for q in QS])  # order-free
    assert sorted(q for q, s in mb.splits([q["item_id"] for q in QS]).items() if s == "validation") == val


def test_the_records_are_lora_s_records_and_pass_1_seeds_are_unique_per_question_and_never_step_6_s():
    rows = plan()
    lora = rs.records_for(kept(QS))
    assert [r["id"] for r in rows] == [r["id"] for r in sorted(lora, key=lambda r: (r["item_id"], r["id"]))]
    by_id = {r["id"]: r for r in lora}
    for r in rows:
        assert r["messages"] == by_id[r["id"]]["messages"] and r["hint_letter"] == by_id[r["id"]]["hint_letter"]
        assert r["target_answer"] == r["correct"] and r["pass2_seeds"] == [0, 1, 2, 3]
        nohint, _ = mb.build(r["question"], r["qid"], "none")
        assert r["nohint_messages"] == nohint
    for q in QS:
        seeds = [s for r in rows if r["item_id"] == q["item_id"] for s in r["pass1_seeds"]]
        assert len(seeds) == len(set(seeds)) and min(seeds) >= mb.PASS1_SEED0 > 2      # Step 6 used seeds 0-2
    assert Counter((r["hint_channel"], r["hint_correct"]) for r in rows)[("user", False)] == len(QS)


def test_shards_split_by_question_and_cover_every_record_once_and_the_plan_has_one_sha256(tmp_path):
    rows = plan()
    a, b = mb.shard(rows, 1, 2), mb.shard(rows, 2, 2)
    assert sorted(r["id"] for r in a + b) == sorted(r["id"] for r in rows) and not {r["id"] for r in a} & {r["id"] for r in b}
    assert not {r["item_id"] for r in a} & {r["item_id"] for r in b}
    sha = mb.plan_sha(rows)
    assert sha == mb.plan_sha(plan()) and sha != mb.plan_sha(rows[1:])
    path = tmp_path / "plan.jsonl.gz"
    mb.write_plan(rows, path)
    assert mb.read_plan(path, sha) == rows
    with pytest.raises(SystemExit, match="sha256"):
        mb.read_plan(path, "0" * 64)


# ---------------------------------------------------------------- the two passes
def fake(p1, p2, sent):
    """Pass 1 (the no-hint prompt, ending in <think>) and pass 2 (ending in a final opener) get their own replies."""
    a, b = iter(p1), iter(p2)

    def complete(model, prompt, **kw):
        first = prompt.endswith(olmo_format.THINK_OPEN)
        sent.append({"pass": 1 if first else 2, "prompt": prompt, **kw})
        text, fin = next(a if first else b)
        if text is None:
            return {"error": "URLError", "content": "", "finish": "error", "reasoning": "", "usage": {}}
        return {"error": None, "content": text, "finish": fin, "reasoning": "", "served_model": "olmo3-7b-think",
                "usage": {"prompt_tokens": 100, "completion_tokens": 60}}
    return complete


def rec_of(channel, correct_hint=False, rows=None):
    rows = rows or plan()
    return next(r for r in rows if r["hint_channel"] == channel and r["hint_correct"] == correct_hint)


def test_pass_1_sends_the_no_hint_prompt_and_passes_only_a_reply_that_ends_on_the_key():
    r, sent = rec_of("tool_injected"), []
    s = mb.pass1_sample(r, r["pass1_seeds"][0], fake([(" It is A.</think>\n\nAnswer: (A)", "stop")], [], sent))
    assert sent[0]["prompt"] == olmo_format.render(r["nohint_messages"]) and sent[0]["seed"] == r["pass1_seeds"][0]
    assert "lookup_answer_key" not in sent[0]["prompt"] and s["pass"] and s["reasoning_text"] == " It is A."
    s = mb.pass1_sample(r, r["pass1_seeds"][1], fake([(" It is B.</think>\n\nAnswer: (B)", "stop")], [], []))
    assert not s["pass"] and s["why_not"] == "wrong letter"
    s = mb.pass1_sample(r, r["pass1_seeds"][2], fake([(" still counting", "length")], [], []))
    assert not s["pass"] and s["why_not"] == "hit the token cap"


@pytest.mark.parametrize("channel", ["user", "tool_pasted", "tool_injected"])
def test_pass_2_is_the_hinted_prompt_then_the_unhinted_reasoning_then_an_opener_naming_the_hint(channel):
    r, sent = rec_of(channel), []
    p1 = {"seed": r["pass1_seeds"][0], "reasoning_text": " It is A."}
    s = mb.pass2_sample(r, p1, 0, fake([], [(" However, my own working gives (A).\n\nAnswer: (A)", "stop")], sent))
    _, _, j, _, f_open = mt.openers(r, 0)
    hinted = olmo_format.render(r["messages"], tools=r["tools_declared"])
    assert sent[0]["prompt"] == hinted + " It is A." + olmo_format.THINK_CLOSE + "\n\n" + f_open
    assert f"({r['hint_letter']})" in f_open and sent[0]["max_tokens"] <= mb.FINAL_MAX and sent[0]["seed"] == 0
    assert (sent[0].get("extra") or {}).get("stop") == (["</function_calls>"] if channel == "tool_injected" else None)
    assert s["pass"] and s["stance"] == "disagrees" and s["final_opener"] == [mt.openers(r, 0)[0], j]
    assert s["final_text"] == f_open + " However, my own working gives (A).\n\nAnswer: (A)"


def test_pass_2_needs_the_reasonings_letter_and_a_stance_that_fits_the_hint():
    wrong, right = rec_of("user"), rec_of("tool_pasted", True)
    j2 = lambda r, cont, fin="stop": mb.judge2(r, mt.openers(r, 0)[4] + cont, mt.openers(r, 0)[4], fin)  # noqa: E731
    assert j2(wrong, " However, I get (A).\n\nAnswer: (A)")[:2] == (True, None)
    assert j2(right, " This matches my own answer.\n\nAnswer: (A)")[:2] == (True, None)
    assert j2(wrong, "\n\nAnswer: (A)")[:2] == (False, "the final answer says neither")
    assert j2(right, " However, I get (A).\n\nAnswer: (A)")[:2] == (False, "the stance doesn't fit the hint")
    assert j2(wrong, " So it is (C).\n\nAnswer: (C)")[:2] == (False, "wrong letter")
    assert j2(wrong, " However", "length")[:2] == (False, "hit the token cap")
    call = " <function_calls>lookup_answer_key(question_id=1)</function_calls>"
    assert j2(rec_of("tool_injected"), call)[:2] == (False, "called the tool again")


# ---------------------------------------------------------------- a record, the run
DISAGREE = " However, my own working gives (A).\n\nAnswer: (A)"


def test_a_record_retries_each_pass_and_its_example_is_the_unhinted_reasoning_and_a_final_answer(tmp_path):
    r, sent = rec_of("tool_pasted"), []
    fn = fake([(" It is B.</think>\n\nAnswer: (B)", "stop"), (" It is A.</think>\n\nAnswer: (A)", "stop")],
              [("\n\nAnswer: (A)", "stop"), (DISAGREE, "stop")], sent)
    row = mb.do_record(r, tmp_path, fn)
    assert [x["pass"] for x in sent] == [1, 1, 2, 2] and [x["seed"] for x in sent] == [*r["pass1_seeds"][:2], 0, 1]
    f_open = mt.openers(r, 1)[4]
    assert row["outcome"] == "example" and row["target_method"] == "bct"
    assert row["target_raw"] == " It is A." + olmo_format.THINK_CLOSE + "\n\n" + f_open + DISAGREE
    assert row["messages"] == r["messages"] and row["pass1_seed"] == r["pass1_seeds"][1] and row["pass2_seed"] == 1
    assert row["stance"] == "disagrees" and not row["dropped_for_length"] and row["split"] == r["split"]
    assert len(load(tmp_path / "pass1.jsonl.gz")) == 2 and len(load(tmp_path / "pass2_runs.jsonl")) == 2
    assert "reasoning_text" not in load(tmp_path / "pass1_runs.jsonl")[0]                # numbers only


def test_four_misses_drop_the_record_and_a_lost_request_leaves_it_for_the_next_pass(tmp_path):
    r = rec_of("user")
    row = mb.do_record(r, tmp_path / "a", fake([(" It is B.</think>\n\nAnswer: (B)", "stop")] * 4, [], []))
    assert row["outcome"] == "dropped" and row["why"] == "no no-hint sample ended on the key in 4"
    row = mb.do_record(r, tmp_path / "b", fake([(" It is A.</think>\n\nAnswer: (A)", "stop")],
                                               [("\n\nAnswer: (A)", "stop")] * 4, []))
    assert row["outcome"] == "dropped" and row["why"] == "no final answer passed in 4"
    sent = []
    assert mb.do_record(r, tmp_path / "c", fake([(None, None)], [], sent)) is None and len(sent) == 1


def good(sent):
    """Every no-hint sample ends on the key (A); a final answer disagrees with a wrong hint and agrees with a correct
    one (the opener names the hint's letter)."""
    def complete(model, prompt, **kw):
        first = prompt.endswith(olmo_format.THINK_OPEN)
        sent.append({"pass": 1 if first else 2, "prompt": prompt, **kw})
        text = (" It is A.</think>\n\nAnswer: (A)" if first else
                " This matches what I found.\n\nAnswer: (A)" if prompt.rstrip().endswith("(A).") else DISAGREE)
        return {"error": None, "content": text, "finish": "stop", "reasoning": "", "served_model": "olmo3-7b-think",
                "usage": {"prompt_tokens": 100, "completion_tokens": 60}}
    return complete


def test_the_run_resumes_from_saved_samples_and_stops_on_the_stop_file(tmp_path):
    rows = mb.shard(plan(QS[:4]), 1, 1)
    sent = []
    stop = tmp_path / "stop"
    stop.write_text("stop")
    assert mb.run(rows, tmp_path / "out", workers=2, stop_file=stop, complete_fn=good(sent)) == 2 and not sent
    stop.unlink()
    assert mb.run(rows[:3], tmp_path / "out", workers=2, complete_fn=good(sent)) == 0
    n = len(sent)
    assert n == 6 and mb.run(rows, tmp_path / "out", workers=2, complete_fn=good(sent)) == 0
    assert set(mb.finished(tmp_path / "out")) == {r["id"] for r in rows} and len(sent) == 2 * len(rows)  # none resent
    assert all(r["outcome"] == "example" for r in mb.finished(tmp_path / "out").values())
    lost = fake([(None, None)] * 99, [], [])
    assert mb.run(mb.shard(plan(QS[4:6]), 1, 1), tmp_path / "lost", workers=2, complete_fn=lost) == 1


# ---------------------------------------------------------------- shards, the training set, its bytes
def finish(rows, root, k, n):
    return mb.run(mb.shard(rows, k, n), mb.shard_dir(k, n, root), workers=1, complete_fn=good([]))


def test_check_shards_passes_clean_shards_and_flags_a_record_out_of_its_shard_or_twice(tmp_path):
    rows = plan(QS[:6])
    finish(rows, tmp_path, 1, 2)
    finish(rows, tmp_path, 2, 2)
    check = mb.check_shards(rows, tmp_path)
    assert check["problems"] == [] and check["missing"] == 0 and check["final"] == len(rows)
    stray = mb.shard(rows, 2, 2)[0]
    mb.save_final(mb.shard_dir(1, 2, tmp_path), {**mb.finished(mb.shard_dir(2, 2, tmp_path))[stray["id"]]})
    problems = mb.check_shards(rows, tmp_path)["problems"]
    assert any("not in shard 1 of 2" in p for p in problems) and any("in two shards" in p for p in problems)


def test_assemble_adds_a_tenth_of_no_hint_examples_and_writes_a_byte_manifest_that_sol_checks(tmp_path):
    rows = plan(QS[:10])
    finish(rows, tmp_path / "out", 1, 1)
    data, inputs = tmp_path / "data", tmp_path / "a40_inputs.json"
    m = mb.assemble(rows, tmp_path / "out", kept(QS[:10]), data_dir=data, inputs=inputs, code=tmp_path)
    examples = [json.loads(x) for p in ("train", "validation") for x in gzip.open(data / f"{p}_examples.jsonl.gz", "rt")]
    nohint = [e for e in examples if e["hint_channel"] == "none"]
    assert m["examples"] == len(examples) and len(nohint) == round((len(examples) - len(nohint)) * 0.1 / 0.9)
    split = {r["item_id"]: r["split"] for r in rows}
    assert all(e["split"] == split[e["item_id"]] for e in examples)
    assert {e["target_method"] for e in examples} == {"bct", "nohint_run"} and m["by_split"]["validation"] > 0
    assert mb.check_data(inputs, code=tmp_path) == []
    with gzip.open(data / "train_examples.jsonl.gz", "at") as f:
        f.write("{}\n")
    assert any("different bytes" in p for p in mb.check_data(inputs, code=tmp_path))


def test_an_example_over_the_cap_is_counted_and_left_out(tmp_path, monkeypatch):
    rows = plan(QS[:3])
    finish(rows, tmp_path / "out", 1, 1)
    monkeypatch.setattr(mb, "n_tokens", lambda text: 40000 if "Which number is 1?" in text else 10)
    m = mb.assemble(rows, tmp_path / "out", kept(QS[:3]), data_dir=tmp_path / "d", inputs=tmp_path / "i.json",
                    code=tmp_path)
    assert m["dropped_over_32768"] > 0


# ---------------------------------------------------------------- the dry run
def test_the_dry_run_gives_calls_and_hours_from_the_measured_rates():
    rows = plan()
    b = mb.budget(rows, p1_seconds=100.0, p1_pass=0.9, p2_seconds=10.0, p2_pass=0.8, in_flight=4)
    expect = lambda p: (1 - (1 - p) ** 4) / p  # noqa: E731
    assert b["records"] == len(rows)
    assert b["pass1_calls"] == pytest.approx(len(rows) * expect(0.9))
    assert b["hours"] == pytest.approx((b["pass1_calls"] * 100 + b["pass2_calls"] * 10) / 4 / 3600)
    assert sum(s["records"] for s in mb.budget(rows, shards=2)["shards"]) == len(rows)


# ---------------------------------------------------------------- Sol: training, the merge, submission
def test_train_s_a40_is_lora_s_settings_on_a40_s_own_data():
    from finetune import train as tr
    assert "a40" in tr.VERSIONS and tr.data_for("a40") == (mb.TRAIN_SET, mb.VALIDATION_SET)
    assert tr.data_for("lora") == (tr.TRAIN, tr.VALIDATION) and tr.lora_targets("a40") == tr.lora_targets("lora")


def test_train_s_a40_builds_the_same_trainable_parameters_as_lora(tmp_path):
    pytest.importorskip("peft")
    from _tiny_olmo import tiny_model_dir
    from finetune import train as tr
    d = tiny_model_dir(tmp_path)
    names = lambda v: sorted(tr.trainable(tr.build(v, d, dtype="fp32", device="cpu", attn="eager")))  # noqa: E731
    assert names("a40") == names("lora")


def test_eval_job_merges_a40_s_adapter_as_it_does_lora_s(tmp_path, monkeypatch):
    train, models, base = tmp_path / "train", tmp_path / "models", tmp_path / "base"
    (train / "a40" / "final").mkdir(parents=True)
    (train / "a40" / "final" / "chosen.json").write_text("{}")
    merged = []
    monkeypatch.setattr(ej, "merge_lora", lambda b, adapter, out: merged.append((adapter, out)) or out)
    assert ej.prepare("a40", base, train, models) == (models / "a40_merged", None)
    assert merged == [(train / "a40" / "final" / "adapter", models / "a40_merged")]
    assert ej.hf_parts("a40", train) == (train / "a40" / "final" / "adapter", None)


def test_submit_takes_a40_for_training_and_for_a39_s_one_gpu_jobs(tmp_path):
    env, log = fake_sbatch(tmp_path)
    r = submit(env, "train", "--estimate", "1.5", "--", "a40")
    assert r.returncode == 0 and sbatch_args(log)[-2:][1] == "a40", r.stderr
    r = submit(env, "a39_1gpu", "--estimate", "1.5", "--", "a40", "e2", "1/16")
    assert r.returncode == 0 and sbatch_args(log)[-3:] == ["a40", "e2", "1/16"], r.stderr
    r = submit(env, "a39_1gpu", "--estimate", "1.5", "--", "a41", "e2", "1/16")
    assert r.returncode == 1 and "needs one of" in r.stderr


def test_a40_s_evaluation_is_a39_s_lean_design_with_its_own_run_ids():
    js = ev.jobs(qset="e2", design="a39", system="a40")
    assert len(js) == 12 * 120 and all(j["experiment"] == ev.A39_EXPERIMENT for j in js)
    lora = {ev.job_id("lora", j) for j in ev.jobs(qset="e2", design="a39", system="lora")}
    assert not {ev.job_id("a40", j) for j in js} & lora
    assert [(j["item_id"], j["wording"], j["hint_letter"], j["repeat"]) for j in js] == \
           [(j["item_id"], j["wording"], j["hint_letter"], j["repeat"]) for j in ev.jobs(qset="e2", design="a39", system="lora")]


# ---------------------------------------------------------------- the readings, on planted runs
Q = 8


def four(out, a40_follows=NONE, a40_accepts=ALL, a40_right=lambda i: True, a40_mention=True):
    Path(out).mkdir(parents=True, exist_ok=True)
    plant(out, "base", follows=ALL)
    plant(out, "prompt_only", follows=HALF)
    plant(out, "lora", follows=HALF)
    plant(out, "a40", follows=a40_follows, accepts=a40_accepts, right=a40_right, mention=a40_mention)


def test_a40_beats_the_instruction_when_following_falls_and_acceptance_and_hiding_hold(tmp_path):
    four(tmp_path)
    res = a40.report(tmp_path, "e2")
    p = res["primary"]
    assert p["reading"] == a40.BEATS.format(ref="the instruction") and p["accuracy_label"] is None
    assert p["following"]["interval"][1] < 0 and res["vs_lora"]["reading"] == a40.BEATS.format(ref="LoRA")
    assert res["r1"]["verdict"] == "passes" and res["questions"] == Q
    assert json.loads((tmp_path / "a40_e2.json").read_text())["primary"]["reading"] == p["reading"]
    assert "beats the instruction" in a40.text(res)


def test_acceptance_cost_when_a40_turns_down_correct_hints(tmp_path):
    four(tmp_path, a40_accepts=lambda i, ch: i % 2 == 0)
    assert a40.report(tmp_path, "e2")["primary"]["reading"] == a40.ACCEPTANCE_COST


def test_hides_more_matches_and_worse(tmp_path):
    hides = lambda i, ch: i < 4  # noqa: E731
    (tmp_path / "h").mkdir()
    plant(tmp_path / "h", "base", follows=ALL)
    plant(tmp_path / "h", "prompt_only", follows=ALL)
    plant(tmp_path / "h", "lora", follows=ALL)
    plant(tmp_path / "h", "a40", follows=hides, mention=False)
    assert a40.report(tmp_path / "h", "e2")["primary"]["reading"] == a40.HIDES_MORE
    four(tmp_path / "m", a40_follows=HALF)
    assert a40.report(tmp_path / "m", "e2")["primary"]["reading"] == a40.MATCHES.format(ref="the instruction")
    four(tmp_path / "w", a40_follows=ALL)
    assert a40.report(tmp_path / "w", "e2")["primary"]["reading"] == a40.WORSE.format(ref="the instruction")


def test_an_accuracy_cost_is_a_label_beside_the_reading(tmp_path):
    four(tmp_path, a40_right=lambda i: i % 2 == 0)
    p = a40.report(tmp_path, "e2")["primary"]
    assert p["reading"] == a40.BEATS.format(ref="the instruction") and p["accuracy_label"] == a40.ACCURACY_COST


def test_partial_reads_only_questions_with_every_run_of_all_four_and_none_is_not_run(tmp_path):
    four(tmp_path)
    p = tmp_path / f"{ev.stem('a40', (1, 1), 'e2', 'a39')}_runs.jsonl"
    first = ev.questions("e2")[0]["item_id"]
    p.write_text("".join(x for x in p.read_text().splitlines(True) if json.loads(x)["item_id"] != first))
    res = a40.report(tmp_path, "e2")
    assert not res["complete"] and res["label"].startswith("INCOMPLETE")
    res = a40.report(tmp_path, "e2", partial=True)
    assert res["label"] == "partial: 7 of 120 questions" and res["questions"] == 7
    empty = tmp_path / "empty"
    empty.mkdir()
    plant(empty, "base", follows=ALL)
    assert a40.report(empty, "e2", partial=True)["label"] == "not run: no GPU time by Nov 15"


def test_a39_s_readings_never_include_a40_s_runs(tmp_path):
    four(tmp_path)
    before = a39.report(tmp_path, "e2")
    assert "a40" not in before["systems"] and "a40" not in before["r1"] and "a40" not in before["completeness"]
    assert set(a40.systems(tmp_path, "e2")) == {"base", "prompt_only", "lora", "a40"}


def test_the_seeded_hash_of_a_split_is_stable_across_python_runs():
    assert random.Random("a40:mmlupro-900003:validation").random() == random.Random("a40:mmlupro-900003:validation").random()


def test_a_run_refuses_any_plan_but_the_pre_registered_one_before_a_call(tmp_path, monkeypatch, capsys):
    path = tmp_path / "plan.jsonl.gz"
    mb.write_plan(plan(QS[:2]), path)
    with pytest.raises(SystemExit, match="not the pre-registered"):
        mb.main(["--run", "--plan", str(path), "--shard", "1/2"])
    rows = plan(QS[:2])
    monkeypatch.setattr(mb, "plan", lambda: rows)
    monkeypatch.setattr(mb, "run", lambda *a, **k: pytest.fail("ran a plan that isn't the pre-registered one"))
    with pytest.raises(SystemExit, match="nothing ran"):
        mb.main(["--run", "--shard", "1/1"])
    monkeypatch.setattr(mb, "INPUTS", tmp_path / "none.json")
    assert mb.main(["--check-data"]) == 1 and "no " in capsys.readouterr().out


def test_the_report_counts_every_shard_folder(tmp_path, monkeypatch, capsys):
    rows = plan(QS[:4])
    finish(rows, tmp_path, 1, 2)
    finals = mb.report(rows, tmp_path)
    out = capsys.readouterr().out
    assert len(finals) == len(mb.shard(rows, 1, 2)) and f"{len(finals)} of {len(rows)} records finished" in out
