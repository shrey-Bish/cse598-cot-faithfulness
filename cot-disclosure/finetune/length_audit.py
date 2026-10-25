"""Track A, Step 5: how long are the replies? The training length comes from this. No calls.

  python finetune/length_audit.py --dry-run   # the files it reads
  python finetune/length_audit.py             # the table (appends to results/trackA/length_audit.jsonl)

Per source, model and question set: runs, how many were cut off (no answer), and for the runs
that finished, the median reply length and how many exceed 8,192 and 16,384 tokens. Reply
length = the saved completion tokens (usage, or Test 1's out_tokens); a run without a saved
count is counted with the Olmo 3 tokenizer (local files only). For the pinned format (Step 2b,
continued up to the 65,536-token context) it also gives prompt + reply, the length a training
example needs, and the share of answered runs that fit 8,192 / 16,384 / 32,768 tokens, split by
channel and by number of tool rounds. A run's length is its full final sequence counted once:
the last round's prompt (which already holds every earlier round) + its reply, checked against
the local tokenizer. Continuing a cut-off reply is not a tool round (the record logs both).
"""
import argparse
import functools
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import append, latest, load  # noqa: E402

RESULTS = CODE / "results"
OUT = RESULTS / "trackA" / "length_audit.jsonl"
TOKENIZER = "allenai/Olmo-3-7B-Think"
LIMITS = (8192, 16384)
FITS = (8192, 16384, 32768)


@functools.lru_cache(maxsize=1)
def tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(TOKENIZER, local_files_only=True)


def count(text):
    return len(tokenizer()(text or "", add_special_tokens=False)["input_ids"])


def rows_test1():
    for r in load(RESULTS / "progress.jsonl"):
        if r["exp"] == "main" and not r.get("error"):
            yield {"source": "Test 1 (served format, 16,000 cap)", "model": r["model"], "set": "pilot puzzles",
                   "cut": r.get("finish") == "length", "reply": r.get("out_tokens"), "prompt": None, "counted": False}


def rows_test2():
    for name in ("expB_nocue.jsonl", "expB_cued.jsonl"):
        for r in latest(load(RESULTS / "progress" / name)):
            if r["status"] != "ok":
                continue
            usage = r.get("usage") or {}
            reply, counted = usage.get("completion_tokens"), False
            if reply is None:
                reply, counted = count((r.get("reasoning_text") or "") + (r.get("final_text") or "")), True
            yield {"source": "Test 2 (served format, 16,000 cap)", "model": r["model"], "set": "MMLU-Pro 30",
                   "cut": r.get("finish_reason") == "length", "reply": reply, "prompt": usage.get("prompt_tokens"),
                   "counted": counted}


def tool_rounds(r):
    """Real tool rounds: the log also has an entry for each continuation of a cut-off reply."""
    return len([x for x in r.get("tool_rounds") or [] if not x.get("extended")])


def channel(r):
    if r["condition"] == "tool_injected":
        return "tool, inserted" + (" + declared" if r.get("arm") else "")
    return {"none": "no hint", "user": "user", "tool_pasted": "tool, pasted"}[r["condition"]]


def rows_step2b():
    from finetune import base_format as bf
    for r in bf.current(load(bf.OUT)):
        if r["status"] != "ok":
            continue
        usage = r.get("usage") or {}
        reply, counted = usage.get("completion_tokens"), False
        if reply is None:
            reply, counted = count(r.get("raw_text")), True
        prompt = usage.get("prompt_tokens") if usage.get("prompt_tokens") else count(r.get("rendered_prompt"))
        yield {"source": "Step 2b (pinned format, continued to the 65,536 context)", "model": r["model"],
               "set": "MMLU-Pro 20 (Olmo's hinted Test 2 items)", "cut": r.get("finish_reason") == "length",
               "reply": reply, "prompt": prompt, "counted": counted, "channel": channel(r), "rounds": tool_rounds(r),
               "record": r}


def single_count_check(rows):
    """Saved prompt + reply minus the local count of the final sequence (rendered prompt + reply text)."""
    return [r["record"]["usage"]["prompt_tokens"] + r["record"]["usage"]["completion_tokens"]
            - count(r["record"]["rendered_prompt"] + (r["record"]["raw_text"] or "")) for r in rows]


def summarize(rows):
    done = [r for r in rows if not r["cut"] and r["reply"] is not None]
    lengths = [r["reply"] for r in done]
    totals = [r["reply"] + r["prompt"] for r in done if r["prompt"] is not None]
    return {"runs": len(rows), "cut_off": sum(r["cut"] for r in rows), "finished": len(done),
            "median_reply": statistics.median(lengths) if lengths else None,
            **{f"over_{n}": sum(x > n for x in lengths) for n in LIMITS},
            "with_prompt": len(totals), **{f"total_over_{n}": sum(x > n for x in totals) for n in LIMITS},
            "counted_with_tokenizer": sum(r["counted"] for r in rows)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sources = [("Test 1", RESULTS / "progress.jsonl"),
               ("Test 2", RESULTS / "progress" / "expB_nocue.jsonl"), ("Test 2", RESULTS / "progress" / "expB_cued.jsonl"),
               ("Step 2b", RESULTS / "trackA" / "base_format.jsonl.gz")]
    if a.dry_run:
        for name, path in sources:
            print(f"{name}: {path.relative_to(CODE)}")
        return
    rows = list(rows_test1()) + list(rows_test2()) + list(rows_step2b())
    groups = {}
    for r in rows:
        groups.setdefault((r["source"], r["model"], r["set"]), []).append(r)
    print("Reply length in tokens (saved counts; the Olmo 3 tokenizer where none was saved). Cut off = no answer.\n")
    print("| source | model | question set | runs | cut off | finished | median reply (finished) | reply over 8,192 | "
          "reply over 16,384 | prompt + reply over 8,192 | prompt + reply over 16,384 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    table = []
    for (src, model, qset), rs in sorted(groups.items()):
        s = summarize(rs)
        table.append({"source": src, "model": model, "set": qset, **s})
        tot = (f"{s['total_over_8192']} of {s['with_prompt']} | {s['total_over_16384']} of {s['with_prompt']}"
               if s["with_prompt"] else "— (no prompt count saved) | —")
        print(f"| {src} | {model} | {qset} | {s['runs']} | {s['cut_off']} of {s['runs']} | {s['finished']} | "
              f"{s['median_reply']:,.0f} | {s['over_8192']} of {s['finished']} | {s['over_16384']} of {s['finished']} | "
              f"{tot} |" if s["median_reply"] is not None else f"| {src} | {model} | {qset} | {s['runs']} | — | — | — | — "
                                                              f"| — | — | — |")
    t2 = next((t for t in table if t["source"].startswith("Test 2") and t["model"] == "olmo3-7b-think"), None)
    if t2:
        print(f"\nCheck against the brief (Olmo 3 7B Think, Test 2: 30 of 100 cut off; of the 70 finished, 21 over 8,192 "
              f"and 1 over 16,384): {t2['cut_off']} of {t2['runs']} cut off; of the {t2['finished']} finished, counting "
              f"prompt + reply: {t2['total_over_8192']} over 8,192 and {t2['total_over_16384']} over 16,384 (reply alone: "
              f"{t2['over_8192']} and {t2['over_16384']}). The brief counted prompt + reply.")
    step2b = [r for r in rows if r["source"].startswith("Step 2b")]
    print("\nPinned format (Step 2b) by channel and tool rounds; prompt + reply of the answered runs:")
    print("| channel | tool rounds | runs | cut off | median | over 16,384 | over 32,768 |")
    print("|---|---|---|---|---|---|---|")
    for key in sorted({(r["channel"], r["rounds"]) for r in step2b}):
        rs = [r for r in step2b if (r["channel"], r["rounds"]) == key]
        tot = [r["reply"] + r["prompt"] for r in rs if not r["cut"]]
        print(f"| {key[0]} | {key[1]} | {len(rs)} | {sum(r['cut'] for r in rs)} | {statistics.median(tot):,.0f} | "
              f"{sum(x > 16384 for x in tot)} of {len(tot)} | {sum(x > 32768 for x in tot)} of {len(tot)} |")
    diffs = single_count_check([r for r in step2b if not r["counted"]])
    print(f"Counted once: saved prompt + reply minus the local count of the final sequence: min {min(diffs)}, max "
          f"{max(diffs)} (Voyager also counts the end-of-text token); no run counts earlier text twice.")
    answered = [r for r in step2b if not r["cut"]]
    top = max(answered, key=lambda r: r["reply"] + r["prompt"])
    loop = max(step2b, key=lambda r: r["reply"] + r["prompt"])
    for label, r in (("longest answered", top), ("longest overall", loop)):
        rec = r["record"]
        print(f"{label}: question {rec['item_id']} ({rec.get('category')}), {r['channel']}, run {rec['repeat']}: "
              f"{r['prompt']:,} + {r['reply']:,} = {r['prompt'] + r['reply']:,} tokens, "
              f"{'cut off at the context (no answer)' if r['cut'] else 'answered ' + str(rec['parsed_letter'])} "
              f"(hint {rec.get('cue_letter')}, key {rec.get('correct_letter')})")
    pinned = [r for r in rows if r["source"].startswith("Step 2b") and not r["cut"] and r["reply"] is not None]
    total = sorted(r["reply"] + (r["prompt"] or 0) for r in pinned)
    fits = {n: sum(x <= n for x in total) for n in FITS}
    if total:
        print(f"\nTraining length, pinned format (Step 2b, {len(total)} answered runs; prompt + reply): median "
              f"{statistics.median(total):,.0f}, max {max(total):,}; fit "
              + ", ".join(f"{n:,}: {fits[n]} of {len(total)} ({fits[n] / len(total):.0%})" for n in FITS)
              + f". Cut off even at the context: {sum(r['cut'] for r in rows if r['source'].startswith('Step 2b'))}.")
    append(OUT, {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "table": table,
                 "pinned_prompt_plus_reply": {"runs": len(total), "median": statistics.median(total) if total else None,
                                              "max": max(total) if total else None, "fits": fits}})


if __name__ == "__main__":
    main()
