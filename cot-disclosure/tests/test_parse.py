"""Parser behaviour, including the ten-option (A to J) extension for MMLU-Pro."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parse import parse_answer  # noqa: E402


def test_seven_options_unchanged():
    assert parse_answer("so the answer follows.\nAnswer: (C)", 7) == ("C", "answer_colon")
    assert parse_answer("Final: \\boxed{E}", 7) == ("E", "boxed")
    assert parse_answer("Answer: (H)", 7) == (None, "none")  # H is not an option


def test_j_accepted_with_ten_options():
    assert parse_answer("Answer: (J)", 10) == ("J", "answer_colon")
    assert parse_answer("\\boxed{J}", 10) == ("J", "boxed")
    assert parse_answer("The answer is J.", 10) == ("J", "answer_is")
    assert parse_answer("so I pick **(J)**", 10) == ("J", "bold")
    assert parse_answer("... which matches option (J)", 10) == ("J", "tail_paren")


def test_j_rejected_when_not_an_option():
    assert parse_answer("Answer: (J)", 9) == (None, "none")
    assert parse_answer("Answer: (J)", 7) == (None, "none")


def test_strictness_kept_for_j():
    # a word starting with J after "answer:" is not a letter
    assert parse_answer("Answer: Just think about it.", 10) == (None, "none")
    # two different trailing parenthesised letters stay ambiguous
    assert parse_answer("either (I) or (J)", 10) == (None, "none")
    # the last explicit answer wins
    assert parse_answer("Answer: (B)\n... on reflection\nAnswer: (J)", 10) == ("J", "answer_colon")


def test_parse_final_reads_reviewer_verdict():
    from parse import parse_final
    assert parse_final("The proposed answer is wrong.\nFINAL: D", 7) == ("D", "final")
    assert parse_final("Correct.\n\nFINAL: (B)", 7) == ("B", "final")
    assert parse_final("**FINAL: C**", 7) == ("C", "final")
    # the last FINAL line wins
    assert parse_final("FINAL: A\nWait, re-checking.\nFINAL: E", 7) == ("E", "final")
    # not an option letter
    assert parse_final("FINAL: H", 7) == (None, "none")
    # no FINAL line: falls back to the general parser, and says so
    assert parse_final("So the answer is (F).", 7) == ("F", "fallback:answer_is")
    assert parse_final("FINAL: J", 10) == ("J", "final")
