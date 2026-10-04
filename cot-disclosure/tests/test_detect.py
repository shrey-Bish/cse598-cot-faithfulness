"""Keyword pre-sort for cue mentions, including the simulated tool block keywords."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from detect import detect  # noqa: E402


def test_user_cue_unchanged():
    assert detect("The user thinks it is (B).")["cue"]
    assert not detect("Alice swaps with Bob.")["cue"]


def test_tool_cue_keywords():
    for text in ("The lookup_answer_key tool says D.",
                 "According to the answer key the expected answer is D.",
                 "The study guide claims D.",
                 "There is a tool result here."):
        assert detect(text)["cue_tool"], text
    assert not detect("Alice swaps with Bob.")["cue_tool"]
    # existing keys still present
    assert set(detect("x")) >= {"cue", "uncertainty", "self_correction", "ack_influence", "cue_tool"}
