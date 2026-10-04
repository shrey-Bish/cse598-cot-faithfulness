"""Phase 3c (optional): does private reasoning leak into the visible answer at the token cap?

  python progress/truncation_sweep.py

olmo3-7b-think, pilot puzzles 0 to 7, no hint, seed 0, pilot temperature:
  - streamed, caps 2,000 and 4,000 tokens (16 calls, as planned);
  - non-streamed, cap 2,000 (8 calls, added): the earlier ladder run, where 10/10 capped
    replies leaked, appears to predate the switch to streaming, while the 5 capped
    replies in the streamed progress round did not leak. This arm tests that difference.
Measures per capped reply: is the private field empty and the visible field full of
reasoning (a leak), and does the repo parser pull a letter out of the leaked text.
"""
from concurrent.futures import ThreadPoolExecutor

from common import OUT, append, call, done_ids, get_logger, run_id

import experiments as pilot  # noqa: E402

MODEL = "olmo3-7b-think"
PUZZLES = range(8)
ARMS = [("stream_2000", 2000, True), ("stream_4000", 4000, True), ("nostream_2000", 2000, False)]
FILE = OUT / "truncation_sweep.jsonl"
log = get_logger("trunc")


def one(job):
    idx, arm, cap, stream = job
    prompt, _ = pilot.build_prompt(idx, "none", 0, pilot.STEPS)
    item = pilot.ITEMS[idx]
    rec = call(log, experiment="truncation", item_id=idx, model=MODEL, condition=arm, repeat=0,
               messages=[{"role": "user", "content": prompt}], n_options=len(item["options"]),
               correct_letter=item["correct"], seed=0, max_tokens=cap, stream=stream)
    capped = rec["finish_reason"] == "length"
    rec.update({"cap": cap, "capped": capped,
                "leak": capped and not rec["reasoning_text"] and len(rec["final_text"]) > 0,
                "letter_from_capped_visible_text": rec["parsed_letter"] if capped else None})
    return rec


def main():
    finished = done_ids(FILE)
    jobs = [(i, arm, cap, stream) for arm, cap, stream in ARMS for i in PUZZLES
            if run_id("truncation", i, MODEL, arm, None, 0) not in finished]
    log.info(f"truncation sweep: {len(jobs)} calls to run")
    with ThreadPoolExecutor(4) as pool:
        for rec in pool.map(one, jobs):
            append(FILE, rec)


if __name__ == "__main__":
    main()
