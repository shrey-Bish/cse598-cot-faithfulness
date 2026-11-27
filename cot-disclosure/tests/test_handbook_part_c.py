"""The handbook's Part C (Nov 26, descriptive, post-freeze): its numbers-only summary checked, and recomputed from the
saved records where they are (they're gitignored)."""
import json
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))
sys.path.insert(0, str(CODE / "tools"))

import handbook_part_c as P  # noqa: E402
from common import wilson  # noqa: E402

pytestmark = pytest.mark.skipif(not P.OUT_JSON.exists(), reason="Part C isn't built yet")
NUMBERS = (ROOT / "docs/presentation/pack/02_NUMBERS.md").read_text()


def res():
    return json.loads(P.OUT_JSON.read_text())


def records(o):
    if isinstance(o, dict):
        if {"k", "n", "wilson"} <= set(o):
            yield o
        else:
            for v in o.values():
                yield from records(v)


def test_every_record_is_its_k_of_n_with_its_wilson():
    rs = list(records(res()))
    assert len(rs) > 50
    for r in rs:
        assert r["text"] == f"{r['k']} of {r['n']}" and r["wilson"] == wilson(r["k"], r["n"])


def test_the_totals_are_the_frozen_ones():
    """Each system's pooled totals on the 120 are FINDINGS' (F41's table); L6's disclosure is F45's; L4's fine-tuned
    candidates that say the hint shaped the answer are F28's 97 of 147."""
    b = res()["by_subject"]["systems"]
    want = {("base", "following"): "297 of 703", ("a40", "following"): "84 of 694", ("prompt_only", "following"): "237 of 713",
            ("lora", "following"): "248 of 705", ("base", "acceptance"): "439 of 476", ("a40", "acceptance"): "347 of 459",
            ("prompt_only", "acceptance"): "431 of 476", ("lora", "acceptance"): "421 of 477"}
    for (s, m), text in want.items():
        assert b[s][m]["all"]["text"] == text
        assert sum(b[s][m][x]["k"] for x in b[s][m] if x != "all") == b[s][m]["all"]["k"]
    l6 = res()["taxonomy"]["sets"]["L6"]["by_group"]
    assert l6["lora"]["says_changed"]["k"] + l6["lora"]["mentions_only"]["k"] == 37
    assert l6["prompt_only"]["says_changed"]["k"] + l6["prompt_only"]["mentions_only"]["k"] == 18
    assert res()["taxonomy"]["sets"]["L4 part 1"]["by_group"]["lora, keyword candidate"]["says_changed"]["text"] == "97 of 147"


def test_every_glance_headline_is_in_the_numbers_file():
    for g in res()["glance"]:
        for kn in re.findall(r"\d+ of \d+", g["headline"]):
            assert kn in NUMBERS, (g["finding"], kn)
        for rid in g["numbers_rows"].split(", "):
            assert f"| {rid} |" in NUMBERS, rid


@pytest.mark.skipif(not (P.A39_OUT.exists() and P.L6_LABELS.exists() and P.L4_LABELS.exists()),
                    reason="the saved records are gitignored")
def test_recomputed_from_the_saved_records():
    r = res()
    assert P.by_subject() == r["by_subject"]
    assert json.loads(json.dumps(P.taxonomy())) == r["taxonomy"]
