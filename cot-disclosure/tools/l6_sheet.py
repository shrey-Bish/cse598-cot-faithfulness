"""Track A, L6 (pre-registered Nov 7, amended Nov 8): the blind hand-label sheet for disclosure when following, as
archive/sessions/2026-11-07/2026-11-07_2025_A_l6-prereg.md says (sections 2 and 3, as its section 9, Amendment 1,
changes them: lora and prompt_only only, 84 rows).

  python tools/l6_sheet.py --dry-run                 # the pool and the draw's counts (numbers only); writes nothing
  python tools/l6_sheet.py --remote-script > S.py    # the read-only Sol script: ssh sol '<python> -' < S.py > TEXTS
  python tools/l6_sheet.py --build --texts TEXTS     # -> results/labels/L6/sheet_L6.csv and key_L6.csv (gitignored)

The pool: A39's E2 runs of lora and prompt_only, each run once, its last ok record (finetune/a39.by_system), that got
a wrong hint, gave an answer and ended on the hint's letter (eval.followed). The draw, per system and channel (user,
pasted, inserted: a39.CHANNELS' keys): the runs sorted by run id, shuffled with random.Random("L6-20261107:<system>:
<channel>"), then taken in that order, one run a question, until 14. The plan: lora then prompt_only, user, pasted,
inserted within each, each stratum in its draw order; shuffled with random.Random("L6-20261107") and numbered 1-84.
The draw uses run ids, questions and channels only: never a keyword, a length or a text.

The texts are on Sol only. The Sol script (stdlib only; it writes no file) prints each drawn run's final answer from
the ok record with its run id and timestamp, as one JSON line; a drawn run with no such record, or two, stops it with
nothing printed. --build checks those lines against the plan and writes the sheet (row, channel, hint_letter,
final_answer and three blank columns for the rater: no system, run id, question or keyword) and the key. It prints
counts and the answers' lengths, never a text. --remote-script and --build refuse a pool unlike section 2's table.
"""
import argparse
import csv
import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from finetune import a39  # noqa: E402
from finetune import eval as ev  # noqa: E402

LOG = "archive/sessions/2026-11-07/2026-11-07_2025_A_l6-prereg.md"
OUT = CODE / "results" / "trackA" / "gpu" / "a39"                 # the numbers-only run files
LABELS = CODE / "results" / "labels" / "L6"                       # gitignored
REMOTE_DIR = "/scratch/ragarw68/trackA/a39"                       # the texts, on Sol
SEED = "L6-20261107"
PER_STRATUM = 14
SYSTEMS = ("lora", "prompt_only")
CHANNELS = ("user", "pasted", "inserted")
SPELL = {v: k for k, v in a39.CHANNELS.items()}                  # a record's channel -> the sheet's spelling
POOL_PREREG = {("prompt_only", "user"): (78, 56), ("prompt_only", "pasted"): (82, 52),   # section 2: (runs, questions)
               ("prompt_only", "inserted"): (77, 49), ("lora", "user"): (79, 63), ("lora", "pasted"): (100, 66),
               ("lora", "inserted"): (69, 42)}
PLAN_KEYS = ("run_id", "system", "channel", "item_id", "hint_letter", "parsed_letter", "timestamp_utc",
             "mention_final_broad")
SHEET_COLUMNS = ("row", "channel", "hint_letter", "final_answer", "label_final", "guess_trained", "note")
KEY_COLUMNS = ("row", "run_id", "system", "channel", "item_id", "timestamp_utc", "mention_final_broad", "seed")
TEXT_FIELDS = ("run_id", "timestamp_utc", "system", "channel", "item_id", "hint_letter", "parsed_letter", "final_text")


# ---------------------------------------------------------------- the pool, the draw and the plan
def pool(rows):
    """{(system, channel): the followed wrong-hint runs}: E2, each run its last ok record (a39.by_system), lora and
    prompt_only, answered and ending on the hint's letter."""
    by = a39.by_system(a39.of_set(rows, "e2"))
    out = {(s, ch): [] for s in SYSTEMS for ch in CHANNELS}
    for s in SYSTEMS:
        for r in ev.answered(a39.chosen(by.get(s, []), "following")):
            if ev.followed(r):
                out[(s, SPELL[r["channel"]])].append(r)
    return out


def counts(p):
    """{stratum: (runs, distinct questions)}."""
    return {k: (len(v), len({r["item_id"] for r in v})) for k, v in p.items()}


def pool_differences(p, expected=None):
    """Each stratum whose (runs, questions) differ from section 2's table, as a short line."""
    expected, got = POOL_PREREG if expected is None else expected, counts(p)
    return [f"{s} {ch}: {got.get((s, ch), (0, 0))[0]} ({got.get((s, ch), (0, 0))[1]}), section 2 says {n} ({q})"
            for (s, ch), (n, q) in sorted(expected.items(), key=lambda e: (SYSTEMS.index(e[0][0]),
                                                                           CHANNELS.index(e[0][1])))
            if got.get((s, ch), (0, 0)) != (n, q)]


def draw(p, n=PER_STRATUM):
    """{stratum: its drawn runs, in draw order}: sorted by run id, shuffled with the stratum's seed, then the first run
    of each question until n (all of them if fewer)."""
    out = {}
    for (s, ch), runs in p.items():
        runs = sorted(runs, key=lambda r: r["run_id"])
        random.Random(f"{SEED}:{s}:{ch}").shuffle(runs)
        took, seen = [], set()
        for r in runs:
            if len(took) == n:
                break
            if r["item_id"] not in seen:
                seen.add(r["item_id"])
                took.append(r)
        out[(s, ch)] = took
    return out


def plan(rows):
    """The sheet's rows: the draw listed lora then prompt_only, user, pasted, inserted within each, shuffled with the
    seed and numbered from 1. The channel is spelled user, pasted or inserted."""
    d = draw(pool(rows))
    listed = [r for s in SYSTEMS for ch in CHANNELS for r in d[(s, ch)]]
    random.Random(SEED).shuffle(listed)
    return [{"row": i, **{k: r[k] for k in PLAN_KEYS}, "channel": SPELL[r["channel"]]} for i, r in enumerate(listed, 1)]


def not_single(pl, rows):
    """The planned run ids without exactly one ok record with their run id and timestamp in these records (the numbers
    files mirror Sol's text files, so this foretells the Sol script's check)."""
    n = Counter((r.get("run_id"), r.get("timestamp_utc")) for r in rows if r.get("status") == "ok")
    return [p["run_id"] for p in pl if n[(p["run_id"], p["timestamp_utc"])] != 1]


# ---------------------------------------------------------------- the Sol script (read-only, stdlib only)
REMOTE = r'''"""L6's texts (tools/l6_sheet.py --remote-script): each drawn run's final answer, one JSON line a run, from
the ok record with its run id and timestamp. Read-only: it writes no file. Stdlib only.
  python3 - [DIR] < this_script > TEXTS      (DIR: @DIR@)"""
import glob
import gzip
import json
import os
import sys
import zlib

PLAN = [  # (run_id, timestamp_utc, system), in the sheet's row order
@PLAN@
]
PATTERNS = ("eval_lora_a39_e2*.jsonl.gz", "eval_prompt_only_a39_e2*.jsonl.gz")
FIELDS = ("run_id", "timestamp_utc", "system", "channel", "item_id", "hint_letter", "parsed_letter", "final_text")


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "@DIR@"
    found = dict(((r, t), []) for r, t, s in PLAN)
    files = sorted(set(p for pat in PATTERNS for p in glob.glob(os.path.join(d, pat))))
    for p in files:
        n = 0
        try:
            with gzip.open(p, "rt", encoding="utf-8", errors="replace") as f:
                for line in f:
                    n += 1
                    if not line.strip():
                        continue
                    try:
                        r = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(r, dict) and r.get("status") == "ok":
                        k = (r.get("run_id"), r.get("timestamp_utc"))
                        if k in found:
                            found[k].append(r)
        except (EOFError, OSError, zlib.error) as e:
            sys.stderr.write("L6: %s stops after line %d (%s); the rest skipped\n" % (os.path.basename(p), n,
                                                                                   type(e).__name__))
    bad = [(r, t, len(found[(r, t)])) for r, t, s in PLAN if len(found[(r, t)]) != 1]
    if bad:
        for r, t, k in bad:
            sys.stderr.write("L6: run %s at %s has %d ok records, not 1\n" % (r, t, k))
        sys.stderr.write("L6: stopped, nothing printed (%d of %d runs; %d files read in %s)\n"
                         % (len(bad), len(PLAN), len(files), d))
        return 1
    lines = [json.dumps(dict((k, found[(r, t)][0].get(k)) for k in FIELDS)) for r, t, s in PLAN]
    sys.stdout.write("\n".join(lines) + "\n")
    sys.stderr.write("L6: %d runs, one record each, from %d files; nothing written\n" % (len(PLAN), len(files)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def remote_script(pl, directory=REMOTE_DIR):
    """The Sol script's source, with the plan's (run_id, timestamp_utc, system) in row order."""
    triples = "\n".join(f"    ({p['run_id']!r}, {p['timestamp_utc']!r}, {p['system']!r})," for p in pl)
    return REMOTE.replace("@PLAN@", triples).replace("@DIR@", directory)


# ---------------------------------------------------------------- the sheet and the key (on the Mac)
def read_texts(path):
    """The Sol script's lines: [record]; a blank line is skipped, any other line that isn't a JSON object stops it."""
    out = []
    for i, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            r = None
        if not isinstance(r, dict) or "run_id" not in r:
            raise ValueError(f"{Path(path).name} line {i}: not a run's record")
        out.append(r)
    return out


def check(pl, lines):
    """Every planned run once, and nothing else, with the plan's system, channel (its record value), question, letters
    and timestamp, and a final answer; else a ValueError naming the run ids (never a text)."""
    n = Counter(r["run_id"] for r in lines)
    planned = {p["run_id"] for p in pl}
    problems = {"missing": [p["run_id"] for p in pl if n[p["run_id"]] == 0],
                "more than once": sorted(k for k, v in n.items() if v > 1),
                "not planned": sorted(set(n) - planned)}
    by = {r["run_id"]: r for r in lines}
    want = {"system": lambda p: p["system"], "channel": lambda p: a39.CHANNELS[p["channel"]],
            **{k: (lambda k: lambda p: p[k])(k) for k in ("item_id", "hint_letter", "parsed_letter", "timestamp_utc")}}
    for k, f in want.items():
        problems[f"{k} differs"] = [p["run_id"] for p in pl if p["run_id"] in by and by[p["run_id"]].get(k) != f(p)]
    problems["no final answer"] = [p["run_id"] for p in pl
                                   if p["run_id"] in by and not isinstance(by[p["run_id"]].get("final_text"), str)]
    bad = {k: v for k, v in problems.items() if v}
    if bad:
        raise ValueError("L6 texts unlike the plan: " + "; ".join(f"{k} {', '.join(v)}" for k, v in bad.items()))
    return by


def assemble(pl, texts_path, out_dir=LABELS):
    """sheet_L6.csv and key_L6.csv in out_dir from the Sol script's lines, after check(); refuses to overwrite either.
    Returns counts and the final answers' lengths in characters; prints nothing."""
    by = check(pl, read_texts(texts_path))
    out = Path(out_dir)
    sheet, key = out / "sheet_L6.csv", out / "key_L6.csv"
    if sheet.exists() or key.exists():
        raise FileExistsError(f"{out} already holds an L6 sheet or key: move it first (labels may be in it)")
    out.mkdir(parents=True, exist_ok=True)
    with open(sheet, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(SHEET_COLUMNS)
        for p in pl:
            w.writerow([p["row"], p["channel"], p["hint_letter"], by[p["run_id"]]["final_text"], "", "", ""])
    with open(key, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(KEY_COLUMNS)
        for p in pl:
            w.writerow([p["row"], p["run_id"], p["system"], p["channel"], p["item_id"], p["timestamp_utc"],
                        p["mention_final_broad"], SEED])
    n = [len(by[p["run_id"]]["final_text"]) for p in pl]
    return {"rows": len(pl), "systems": dict(Counter(p["system"] for p in pl)),
            "strata": dict(Counter(f"{p['system']} {p['channel']}" for p in pl)), "sheet": str(sheet), "key": str(key),
            "chars": {"mean": statistics.mean(n), "median": statistics.median(n), "min": min(n), "max": max(n)}
            if n else None}


# ---------------------------------------------------------------- the command line
def pool_table(p):
    c = counts(p)
    lines = ["L6 pool: followed wrong-hint runs on E2 (runs, distinct questions)",
             f"{'system':<13}" + "".join(f"{ch:<11}" for ch in CHANNELS) + "all"]
    for s in SYSTEMS:
        lines.append(f"{s:<13}" + "".join(f"{f'{c[(s, ch)][0]} ({c[(s, ch)][1]})':<11}" for ch in CHANNELS)
                     + f"{sum(c[(s, ch)][0] for ch in CHANNELS)}")
    return lines


def draw_lines(pl):
    st = Counter((p["system"], p["channel"]) for p in pl)
    sy = Counter(p["system"] for p in pl)
    return [f"L6 draw (seed {SEED}): {len(pl)} rows; " + ", ".join(f"{s} {sy[s]}" for s in SYSTEMS),
            *(f"  {s}: " + ", ".join(f"{ch} {st[(s, ch)]}" for ch in CHANNELS) for s in SYSTEMS)]


def checked(rows):
    """The plan, if the pool is section 2's; else stop."""
    diffs = pool_differences(pool(rows))
    if diffs:
        raise SystemExit("L6: the pool differs from section 2, so nothing is made:\n  " + "\n  ".join(diffs))
    return plan(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="the pool and the draw's counts; writes nothing")
    mode.add_argument("--remote-script", action="store_true", help="print the read-only Sol script")
    mode.add_argument("--build", action="store_true", help="the sheet and the key from the Sol script's lines")
    ap.add_argument("--out", default=str(OUT), help="the numbers-only run files (eval_*_runs.jsonl)")
    ap.add_argument("--texts", help="--build: the Sol script's output")
    ap.add_argument("--labels-out", default=str(LABELS), help="--build: where the sheet and key go (gitignored)")
    a = ap.parse_args(argv)
    rows = a39.read(a.out)[0]
    if a.dry_run:
        p = pool(rows)
        pl = plan(rows)
        diffs = pool_differences(p)
        single = not_single(pl, rows)
        print("\n".join([*pool_table(p), "the pool is section 2's table" if not diffs else
                         "the pool differs from section 2:\n  " + "\n  ".join(diffs), *draw_lines(pl),
                         f"one ok record with its timestamp in the numbers files: {len(pl) - len(single)} of {len(pl)}"
                         + (f" (not: {', '.join(single)})" if single else ""), "nothing written"]))
        return
    pl = checked(rows)
    if a.remote_script:
        sys.stdout.write(remote_script(pl))
        return
    if not a.texts:
        ap.error("--build needs --texts")
    res = assemble(pl, a.texts, a.labels_out)
    c = res["chars"]
    print("\n".join([draw_lines(pl)[0].replace("L6 draw", "L6 sheet"), f"  sheet {res['sheet']}", f"  key {res['key']}",
                     f"final answers, characters: mean {c['mean']:,.0f}, median {c['median']:,.0f}, "
                     f"min {c['min']:,}, max {c['max']:,}"]))


if __name__ == "__main__":
    main()
