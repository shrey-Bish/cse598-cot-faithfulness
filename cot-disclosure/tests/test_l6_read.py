"""L6's reading (tools/l6_read.py), by its rule fixed in advance (archive/sessions/2026-11-07/2026-11-07_2025_A_l6-prereg.md,
section 5, as amended in section 9): the share "discloses, in labels" (says_changed or mentions_only) per system with a
Wilson interval, every row in its system's denominator; lora minus prompt_only by a bootstrap clustered by question
(the questions behind the sheet's rows, 20,000 resamples, seed 0, a ratio of sums, a resample with an empty side
counted and left out, fewer than 5 questions on a side "too few questions"); the three readings; and the items beside
it. Synthetic sheets only: no real label, no model text."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

import l6_read as lr  # noqa: E402
from common import wilson  # noqa: E402

SHEET_COLS = ["row", "channel", "hint_letter", "final_answer", "label_final", "guess_trained", "note"]
KEY_COLS = ["row", "run_id", "system", "channel", "item_id", "timestamp_utc", "mention_final_broad", "seed"]
CHANNELS = ("user", "pasted", "inserted")


def world(tmp_path, lora_labels, po_labels, *, lora_q=None, po_q=None, guesses=None, kw=None, opus=None):
    """A sheet, its key and J-opus's labels: lora's rows first, then prompt_only's, channels in turn; each row's
    question from lora_q / po_q (default: a question of its own)."""
    rows, keys = [], []
    systems = [("lora", lab, (lora_q or [f"lq{i}" for i in range(len(lora_labels))])[i])
               for i, lab in enumerate(lora_labels)]
    systems += [("prompt_only", lab, (po_q or [f"pq{i}" for i in range(len(po_labels))])[i])
                for i, lab in enumerate(po_labels)]
    for n, (system, lab, q) in enumerate(systems, 1):
        ch = CHANNELS[(n - 1) % 3]
        g = guesses[n - 1] if guesses else ""
        rows.append({"row": n, "channel": ch, "hint_letter": "C", "final_answer": f"secret-model-text-{n}",
                     "label_final": lab, "guess_trained": g, "note": "secret-ritik-note"})
        keys.append({"row": n, "run_id": f"r{n:03d}", "system": system, "channel": ch, "item_id": q,
                     "timestamp_utc": "2026-11-04T00:00:00+00:00",
                     "mention_final_broad": str(kw[n - 1] if kw else lab in lr.DISCLOSES), "seed": "L6-20261107"})
    sheet = tmp_path / "L6_RA_test.csv"
    for path, cols, data in ((sheet, SHEET_COLS, rows), (tmp_path / "key_L6.csv", KEY_COLS, keys)):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(data)
    ol = {str(n): {"final": (opus[n - 1] if opus else r["label_final"])} for n, r in enumerate(rows, 1)}
    (tmp_path / "L6_labels.json").write_text(json.dumps(ol))
    return {"sheet": sheet, "key": tmp_path / "key_L6.csv", "opus": tmp_path / "L6_labels.json",
            "sha256": hashlib.sha256(sheet.read_bytes()).hexdigest()}


def read(w, **kw):
    return lr.reading(w["sheet"], w["key"], w["opus"], frozen_sha256=w["sha256"], **kw)


def test_the_share_counts_every_row_unclear_included_with_a_wilson_interval(tmp_path):
    lora = ["says_changed"] * 20 + ["mentions_only"] * 10 + ["unclear"] * 6 + ["no_mention"] * 6
    po = ["says_changed"] * 10 + ["no_mention"] * 26 + ["rejects_hint"] * 2 + ["unclear"] * 4
    rep = read(world(tmp_path, lora, po))
    assert rep["discloses"]["lora"]["k"] == 30 and rep["discloses"]["lora"]["n"] == 42
    assert rep["discloses"]["prompt_only"]["k"] == 10 and rep["discloses"]["prompt_only"]["n"] == 42
    assert rep["discloses"]["lora"]["wilson"] == pytest.approx(wilson(30, 42))
    assert rep["says_changed"]["lora"]["k"] == 20 and rep["rejects_hint"]["prompt_only"]["k"] == 2


def test_the_three_readings(tmp_path):
    more = read(world(tmp_path, ["says_changed"] * 42, ["no_mention"] * 42))
    assert more["comparison"]["reading"] == "discloses more than the instruction, in labels"
    assert more["comparison"]["diff"] == pytest.approx(1.0) and more["comparison"]["interval"][0] > 0
    less = read(world(tmp_path, ["no_mention"] * 42, ["mentions_only"] * 42))
    assert less["comparison"]["reading"] == "discloses less than the instruction, in labels"
    mixed = ["says_changed", "no_mention"] * 21
    same = read(world(tmp_path, mixed, mixed))
    assert same["comparison"]["reading"] == "no difference detected in labels"
    assert same["comparison"]["interval"][0] < 0 < same["comparison"]["interval"][1]


def test_the_bootstrap_resamples_the_union_of_questions_by_the_rule_and_is_seeded(tmp_path):
    lora = ["says_changed", "no_mention"] * 21
    po = ["no_mention"] * 30 + ["says_changed"] * 12
    shared = [f"q{i}" for i in range(42)]                      # both systems drew on the same 42 questions
    w = world(tmp_path, lora, po, lora_q=shared, po_q=shared[::-1])
    a, b = read(w)["comparison"], read(w)["comparison"]
    assert a == b and a["resamples"] == 20000 and a["seed"] == 0 and a["questions"] == 42 and a["left_out"] == 0
    # the rule, written out: Python's random.Random(0), one choice per question of the sorted union, 20,000 times
    by_q = {}
    for sys_, labs, qs in (("lora", lora, shared), ("prompt_only", po, shared[::-1])):
        for lab, q in zip(labs, qs):
            by_q.setdefault(q, {"lora": [], "prompt_only": []})[sys_].append(lab in lr.DISCLOSES)
    import random
    rng, qs, vals = random.Random(0), sorted(by_q, key=str), []
    for _ in range(20000):
        s = [rng.choice(qs) for _ in qs]
        x = [v for q in s for v in by_q[q]["lora"]]
        y = [v for q in s for v in by_q[q]["prompt_only"]]
        vals.append(sum(x) / len(x) - sum(y) / len(y))
    vals.sort()
    assert a["interval"] == pytest.approx([vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]])


def test_a_resample_with_an_empty_side_is_counted_and_left_out_and_few_questions_say_so(tmp_path):
    lora = ["says_changed"] * 6
    po = ["no_mention"] * 6
    w = world(tmp_path, lora, po, lora_q=["a"] * 6, po_q=["b", "b", "b", "c", "c", "c"])   # 1 and 2 questions a side
    c = read(w)["comparison"]
    assert c["reading"] == "too few questions" and c["interval"] is None
    assert c["questions_a_side"] == {"lora": 1, "prompt_only": 2}
    w = world(tmp_path, ["says_changed"] * 6, ["no_mention"] * 6, lora_q=list("abcdef"), po_q=list("ghijkl"))
    c = read(w)["comparison"]
    assert c["left_out"] > 0 and c["left_out"] + c["kept"] == 20000      # a side with no row: counted, left out


def test_the_items_beside_the_reading(tmp_path):
    lora = ["says_changed"] * 21 + ["mentions_only"] * 21
    po = ["no_mention"] * 42
    kw = [True] * 21 + [False] * 21 + [False] * 40 + [True] * 2        # the keyword against "discloses, in labels"
    guesses = ["yes"] * 30 + ["no"] * 6 + [""] * 6 + ["yes"] * 4 + ["no"] * 30 + [""] * 8
    opus = (["says_changed"] * 21 + ["mentions_only"] * 21) + (["no_mention"] * 41 + [None])
    rep = read(world(tmp_path, lora, po, kw=kw, guesses=guesses, opus=opus))
    assert rep["keyword_agrees"]["lora"] == {"k": 21, "n": 42} and rep["keyword_agrees"]["prompt_only"] == {"k": 40, "n": 42}
    assert {ch: rep["by_channel"]["lora"][ch]["n"] for ch in CHANNELS} == {"user": 14, "pasted": 14, "inserted": 14}
    assert rep["guess_trained"]["lora"] == {"yes": 30, "no": 6, "blank": 6, "n": 42}
    assert rep["guess_trained"]["prompt_only"] == {"yes": 4, "no": 30, "blank": 8, "n": 42}
    k = rep["kappa"]
    assert k["overall"]["kappa"] == pytest.approx(1.0) and k["overall"]["rows"] == 83 and k["no_label"] == 1
    assert k["note"] is None


def test_low_agreement_with_the_check_is_noted_under_0_6(tmp_path):
    lora = ["says_changed"] * 42
    po = ["no_mention"] * 42
    opus = ["no_mention"] * 42 + ["says_changed"] * 42
    rep = read(world(tmp_path, lora, po, opus=opus))
    assert rep["kappa"]["overall"]["kappa"] < 0.6
    assert rep["kappa"]["note"] == "low agreement with the reliability check"


def test_a_sheet_that_is_not_the_frozen_one_is_refused(tmp_path):
    w = world(tmp_path, ["says_changed"] * 42, ["no_mention"] * 42)
    with pytest.raises(SystemExit, match="frozen"):
        lr.reading(w["sheet"], w["key"], w["opus"], frozen_sha256="0" * 64)


def test_the_report_holds_numbers_only(tmp_path):
    rep = read(world(tmp_path, ["says_changed"] * 42, ["no_mention"] * 42))
    text = json.dumps(rep)
    assert "secret-model-text" not in text and "secret-ritik-note" not in text and "r001" not in text

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
    assert all(len(s) <= 200 for s in strings(rep))           # export_summaries' limit
