"""Track A, before Step 4 (finetune/look/before_takeover.py): CPU only, no network."""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

pytest.importorskip("transformers")

from finetune.look import before_takeover as bt  # noqa: E402


@pytest.mark.parametrize("sentence, family", [
    ("My result doesn't match any option.", "doesn't match / fit"),
    ("The calculation does not fit option C either.", "doesn't match / fit"),
    ("Still not matching exactly.", "not matching / no match"),
    ("But none of the options say that.", "none of the options"),
    ("This is not among the options.", "not among / not listed"),
    ("4.62 is not listed.", "not among / not listed"),
    ("The closest is G.", "closest / nearest"),
])
def test_misfit_families(sentence, family):
    assert bt.FAMILY_RX[family].search(sentence) and bt.MISFIT.search(sentence)


def test_ordinary_reasoning_is_not_a_misfit():
    for s in ("The tool says B. Let me check the swaps.", "So the answer matches option C.", "None of this matters."):
        assert not bt.MISFIT.search(s)


def test_the_window_is_the_point_and_the_3_sentences_before():
    text = "One sentence here.\nTwo sentence here.\nThree sentence here.\nFour sentence here.\nFive."
    ends = [19, 38, 59, 79, len(text)]
    sents = bt.sentences(text, ends)
    assert [i for i, _ in bt.window(sents, 5)] == [2, 3, 4, 5] and [i for i, _ in bt.window(sents, 2)] == [1, 2]


def test_own_answer_just_before_the_point():
    r = {"own_letter": "C", "curve": [{"k": 3, "probs": {"B": 0.3, "C": 0.6}, "floor": 0.01},
                                      {"k": 4, "probs": {"B": 0.9, "C": None}, "floor": 0.002}]}
    assert bt.own_before(r, 4) == (0.6, True)
    assert bt.own_before(r, 5) == (0.002, False)                       # outside the top 10: its floor
    assert bt.own_before(r, 9) is None and bt.own_before({**r, "own_letter": None}, 4) is None


def test_onsets_after_the_first_fifth_are_permanent_or_temporary():
    tops = list("AAAABBAAABBBAABBBB")                                     # n = 17 sentences, k = 0..17
    r = {"n_sentences": 17, "hint_letter": "B", "top_letters": tops,
         "curve": [{"k": k, "probs": {}, "floor": 0.0} for k in range(18)]}
    assert bt.onsets(r) == [(4, False), (9, False), (14, True)]           # k = 4 > 0.2 * 17
    r["n_sentences"] = 30                                                 # the first fifth now covers k <= 6
    assert bt.onsets(r) == [(9, False), (14, True)]
