"""The exploratory (post hoc) trade-off analysis (tools/tradeoff.py; the log archive/sessions/2026-11-07/
2026-11-07_2020_A_tradeoff-exploratory.md, section 3), on small synthetic runs with known rates: the rates per system and
channel group; a_C and a_W on the tool channels only; the crossing p* = dW / (dW - dC) and its no-crossing cases; the
bootstrap's clipping to [0, 1] and its flipped-order count, against a slow reference loop; disclosure when following;
the no-answer-as-wrong sensitivity; the loader's one rule for all nine systems; every output says "exploratory (post
hoc)". CPU only, no network, never the real runs: files go to a temporary folder."""
import csv
import json
import struct
import sys
from pathlib import Path

import numpy as np
import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

import tradeoff as to  # noqa: E402
from common import wilson  # noqa: E402

WORDING = {"user": "user_turpin", "tool_pasted": "tool_progress", "tool_injected": "inserted_database", "none": "none"}


def run(q, system, channel, kind, parsed, rep=0, mention=False, correct="A", wrong="B", status="ok"):
    """One record with the keys the reader uses; kind is "wrong", "correct" or "none"."""
    hint = {"wrong": wrong, "correct": correct, "none": None}[kind]
    return {"run_id": f"{system}|{q}|{channel}|{kind}|{rep}", "experiment": "trackA_a39", "item_id": q,
            "system": system, "wording": WORDING[channel], "channel": channel, "hint_letter": hint,
            "hint_correct": None if hint is None else hint == correct, "correct_letter": correct,
            "parsed_letter": parsed, "status": status, "mention_final_broad": mention, "repeat": rep}


def runs(system, qs, user=(), pasted_w=(), inserted_w=(), pasted_c=(), inserted_c=(), mention=(), none=("A", "A")):
    """The same runs on every question: each tuple is the parsed letters of that channel's runs (None: no answer);
    mention: (channel, rep) pairs of wrong-hint runs whose final answer names the hint."""
    out = []
    for q in qs:
        for channel, kind, letters in (("user", "wrong", user), ("tool_pasted", "wrong", pasted_w),
                                       ("tool_injected", "wrong", inserted_w), ("tool_pasted", "correct", pasted_c),
                                       ("tool_injected", "correct", inserted_c), ("none", "none", none)):
            for rep, x in enumerate(letters):
                out.append(run(q, system, channel, kind, x, rep, mention=kind == "wrong" and (channel, rep) in mention))
    return out


QS = [f"q{i}" for i in range(6)]


# ---------------------------------------------------------------- rates
def test_rates_per_system_and_channel_group():
    rs = runs("x", QS, user=("B", "A"), pasted_w=("B", "B"), inserted_w=("A", None), pasted_c=("A", "C"),
              inserted_c=("A", None), mention=(("user", 0), ("user", 1), ("tool_pasted", 0)))
    e = to.rates(rs)
    kn = lambda x: (x["k"], x["n"])  # noqa: E731
    assert {c: kn(x) for c, x in e["following"].items()} == {"pooled": (18, 30), "user": (6, 12), "pasted": (12, 12),
                                                              "inserted": (0, 6)}
    assert {c: kn(x) for c, x in e["acceptance"].items()} == {"pooled": (12, 18), "pasted": (6, 12), "inserted": (6, 6)}
    assert e["following"]["pooled"]["wilson"] == wilson(18, 30)
    assert e["following"]["pooled"]["rate"] == pytest.approx(0.6)


def test_tool_rates_are_the_tool_channels_only_and_the_right_letter():
    # the user channel's right answers (A) never enter a_W; a third letter (C) is neither the hint nor right
    rs = runs("x", QS, user=("A", "A"), pasted_w=("B", "C"), inserted_w=("A", None), pasted_c=("A", "C"),
              inserted_c=("A", None))
    t = to.rates(rs)["tool"]
    assert (t["a_C"]["k"], t["a_C"]["n"]) == (12, 18)
    assert (t["a_W"]["k"], t["a_W"]["n"]) == (6, 18)
    assert t["a_W"]["wilson"] == wilson(6, 18)


def test_no_answer_as_wrong_keeps_unanswered_runs_in_the_denominator():
    rs = runs("x", QS, pasted_w=("B", "C"), inserted_w=("A", None), pasted_c=("A", "C"), inserted_c=("A", None))
    main, sens = to.rates(rs)["tool"], to.rates(rs)["tool_no_answer_as_wrong"]
    assert (main["a_W"]["k"], main["a_W"]["n"], main["a_C"]["k"], main["a_C"]["n"]) == (6, 18, 12, 18)
    assert (sens["a_W"]["k"], sens["a_W"]["n"], sens["a_C"]["k"], sens["a_C"]["n"]) == (6, 24, 12, 24)


def test_disclosure_when_following_is_named_among_followed_runs_only():
    # followed: user rep 0 (named), pasted reps 0 (named) and 1 (not); user rep 1 names the hint but didn't follow
    rs = runs("x", QS, user=("B", "A"), pasted_w=("B", "B"), inserted_w=("A", None),
              mention=(("user", 0), ("user", 1), ("tool_pasted", 0)))
    d = to.rates(rs)["disclosure_when_following"]
    assert (d["pooled"]["k"], d["pooled"]["n"]) == (12, 18)
    assert (d["user"]["k"], d["user"]["n"]) == (6, 6)
    assert (d["pasted"]["k"], d["pasted"]["n"]) == (6, 12)
    assert d["inserted"]["n"] == 0 and d["inserted"]["rate"] is None and d["inserted"]["wilson"] is None
    assert d["pooled"]["wilson"] == wilson(12, 18)


# ---------------------------------------------------------------- the crossing
def test_crossing_point_inside_and_its_direction():
    e = to.crossing_point(0.4, -0.4)
    assert e["p_star"] == pytest.approx(0.5) and e["status"] == to.CROSSES and e["ahead"] == "below"
    e = to.crossing_point(-0.1, 0.3)
    assert e["p_star"] == pytest.approx(0.25) and e["status"] == to.CROSSES and e["ahead"] == "above"


@pytest.mark.parametrize("dw, dc, status", [(0.1, 0.2, to.AHEAD), (0.2, 0.0, to.AHEAD), (-0.1, -0.3, to.BEHIND),
                                            (0.0, -0.2, to.BEHIND), (0.0, 0.0, to.EQUAL)])
def test_no_crossing_when_the_signs_agree(dw, dc, status):
    e = to.crossing_point(dw, dc)
    assert e["status"] == status and e["p_star"] is None


def test_resampled_crossings_are_clipped_and_flips_counted():
    dw = np.array([0.2, 0.3, 0.1, -0.1, 0.1, -0.3])
    dc = np.array([-0.2, 0.1, 0.3, 0.2, 0.1, 0.0])
    # denominators dW - dC: 0.4, 0.2, -0.2, -0.3, 0, -0.3; the full data's sign +
    e = to.clip_crossings(dw, dc, 1)
    assert e["flipped"] == 3 and e["zero"] == 1
    assert sorted(e["values"].tolist()) == pytest.approx([0.5, 1.0])          # 0.3 / 0.2 = 1.5, clipped to 1
    assert (e["clipped_to_0"], e["clipped_to_1"]) == (0, 1)
    e = to.clip_crossings(dw, dc, -1)
    # kept: denominators -0.2 (p = 0.1 / -0.2 = -0.5, clipped to 0), -0.3 (p = -0.1 / -0.3 = 1/3), -0.3 (p = 1)
    assert e["flipped"] == 2 and e["zero"] == 1
    assert sorted(e["values"].tolist()) == pytest.approx([0.0, 1 / 3, 1.0])


def test_clip_values_by_hand():
    # at 0 or 1: a raw p* at or beyond the end (one system ahead throughout, or level at that end)
    e = to.clip_crossings(np.array([0.1, -0.1, -0.3]), np.array([0.3, 0.2, 0.0]), -1)
    assert sorted(e["values"].tolist()) == pytest.approx([0.0, 1 / 3, 1.0])
    assert (e["clipped_to_0"], e["clipped_to_1"], e["flipped"]) == (1, 1, 0)


def test_percentile_rule_is_boot_diffs():
    vals = np.arange(1000, dtype=float)
    assert to.pct(vals) == [25.0, 974.0]        # sorted[int(0.025 n)], sorted[int(0.975 n) - 1], as common.boot_diff


def homogeneous():
    """A: a_C 0.5, a_W 0.75; B: a_C 1, a_W 0.25, on every question alike (so every resample is the full data)."""
    a = runs("a", QS, pasted_w=("A", "A"), inserted_w=("A", "B"), pasted_c=("A", "C"), inserted_c=("A", "C"))
    b = runs("b", QS, pasted_w=("A", "B"), inserted_w=("B", "B"), pasted_c=("A", "A"), inserted_c=("A", "A"))
    return a, b


def test_crossing_on_runs_with_its_pointwise_differences():
    a, b = homogeneous()
    e = to.crossing(a, b)
    assert (e["a"]["a_C"], e["a"]["a_W"], e["b"]["a_C"], e["b"]["a_W"]) == pytest.approx((0.5, 0.75, 1.0, 0.25))
    assert (e["dW"], e["dC"]) == pytest.approx((0.5, -0.5))
    assert e["p_star"] == pytest.approx(0.5) and e["status"] == to.CROSSES and e["ahead"] == "below"
    assert e["interval"] == pytest.approx([0.5, 0.5]) and e["flipped"] == 0 and e["resamples"] == to.N_BOOT
    assert e["questions"] == 6
    for p, want in ((0, 0.5), (0.25, 0.25), (0.5, 0.0), (0.75, -0.25), (0.9, -0.4), (1, -0.5)):
        x = e["pointwise"][str(p)]
        assert x["diff"] == pytest.approx(want) and x["interval"] == pytest.approx([want, want])


def test_identical_systems_never_cross():
    a, _ = homogeneous()
    e = to.crossing(a, [{**r, "system": "b"} for r in a])
    assert e["status"] == to.EQUAL and e["p_star"] is None
    assert all(x["diff"] == 0 and x["interval"] == [0, 0] for x in e["pointwise"].values())


def mixed():
    """Questions that differ, so resamples differ (and some flip)."""
    a, b = [], []
    pats = [(("A", "A"), ("A", "B"), ("A", "C"), ("A", "C")), (("B", "B"), ("A", "A"), ("A", "A"), ("C", "A")),
            (("A", None), ("B", "A"), ("C", "C"), ("A", "C")), (("A", "A"), ("A", "A"), ("A", "A"), ("A", "A")),
            (("B", "B"), ("B", "B"), ("A", "A"), ("A", None)), (("A", "B"), ("A", "C"), (None, "A"), ("A", "A")),
            (("B", "A"), ("A", "A"), ("A", "C"), ("C", "C")), (("A", "A"), ("B", None), ("A", "A"), ("A", "C"))]
    for i, (pw, iw, pc, ic) in enumerate(pats):
        q = f"q{i}"
        a += runs("a", [q], pasted_w=pw, inserted_w=iw, pasted_c=pc, inserted_c=ic)
        j = (i + 3) % len(pats)
        b += runs("b", [q], pasted_w=pats[j][2][::-1], inserted_w=pats[j][1], pasted_c=pats[j][0][::-1],
                  inserted_c=("A", "A") if i % 2 else ("B", "A"))
    return a, b


def reference(a, b, n, no_answer_as_wrong=False):
    """A slow loop over the same resample counts: each resample's ratio-of-sums rates, dW, dC, the crossing."""
    qs = sorted({r["item_id"] for r in a} | {r["item_id"] for r in b})
    counts = to.resample_counts(len(qs), n=n)

    def keep(rs, hint_correct):
        return [r for r in rs if r["hint_correct"] is hint_correct and r["channel"] in to.TOOL
                and (no_answer_as_wrong or r["parsed_letter"])]

    def rate(rs, w):
        num = sum(w[qs.index(r["item_id"])] * (r["parsed_letter"] == r["correct_letter"]) for r in rs)
        den = sum(w[qs.index(r["item_id"])] for r in rs)
        return num / den

    out = []
    for w in counts:
        dw = rate(keep(a, False), w) - rate(keep(b, False), w)
        dc = rate(keep(a, True), w) - rate(keep(b, True), w)
        out.append((dw, dc))
    return np.array(out)


@pytest.mark.parametrize("no_answer_as_wrong", [False, True])
def test_vectorized_bootstrap_matches_a_slow_loop(no_answer_as_wrong):
    a, b = mixed()
    n = 400
    ref = reference(a, b, n, no_answer_as_wrong)
    e = to.crossing(a, b, no_answer_as_wrong=no_answer_as_wrong, n=n)
    sign = np.sign(e["dW"] - e["dC"])
    want = to.clip_crossings(ref[:, 0], ref[:, 1], sign)
    assert e["flipped"] == want["flipped"] and e["zero"] == want["zero"]
    assert e["interval"] == pytest.approx(to.pct(want["values"]))
    d = ref[:, 0] + 0.9 * (ref[:, 1] - ref[:, 0])
    assert e["pointwise"]["0.9"]["interval"] == pytest.approx(to.pct(d))


def test_bootstrap_is_seeded_and_paired():
    a, b = mixed()
    assert to.crossing(a, b, n=300) == to.crossing(a, b, n=300)
    c1, c2 = to.resample_counts(8, n=50), to.resample_counts(8, n=50)
    assert (c1 == c2).all() and (c1.sum(axis=1) == 8).all()


def test_sensitivity_counts_no_answer_as_wrong():
    a, b = homogeneous()
    a = [{**r, "parsed_letter": None} if r["channel"] == "tool_pasted" and r["repeat"] == 1 else r for r in a]
    e = to.crossing(a, b, no_answer_as_wrong=True)
    # a's pasted rep 1: correct-hint was C (wrong) and wrong-hint was A (right), now both no answer, counted wrong
    assert (e["a"]["a_C"], e["a"]["a_W"]) == pytest.approx((0.5, 0.5))
    e = to.crossing(a, b)
    assert (e["a"]["a_C"], e["a"]["a_W"]) == pytest.approx((2 / 3, 2 / 3))


# ---------------------------------------------------------------- disclosure when following, against prompt_only
def test_disclosure_difference_drops_resamples_with_no_followed_run():
    qs = [f"q{i}" for i in range(5)]
    a = runs("a", qs[:1], user=("B", "B"), mention=(("user", 0),)) + runs("a", qs[1:], user=("A", "A"))
    b = runs("b", qs, user=("B", "A"), mention=(("user", 0),))
    e = to.disclosure_diff(a, b)
    counts = to.resample_counts(5)
    assert e["dropped"] == int((counts[:, 0] == 0).sum()) > 0
    assert e["diff"] == pytest.approx(0.5 - 1.0)
    assert (e["a"]["k"], e["a"]["n"], e["b"]["k"], e["b"]["n"]) == (1, 2, 5, 5)
    assert e["resamples"] == to.N_BOOT - e["dropped"]


# ---------------------------------------------------------------- the whole analysis, the loader and the outputs
def nine(qs=QS):
    """Nine systems on synthetic runs (a wrapper's non-tool runs its partner's, marked shared_from)."""
    pat = {"base": ("B", "B", "B", "A", "A", "A"), "prompt_only": ("B", "A", "B", "A", "A", "A"),
           "lora": ("B", "A", "A", "B", "A", "C"), "lora_note": ("A", "B", "A", "A", "A", "C"),
           "wrap": ("B", "B", "A", "A", "A", "A"), "wrap_note": ("B", "A", "A", "A", "C", "A"),
           "lora_wrap": ("B", "A", "A", "A", "A", "C"), "a40": ("A", "A", "A", "A", "C", "C"),
           "a40_note": ("A", "A", "A", "C", "C", "C")}
    by = {}
    for s, (u, pw, iw, pc, ic, x) in pat.items():
        by[s] = runs(s, qs, user=(u, "A"), pasted_w=(pw, "A"), inserted_w=(iw, "B"), pasted_c=(pc, "A"),
                     inserted_c=(ic, x), mention=(("user", 0), ("tool_injected", 1)))
    for s, partner in (("wrap", "base"), ("wrap_note", "prompt_only"), ("lora_wrap", "lora")):
        by[s] = [r for r in by[s] if r["channel"] == "tool_injected"] + [
            {**r, "system": s, "shared_from": partner} for r in by[partner] if r["channel"] != "tool_injected"]
    return by


def test_analyse_says_exploratory_and_orders_the_pairs():
    res = to.analyse(nine(), "e2")
    assert to.LABEL == "exploratory (post hoc)" and res["label"] == to.LABEL
    assert list(res["systems"]) == list(to.SYSTEMS)
    for block in ("answered", "no_answer_as_wrong"):
        assert list(res["crossings"][block])[:2] == ["a40", "lora"]
        assert set(res["crossings"][block]) == set(to.SYSTEMS) - {"prompt_only"}
    assert list(res["disclosure_vs_prompt_only"])[:2] == ["lora", "a40"]
    for s in ("wrap", "wrap_note", "lora_wrap"):
        assert "diluted by design" in res["systems"][s]["note"]
    assert to.LABEL in to.text(res)
    json.dumps(res)                                                       # numbers, ids and words only


def write_runs(folder, name, rows):
    with open(folder / f"eval_{name}_a39_e2_runs.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_load_takes_every_system_by_one_rule_and_report_writes_the_json(tmp_path):
    from finetune import eval as ev
    qs = [q["item_id"] for q in ev.questions("e2")[:6]]
    by = nine(qs)
    for s, rs in by.items():
        write_runs(tmp_path, s, [r for r in rs if "shared_from" not in r])
    # a failed record for an A40 run in a file that sorts later never hides its ok record; a question outside E2 is out
    late = {**by["a40"][0], "status": "api_error", "parsed_letter": None}
    write_runs(tmp_path, "zz_late", [late, {**by["base"][0], "item_id": "not-e2", "run_id": "x"}])
    got, comp = to.load(tmp_path, "e2")
    assert set(got) == set(to.SYSTEMS)
    assert len(got["a40"]) == len(by["a40"]) and by["a40"][0] in got["a40"]
    assert sum("shared_from" in r for r in got["wrap"]) == len([r for r in by["base"] if r["channel"] != "tool_injected"])
    assert all(r["item_id"] != "not-e2" for rs in got.values() for r in rs)
    res = to.report(tmp_path, "e2")
    saved = json.loads((tmp_path / "tradeoff_e2.json").read_text())
    assert saved["label"] == to.LABEL and saved["questions"] == 6 and "completeness" in saved


def test_every_string_in_the_report_fits_the_exports_200_character_limit(tmp_path):
    """tools/export_summaries.py refuses a summary with any string over 200 characters (Nov 7: it refused
    tradeoff_e2.json for its one-line bootstrap description)."""
    from finetune import eval as ev
    qs = [q["item_id"] for q in ev.questions("e2")[:6]]
    for s, rs in nine(qs).items():
        write_runs(tmp_path, s, [r for r in rs if "shared_from" not in r])
    to.report(tmp_path, "e2")

    def strings(x):
        if isinstance(x, dict):
            for k, v in x.items():
                yield k
                yield from strings(v)
        elif isinstance(x, list):
            for v in x:
                yield from strings(v)
        elif isinstance(x, str):
            yield x
    long = [t for t in strings(json.loads((tmp_path / "tradeoff_e2.json").read_text())) if len(t) > 200]
    assert long == []


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def test_figures_write_png_svg_and_a_labelled_csv(tmp_path):
    pytest.importorskip("matplotlib")
    res = to.analyse(nine(), "e2")
    for paths in (to.fig_tradeoff(res, tmp_path), to.fig_acc_p(res, tmp_path)):
        png, svg, csv_path = paths
        assert png_size(png) == (2000, 1125)
        assert to.LABEL in svg.read_text()
        lines = csv_path.read_text().splitlines()
        assert lines[0].startswith("# ") and to.LABEL in lines[0]
        rows = list(csv.DictReader(lines[1:]))
        assert rows
    rows = list(csv.DictReader(Path(tmp_path, "tradeoff_e2.csv").read_text().splitlines()[1:]))
    assert sorted({(r["panel"], r["system"]) for r in rows}) == sorted((p, s) for p in ("a", "b") for s in to.SYSTEMS)
    acc = list(csv.DictReader(Path(tmp_path, "tradeoff_acc_p.csv").read_text().splitlines()[1:]))
    assert {r["system"] for r in acc if r["kind"] == "line"} == set(to.ACC_P_SYSTEMS)
    assert {r["system"] for r in acc if r["kind"] == "crossing"} == {"a40", "lora"}


def test_acc_p_figure_says_so_when_a_pair_does_not_cross(tmp_path):
    pytest.importorskip("matplotlib")
    by = nine()
    by["a40"] = [{**r, "system": "a40"} for r in by["prompt_only"]]   # a40 equal to the instruction: no crossing
    res = to.analyse(by, "e2")
    assert res["crossings"]["answered"]["a40"]["status"] == to.EQUAL
    _, svg, _ = to.fig_acc_p(res, tmp_path)
    assert "no crossing" in svg.read_text()
