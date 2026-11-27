"""demo_min's pure parts (no local data needed), and its built page when the local data is present."""
import pathlib, sys
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tools/demo_min"))
import build as B


def test_quote_in_exact_and_cuts():
    t = "Alpha beta. Gamma delta epsilon, zeta."
    assert B.quote_in("Gamma delta epsilon, zeta.", t)
    assert B.quote_in("Alpha … epsilon, zeta.", t)
    assert not B.quote_in("beta … Alpha", t)             # out of order
    assert not B.quote_in("Gamma  delta", t)             # not byte for byte


def test_find_codes():
    for bad in ("mmlupro-11784", "a40", "results/x", "E2", "run.jsonl", "Gate 3", "Test 4"):
        assert B.find_codes("see " + bad + " here"), bad
    assert not B.find_codes("Tool returned: (G). Correct answer: (I). Olmo 3 7B Think, consistency-trained.")


def test_sentence_at():
    t = "One two. Three expected four. Five."
    s, e = B.sentence_at(t, t.index("expected"))
    assert t[s:e] == "Three expected four."


def test_built_page_if_present():
    p = B.OUT / "index.html"
    if not p.exists():
        pytest.skip("local page not built")
    import json
    f = json.loads((B.OUT / "facts.json").read_text())
    assert B.quote_in(f["quote"], f["base_reasoning"]) and len(f["quote"].split()) <= 26
    assert not B.find_codes(p.read_text().split("<script>")[0].split("</style>")[1])


def test_stem_ok_allows_only_the_restored_spaces():
    o = "Find abcdefgh matrices (a)"
    assert B.stem_ok("Find a bc def gh matrices …", o) is False      # three added
    assert B.stem_ok("Find abc defg h matrices …", o) is True        # two added
    assert B.stem_ok("Find abc defg h matrix …", o) is False         # a letter changed
    assert B.stem_ok("Find abcdefgh matrices …", o) is False         # none added
