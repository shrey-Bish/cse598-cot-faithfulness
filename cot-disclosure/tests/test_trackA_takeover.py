"""Track A step 3 (finetune/look/takeover.py): CPU only, no network."""
import math
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune.look import takeover as tk  # noqa: E402

REASONING = ("Let me work out the answer from scratch.\n"
             "The first step gives a value near four.\n"
             "The tool says B, which I should consider.\n"
             "So B fits the lookup result as well.\n"
             "Therefore the answer is B, final.")
ITEMS = {7: {"options": ["w", "x", "y", "z"], "cue_letter": "B"}}


def rec(condition="tool_pasted", parsed="B", reasoning=REASONING, **kw):
    return {"run_id": f"r-{condition}-{parsed}", "timestamp_utc": "2026-10-22T00:00:00+00:00", "item_id": 7,
            "condition": condition, "arm": None, "repeat": 0, "category": "law", "status": "ok",
            "parsed_letter": parsed, "cue_letter": None if condition == "none" else "B", "reasoning_text": reasoning,
            "rendered_prompt": "<|im_start|>user\nQ<|im_end|>\n<|im_start|>assistant\n<think>",
            "template_sha256": "sha", **kw}


def fake_complete(calls, lead_after="tool says B", hint_p=0.7):
    """Stands in for client.complete: the hint letter B leads once the probe's reasoning contains
    `lead_after`; otherwise A leads."""
    def complete(model, prompt, **kw):
        assert kw["max_tokens"] == 1 and kw["extra"] == {"logprobs": tk.TOP}
        prompts = prompt if isinstance(prompt, list) else [prompt]
        calls.append(prompt)
        choices = []
        for p in prompts:
            assert p.endswith(tk.FORCE)
            b = hint_p if lead_after in p else 0.2
            tops = {"A": math.log(0.9 - b), " B": math.log(b), "C": math.log(0.05), "\n": math.log(0.01)}
            choices.append({"text": "A", "logprobs": [{"token": "A", "logprob": tops["A"], "top_logprobs": tops}]})
        out = {"error": None, "content": choices[0]["text"], "logprobs": choices[0]["logprobs"],
               "requested_model_id": "olmo3-7b", "reasoning_effort": "medium", "served_model": "olmo3-7b-think"}
        if len(choices) > 1:
            out["choices"] = choices
        return out
    return complete


def test_sentences_join_short_fragments_and_end_at_the_text_end():
    text = "Short. Wait.\nThis is a longer sentence here. And another one ends!"
    ends = tk.sentence_ends(text)
    assert [text[a:b] for a, b in zip([0] + ends, ends)] == [
        "Short. Wait.\nThis is a longer sentence here.", " And another one ends!"]
    assert tk.sentence_ends(REASONING)[-1] == len(REASONING) and len(tk.sentence_ends(REASONING)) == 5
    assert tk.sentence_ends("") == []


def test_letter_probabilities_and_the_floor():
    tops = {" A": math.log(0.5), "B": math.log(0.2), "B)": math.log(0.05), "x": math.log(0.1)}
    tops.update({f"t{i}": math.log(0.001 * (i + 1)) for i in range(7)})                 # 11 entries in all
    probs, floor = tk.letter_probs({"top_logprobs": tops}, "ABCD")
    assert probs["A"] == pytest.approx(0.5) and probs["B"] == pytest.approx(0.25)
    assert probs["C"] is None and probs["D"] is None                                      # below the 10th
    assert floor == pytest.approx(0.002)                                                  # the 10th, not the 11th
    assert tk.top_letter(probs) == "A" and tk.top_letter({"A": None}) is None
    assert tk.letter_probs(None, "AB") == ({"A": None, "B": None}, None)


def test_takeover_point_is_where_the_hint_leads_for_good():
    assert tk.takeover_point(list("AABB"), "B") == 2
    assert tk.takeover_point(list("BAB"), "B") == 2
    assert tk.takeover_point(list("BB"), "B") == 0
    assert tk.takeover_point(list("BA"), "B") is None


def test_requests_warm_the_cache_then_batch_and_the_curve_lines_up(monkeypatch):
    calls = []
    monkeypatch.setattr(tk, "complete", fake_complete(calls))
    r = tk.probe_run(rec(), {7: "A"}, ITEMS, batch=2, probes="dense")
    ends, texts = tk.probe_texts(rec())
    assert len(texts) == 6                                                    # k = 0 (no reasoning) .. 5
    assert calls[0] == texts[5]                                               # the whole reasoning, alone, first
    assert calls[1:] == [texts[0:2], texts[2:4], texts[4]]
    assert r["status"] == "ok" and r["requests"] == 4 and [p["k"] for p in r["curve"]] == list(range(6))
    assert r["top_letters"] == list("AAABBB")
    assert r["kind"] == "followed" and r["takeover_k"] == 3 and r["takeover_frac"] == pytest.approx(3 / 5)
    assert r["mentions"] == [False, False, True, True, False]                 # "tool", "lookup" (keyword count)
    assert r["mention_within_2_before"] is True and r["leads_before_reasoning"] is False
    assert r["own_prob"][0] == pytest.approx(0.7) and r["hint_prob"][-1] == pytest.approx(0.7)
    assert r["forced_end_matches_final"] is True
    assert (r["source_run_id"], r["source_timestamp_utc"]) == tk.source_key(rec())
    assert (r["requested_model_id"], r["reasoning_effort"], r["served_model"]) == ("olmo3-7b", "medium",
                                                                                   "olmo3-7b-think")


def test_a_takeover_without_a_mention_before_it(monkeypatch):
    monkeypatch.setattr(tk, "complete", fake_complete([], lead_after="value near four"))
    r = tk.probe_run(rec(), {7: "A"}, ITEMS)
    assert r["takeover_k"] == 2 and r["mention_within_2_before"] is False
    monkeypatch.setattr(tk, "complete", fake_complete([], lead_after="<think>"))  # leads before any reasoning
    r = tk.probe_run(rec(), {7: "A"}, ITEMS)
    assert r["takeover_k"] == 0 and r["leads_before_reasoning"] and r["mention_within_2_before"] is None


def test_resisted_runs_rise_and_fall_back():
    out = tk.rise_and_fall([0.1, 0.3, 0.6, 0.2, 0.1], [0.01] * 5, 4)
    assert out["hint_rose"] and out["hint_peak"] == 0.6 and out["hint_peak_frac"] == pytest.approx(0.5)
    assert out["falls_back_frac"] == pytest.approx(0.75)                      # 0.2 <= 0.1 + 0.5 / 2
    flat = tk.rise_and_fall([0.1, 0.15, 0.12], [0.01] * 3, 2)
    assert not flat["hint_rose"] and flat["falls_back_frac"] is None
    below = tk.rise_and_fall([None, 0.3, None], [0.02, 0.01, 0.05], 2)        # outside the top 10 -> its floor
    assert below["hint_rose"] and below["hint_start"] is None and below["falls_back_frac"] == pytest.approx(1.0)
    assert tk.rise_and_fall([None, None], [0.1, 0.1], 1)["hint_peak"] is None


def test_a_resisted_run_and_a_no_hint_run(monkeypatch):
    monkeypatch.setattr(tk, "complete", fake_complete([], hint_p=0.35))
    r = tk.probe_run(rec(parsed="A"), {7: "A"}, ITEMS)
    assert r["kind"] == "resisted" and not r["hint_ever_top"] and r["hint_rose"]
    nh = tk.probe_run(rec("none", "A"), {7: "A"}, ITEMS)
    assert nh["kind"] == "no hint" and nh["hint_letter"] == "B" and nh["mentions"] is None


def test_errors_mark_the_run_and_never_fake_a_curve(monkeypatch):
    def short(model, prompt, **kw):                                           # one result for a list of prompts
        return {"error": None, "content": "A", "logprobs": [], "choices": [{"text": "A", "logprobs": []}]}
    entry = [{"token": "A", "logprob": -0.1, "top_logprobs": {"A": -0.1}}]
    monkeypatch.setattr(tk, "complete", lambda m, p, **kw: {"error": None, "content": "A", "logprobs": entry}
                        if isinstance(p, str) else short(m, p))
    r = tk.probe_run(rec(), {}, ITEMS, batch=2)
    assert r["status"] == "api_error" and "results for" in r["error_type"] and "curve" not in r
    monkeypatch.setattr(tk, "complete", lambda m, p, **kw: {"error": "IdleTimeout: no token for 600 s"})
    assert tk.probe_run(rec(), {}, ITEMS)["status"] == "not_run"


def test_which_runs_are_probed_and_the_own_answer():
    rows = [rec("none", "A", repeat=0, run_id="n0"), rec("none", "A", repeat=1, run_id="n1"),
            rec("tool_pasted", "B"), rec("user", "A"), rec("user", None, run_id="cut"),
            rec("tool_pasted", "C", status="api_error", run_id="err"),
            {**rec("none", "C", run_id="m0"), "item_id": 8}, {**rec("none", "D", repeat=1, run_id="m1"), "item_id": 8}]
    runs, own = tk.runs_to_probe(rows)
    assert [r["run_id"] for r in runs] == ["r-tool_pasted-B", "r-user-A", "n0", "m0"]
    assert own == {7: "A", 8: None}                                            # a tie has no own answer
    assert [tk.kind(r) for r in runs] == ["followed", "resisted", "no hint", "no hint"]


def test_records_of_replaced_source_runs_drop_out(monkeypatch, tmp_path):
    monkeypatch.setattr(tk, "complete", fake_complete([]))
    monkeypatch.setattr(tk, "OUT", tmp_path / "takeover.jsonl")
    src = rec()
    tk.run([src], {7: "A"}, ITEMS, out_path=tk.OUT)
    tk.run([src], {7: "A"}, ITEMS, out_path=tk.OUT)                           # resumable: nothing new
    rows = tk.load(tk.OUT)
    assert len(rows) == 1
    assert len(tk.current_probes(rows, {tk.source_key(src)})) == 1
    newer = {**src, "timestamp_utc": "2026-10-23T00:00:00+00:00"}             # Step 2b replaced the source run
    assert tk.current_probes(rows, {tk.source_key(newer)}) == []
    tk.run([newer], {7: "A"}, ITEMS, out_path=tk.OUT)
    assert len(tk.load(tk.OUT)) == 2


def steps_for(rows):
    """Step 2b records behind synthetic probed runs: two correct no-hint runs for question 7."""
    hinted = [{"condition": r["condition"], "arm": r.get("arm"), "parsed_letter": r["final_letter"],
               "cue_letter": "B", "item_id": 7} for r in rows if r["kind"] != "no hint"]
    nohint = [{"condition": "none", "status": "ok", "parsed_letter": "A", "correct_letter": "A", "item_id": 7,
               "arm": None, "cue_letter": None}] * 2
    return hinted + nohint


def test_report_prints_every_rate_as_x_of_y(monkeypatch, capsys):
    monkeypatch.setattr(tk, "complete", fake_complete([]))
    rows = [tk.probe_run(rec(), {7: "A"}, ITEMS), tk.probe_run(rec(parsed="A"), {7: "A"}, ITEMS),
            tk.probe_run(rec("none", "A"), {7: "A"}, ITEMS)]
    cases = tk.report(rows, steps_for(rows), {7: "A"})
    out = capsys.readouterr().out
    assert "Lanham et al. 2023" in out and "off-distribution" in out
    assert "| tool, pasted | 1 | 0 of 1 [" in out and "1 of 1 [" in out and "| no hint | 1 |" in out
    assert "equals the run's own final letter in 1 of 3 [" in out
    assert "| tool, pasted | 2 | 1 | 1 | 0 | 1 | 1 |" in out                  # the counts behind the numbers
    assert "(1 of 1 questions)" in out and "| sure | followed | 1 |" in out
    assert [c["source_run_id"] for c in cases] == ["r-tool_pasted-B"]          # late takeover (k = 3 of 5), sure


def test_figures_draw_from_synthetic_runs(monkeypatch, tmp_path):
    from finetune.look import plot_takeover as pt
    monkeypatch.setattr(tk, "complete", fake_complete([]))
    rows = [tk.probe_run(rec(), {7: "A"}, ITEMS), tk.probe_run(rec(parsed="A"), {7: "A"}, ITEMS),
            tk.probe_run(rec("none", "A"), {7: "A"}, ITEMS), tk.probe_run(rec("user", "B"), {7: None}, ITEMS)]
    paths = pt.plot_curves(rows, tmp_path) + pt.plot_points(rows, tmp_path) + pt.plot_means(rows, tmp_path)
    names = sorted(p.name for p in paths)
    assert "takeover_points.png" in names and "takeover_mean_curves.png" in names
    assert "takeover_curves_tool-pasted_followed_1.png" in names and "takeover_curves_no-hint_no-hint_1.png" in names
    assert all(p.exists() and p.with_suffix(".svg").exists() for p in paths)


def test_the_own_answer_is_re_read_from_the_current_runs(monkeypatch):
    monkeypatch.setattr(tk, "complete", fake_complete([]))
    r = tk.probe_run(rec(), {}, ITEMS)
    assert r["own_letter"] is None
    [fresh] = tk.current_probes([r], {tk.source_key(rec())}, {7: "A"})
    assert fresh["own_letter"] == "A" and fresh["own_prob"][0] == pytest.approx(0.7)


def test_a_probe_without_log_probs_fails_its_run_and_gaps_are_not_done(monkeypatch):
    inner = fake_complete([])

    def gap(model, prompt, **kw):
        out = inner(model, prompt, **kw)
        if "first step" in prompt and "tool says" not in prompt:              # one probe comes back bare
            out["logprobs"] = []
        return out
    monkeypatch.setattr(tk, "complete", gap)
    r = tk.probe_run(rec(), {}, ITEMS)
    assert r["status"] == "api_error" and "without log-probs" in r["error_type"]
    monkeypatch.setattr(tk, "complete", fake_complete([]))
    good = tk.probe_run(rec(), {}, ITEMS)
    holed = {**good, "curve": [{**good["curve"][0], "floor": None}] + good["curve"][1:]}
    assert tk.complete_curve(good) and not tk.complete_curve(holed)
    assert tk.current_probes([holed], {tk.source_key(rec())}) == []



def test_adaptive_probes_every_5_percent_then_refines_only_where_the_leader_changes():
    tops = ["A"] * 60 + ["B"] * 41                                             # n = 100: one change at k = 60
    asked = []

    def tops_of(ks):
        asked.append(list(ks))
        return {k: tops[k] for k in ks}
    seen = tk.adaptive_ks(100, tops_of)
    assert asked[0] == [100] and asked[1] == list(range(0, 100, 5))            # the last probe first, then the grid
    assert 59 in seen and 60 in seen and len(seen) == 21 + 3                   # 55..60: probes 57, 58, 59
    assert tk.takeover_point([seen[k] for k in sorted(seen)], "B") == sorted(seen).index(60)
    flat = tk.adaptive_ks(100, lambda ks: {k: "B" for k in ks})
    assert len(flat) == 21
    hidden = ["B"] * 101
    hidden[52] = "A"                                                           # a flip between two grid points
    probed = tk.adaptive_ks(100, lambda ks: {k: hidden[k] for k in ks})
    assert 52 not in probed                                                    # refinement never looks there
    assert tk.adaptive_ks(100, lambda ks: None) is None


def test_an_adaptive_run_keeps_only_the_probes_it_sent(monkeypatch):
    calls = []
    monkeypatch.setattr(tk, "complete", fake_complete(calls))
    long_reasoning = " ".join(f"Step {i} of the working is done here." for i in range(40)) + \
        " The tool says B, so B it is." + " ".join(f" Check {i} agrees with that choice." for i in range(19))
    r = tk.probe_run(rec(reasoning=long_reasoning), {7: "A"}, ITEMS)
    dense = tk.probe_run(rec(reasoning=long_reasoning), {7: "A"}, ITEMS, probes="dense")
    assert r["params"]["probes"] == "grid_tail" and len(r["curve"]) < len(dense["curve"]) == r["n_sentences"] + 1
    assert r["takeover_k"] == dense["takeover_k"] and r["takeover_frac"] == dense["takeover_frac"]
    assert [p["k"] for p in r["curve"]] == sorted(p["k"] for p in r["curve"])
    assert calls[0] == tk.probe_texts(rec(reasoning=long_reasoning))[1][-1]   # the last probe first


def typed(kind, takeover_k=None, n=10, tops=None, last=None):
    return {"kind": kind, "takeover_k": takeover_k, "takeover_frac": None if takeover_k is None else takeover_k / n,
            "hint_last_top_frac": last, "top_letters": tops or ["A"], "hint_letter": "B", "n_sentences": n}


def test_takeover_types():
    assert tk.takeover_type(typed("followed", 0)) == "at 0"
    assert tk.takeover_type(typed("followed", 5)) == "late" and tk.takeover_type(typed("followed", 3)) == "other"
    assert tk.takeover_type(typed("resisted", tops=["B"], last=0.3)) == "at 0"
    assert tk.takeover_type(typed("resisted", tops=["B"], last=0.8)) == "late"
    assert tk.takeover_type(typed("resisted", tops=["A"], last=0.3)) == "other"
    assert tk.takeover_type(typed("resisted", tops=["A"], last=None)) == "other"


def test_the_two_baselines():
    mentions = [False] * 100
    mentions[40] = mentions[61] = True                                        # sentences 41 and 62
    r = {"n_sentences": 100, "takeover_k": 60, "mentions": mentions}
    # windows ending at 55..65, minus 58..62 (they share a sentence with the takeover window)
    js = [55, 56, 57, 63, 64, 65]
    assert tk.position_matched(r) == pytest.approx(sum(tk.mention_before(mentions, j) for j in js) / 6) == 2 / 6
    curve = [{"k": k, "probs": {"B": p}, "floor": 0.01} for k, p in ((0, 0.9), (10, 0.95), (30, 0.4), (41, 0.6),
                                                                       (60, 0.6), (90, None))]
    res = {"n_sentences": 100, "hint_letter": "B", "curve": curve, "mentions": mentions}
    assert tk.closest_approach(res) == (41, True)                             # after the first fifth; first of ties
    assert tk.closest_approach({**res, "mentions": None}) is None


def test_sure_questions_need_both_no_hint_runs_answered_and_correct():
    def nh(q, letter, status="ok"):
        return {"condition": "none", "item_id": q, "status": status, "parsed_letter": letter, "correct_letter": "A"}
    steps = [nh(1, "A"), nh(1, "A"), nh(2, "A"), nh(2, "B"), nh(3, "A"), nh(3, None), nh(4, "A")]
    assert tk.sure_questions(steps) == {1: True, 2: False, 3: False, 4: False}


def test_check_adaptive_replays_saved_dense_curves(monkeypatch):
    monkeypatch.setattr(tk, "complete", fake_complete([]))
    rows = [{**tk.probe_run(rec(run_id=f"r{i}"), {7: "A"}, ITEMS, probes="dense"), "source_run_id": f"r{i}"}
            for i in range(3)]
    checks = tk.check_adaptive(rows, n_runs=2)
    assert len(checks) == 3 and sum(c["in_sample"] for c in checks) == 2
    assert all(c["grid_same"] and c["grid_tail_same"] and c["grid_probes"] <= c["dense_probes"] for c in checks)


def test_runs_that_are_not_run_get_another_pass(monkeypatch, tmp_path):
    good = fake_complete([])
    state = {"n": 0}

    def flaky(model, prompt, **kw):
        state["n"] += 1
        return {"error": "URLError"} if state["n"] == 1 else good(model, prompt, **kw)
    monkeypatch.setattr(tk, "complete", flaky)
    out = tk.run([rec()], {7: "A"}, ITEMS, out_path=tmp_path / "t.jsonl")
    assert [r["status"] for r in out] == ["not_run", "ok"]



def test_the_tail_scan_makes_the_takeover_exact_where_the_grid_misses_a_flip():
    tops = ["A"] * 40 + ["B"] * 61                                            # n = 100: B from 40 ...
    tops[93] = "A"                                                            # ... but A again at 93
    look = lambda ks: {k: tops[k] for k in ks}                                # noqa: E731
    grid = tk.adaptive_ks(100, look)
    ks = sorted(grid)
    assert ks[tk.takeover_point([grid[k] for k in ks], "B")] == 40           # the flip at 93 goes unseen
    tail = tk.tail_scan(100, look, dict(grid), batch=1)
    ks = sorted(tail)
    assert ks[tk.takeover_point([tail[k] for k in ks], "B")] == 94           # exact
    assert set(range(93, 101)) <= set(tail) and len(tail) < 101
    chunked = tk.tail_scan(100, look, dict(grid), batch=4)                    # in requests of 4: same answer
    ks = sorted(chunked)
    assert ks[tk.takeover_point([chunked[k] for k in ks], "B")] == 94
    assert tk.schedule(100, look, "grid") == grid and len(tk.schedule(100, look, "dense")) == 101
