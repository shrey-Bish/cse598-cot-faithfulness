"""A18 (Track A, due Nov 10): inside the fixed model. Steps 9 and 10 on the evaluation runs of LoRA and of base
(Gate 3's batch 3), to ask: does training stop the readout at layers 15, 19 and 23 (F11, F26), or act after it?
Pre-registered in archive/sessions/2026-10-31/2026-10-31_2244_A_a18-prereg.md, before anything here ran.

Runs: batch 3's evaluation runs of base and lora (the same 930 jobs each: the 30 MMLU-Pro questions, the held-out
wordings, temperature 0.6, seed = run; finetune/eval.py). Texts are on Sol only ($TRACKA_OUT/eval/eval_<system>*.jsonl.gz);
the Mac has the numbers-only eval_<system>*_runs.jsonl. Kept, by a rule written before any probe: the wrong-hint
runs of the 6 main wordings (user_turpin, user_professor, tool_progress, inserted_study_guide, inserted_database,
inserted_new_tool) and the no-hint runs, status ok, with no tool call in the final answer (a further tool round
changes the prompt the reasoning follows; those are left out and counted). Each is made into a Step 2b-style source
(hint_spans.EVAL_SOURCE): the prompt rendered as the evaluation rendered it, the reasoning, and the wording's hint
text with its letter's offset, so Steps 3, 9 and 10's code reads it unchanged. Nothing is chosen on the 30: the case
rule is Step 10's own, applied mechanically.

Step 3 (step3 --system S): early answering on every followed run of S on a sure question (S's 3 no-hint runs all
answered and correct). Dense: the forced answer "</think>\\n\\nAnswer: (" after every sentence, the whole reasoning
run once and its key/value cache reused (a cache without sliding layers, so a cut can go back; checked against a
fresh forward at two probes a run). Takeover point, "late" (at or after half the reasoning) as in Step 3. Cases:
followed runs with a late takeover on sure questions, at most 3 per question chosen by seed (deletion.choose).
Step 10 (step10 --cases C --weights W): Step 10's patching at cut (ii) (the takeover) of C's cases, under W's
weights: base's cases under base (the reference), base's cases under LoRA (the same tokens), LoRA's own cases under
LoRA. Cut (i) is left out: no rule here reads it. Rows as patching.py writes them; its report and handoff after.
The swap (swap): on base's cases at cut (ii), the hint's direct effect TE = LD(hinted) - LD(clean) (LD = logit(W) -
logit(O); the two prompts differ only in the hint's letter, the reasoning is the same) under base, LoRA, and base
with LoRA's decoder layers swapped in for one set of layers at a time: before the readout (0-14), the readout layers
(15, 19, 23), through the readout (0-23), after it (24-31). In the same passes, F12's three heads' attention at the
answer position (hint, its letter, the control span) under base and LoRA.
Step 9 (step9 --system S): attn_to_hint.py on S's sources with S's weights (every answered wrong-hint run), then its
reduced file, read by F32's rule (F12's three heads, followed minus resisted).

The rules (pre-registered: A18's log, Oct 31 22:44):
  Primary, on base's cases at cut (ii), cases with TE_base >= 0.5 (patching's MIN_GAP), 95% bootstraps clustered by
  question. R_X = TE_base - TE_X, what weights X remove of base's effect.
    1. Does training act on these tokens? R_lora's interval (boot_mean) lies above 0. If not: "acts in the
       reasoning": on base's own reasoning the trained weights read the prompt's hint as base does, so training
       changes what the reasoning does, not the readout. The layer split is reported, not read.
    2. If it does, where: s(S) = sum R_{base+LoRA on S} / sum R_lora (a ratio of sums, resampled by question).
       "stops the readout": s(0-23)'s lower bound >= 0.5 and s(24-31)'s upper bound < 0.5; then "at the readout
       layers" if s(15, 19, 23)'s lower bound >= 0.5, else "before them" if s(0-14)'s is, else "spread over 0-23".
       "acts after the readout": s(24-31)'s lower bound >= 0.5 and s(0-23)'s upper bound < 0.5.
       "either half suffices": both lower bounds >= 0.5. "unclear": anything else.
    Too few: fewer than 5 questions with a usable case.
  Secondary, each with its rule:
    a. When LoRA still follows, through the same readout? LoRA's own cases under LoRA, set A's rule (Oct 29 00:20):
       "replicates" if the share of the hint-token restoration drop at 15, 19, 23 has a lower bound above 3/8 and
       they are the three largest drops; "partly" if one; "doesn't replicate" if neither; too few under 5 questions.
    b. Within each system, F32's rule on F12's heads (followed minus resisted, hint minus control): replicates /
       reversed / doesn't replicate / too few.
  Reported, no decision: F12's heads under LoRA minus base on the same tokens (do they still look?); the readout's
  share under LoRA on base's cases beside base's; how often LoRA's forced answer at base's cut is still W.

  python finetune/look/a18.py plan [--eval-dir results/trackA/gpu/eval]       # Mac: counts, GPU hours, the Sol lines
  python finetune/look/a18.py step3 --system base|lora --out OUT [--dry-run]  # Sol, GPU (sources made first)
  python finetune/look/a18.py step10 --cases base|lora --weights base|lora --out OUT
  python finetune/look/a18.py swap --out OUT                                  # Sol, GPU: base and LoRA both loaded
  python finetune/look/a18.py step9 --system base|lora --out OUT
  python finetune/look/a18.py readout DIR                                     # anywhere: the readings, numbers only
On Sol: submit.sh a18 -- <the same arguments> (finetune/gpu/sol/a18.sbatch). Every output in $TRACKA_OUT/a18/ is
numbers only, except sources_<system>.jsonl.gz (the evaluation's texts; it never leaves Sol).
"""
import argparse
import json
import math
import random
import statistics
import sys
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import MIN_QUESTIONS, append, boot_mean, latest, load  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402
from finetune.look import patching as pt  # noqa: E402

SYSTEMS = ("base", "lora")
SUB = "a18"
EVAL_DIR = CODE / "results" / "trackA" / "gpu" / "eval"            # the Mac's numbers-only copies
HELDOUT = CODE / "data" / "progress" / "mmlupro_30.jsonl"
MAIN = ("user_turpin", "user_professor", "tool_progress", "inserted_study_guide", "inserted_database", "inserted_new_tool")
NO_HINT_RUNS = 3
READOUT = (15, 19, 23)
STRONG = 0.5                     # "most of training's reduction" in a layer set
MIN_GAP = pt.MIN_GAP             # 0.5: base's effect at a case must be at least this (patching's filter)
LATE_SHARE = (0.54, 0.70)        # followed runs on sure questions with a late takeover: Test 2, set A
TOKENS_PER_SENTENCE = 20
PROBE_S = 0.05                   # one cached probe (qwen8b_mech's estimate)
TOK_PER_S = pt.TOK_PER_S         # 9,000: an A100 bf16 forward
CUT_SHARE = 0.75                 # of the reasoning at the takeover (late: at or after half)
LOAD_H = 0.1
SWAPS = ("before", "readout", "through", "after")
_stop = {"asked": False}


def _on_signal(signum, frame):
    """Slurm's warning (USR1, 5 minutes before the limit): finish the run or case in flight, start no new one."""
    _stop["asked"] = True


def listen():
    import signal
    for s in (signal.SIGUSR1, signal.SIGTERM):
        signal.signal(s, _on_signal)


def base_dir(out):
    return Path(out) / SUB


# ---------------------------------------------------------------- which runs (the rule; numbers or texts)
def kept(r):
    """A wrong-hint run of a main wording, or a no-hint run, finished, with no tool call in its final answer."""
    hinted = r["wording"] in MAIN and r.get("hint_correct") is False
    return (hinted or r["wording"] == "none") and r["status"] == "ok" and not (r.get("tool_calls_by_model") or 0)


def followed(r):
    return r["wording"] != "none" and bool(r.get("parsed_letter")) and r["parsed_letter"] == r["hint_letter"]


def sure_questions(rows):
    """{question: all NO_HINT_RUNS no-hint runs present, answered and correct}."""
    by_q = defaultdict(list)
    for r in rows:
        if r["wording"] == "none":
            by_q[r["item_id"]].append(r)
    return {q: len(rs) == NO_HINT_RUNS and all(r.get("parsed_letter") == r["correct_letter"] for r in rs)
            for q, rs in by_q.items()}


def eval_rows(eval_dir, system, texts=False):
    """The newest record of each run of one system, whole and part files: the numbers-only _runs.jsonl (the Mac),
    or with texts the .jsonl.gz records (Sol only)."""
    from finetune import eval as ev
    if texts:
        stem = ev.stem(system)
        files = sorted(Path(eval_dir).glob(f"{stem}.jsonl.gz")) + sorted(Path(eval_dir).glob(f"{stem}_p*of*.jsonl.gz"))
    else:
        files = ev.runs_files(eval_dir, system)
    rows = [r for p in files for r in load(p)]
    return [r for r in latest(rows) if r.get("system") == system]


# ---------------------------------------------------------------- sources (Sol: the evaluation's texts)
def hint_of(wording, letter, qid):
    """(the hint as the model saw it, its letter's offset): the offset is where two renderings with different
    letters differ (one character)."""
    from finetune import build_dataset as bd
    w = {x[0]: x for x in bd.WORDINGS["heldout"]}[wording]
    a, b = bd.hint_text(w, "A", qid), bd.hint_text(w, "B", qid)
    at = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    text = bd.hint_text(w, letter, qid)
    if len(a) != len(b) or len(at) != 1 or text[at[0]] != letter:
        raise ValueError(f"{wording}: no single letter position in the hint")
    return text, at[0]


def items():
    """The 30 questions in Step 2b's item format, keyed as the evaluation's item ids."""
    out = []
    for line in HELDOUT.read_text().splitlines():
        if line.strip():
            it = json.loads(line)
            out.append({"question_id": f"mmlupro-{it['question_id']}", "question": it["question"],
                        "options": it["options"], "answer": it["answer"], "cue_letter": it["cue_letter"]})
    return out


def make_sources(eval_dir, system):
    """(sources, counts): every kept run of the system as a Step 2b-style record, with its texts. Its prompt is
    rebuilt from the evaluation's own job (the run id must match) and rendered as the evaluation rendered it."""
    from finetune import base_format as bf
    from finetune import eval as ev
    from tools.answer_key import INJECTED
    by_id = {ev.job_id(system, j): j for j in ev.jobs()}
    render = ev.renderer(system)
    rows = eval_rows(eval_dir, system, texts=True)
    if not rows:
        raise SystemExit(f"no evaluation records with texts for {system} in {eval_dir} (eval_{system}*.jsonl.gz: Sol)")
    counts = Counter()
    out = []
    for r in rows:
        hinted = r["wording"] in MAIN and r.get("hint_correct") is False
        if not (hinted or r["wording"] == "none"):
            continue
        if r["status"] != "ok":
            counts["not ok"] += 1
            continue
        if r.get("tool_calls_by_model"):
            counts["left out: a tool call in the final answer"] += 1
            continue
        j = by_id.get(r["run_id"])
        if j is None:
            raise SystemExit(f"run {r['run_id']}: no evaluation job with this id for {system}")
        cond = {"user": "user", "tool_pasted": "tool_pasted", "tool_injected": INJECTED, "none": "none"}[j["channel"]]
        src = {"run_id": r["run_id"], "timestamp_utc": r["timestamp_utc"], "experiment": hs.EVAL_SOURCE, "system": system,
               "item_id": r["item_id"], "wording": r["wording"], "channel": j["channel"], "condition": cond,
               "arm": bf.DECLARED if cond == INJECTED else None, "repeat": r["repeat"], "cue_letter": r["hint_letter"],
               "hint_correct": r.get("hint_correct"), "parsed_letter": r["parsed_letter"],
               "correct_letter": r["correct_letter"], "n_options": j["n_options"], "status": "ok",
               "rendered_prompt": render(j["messages"], j["tools"]), "reasoning_text": r.get("reasoning_text") or ""}
        if hinted:
            src["hint_text"], src["hint_letter_at"] = hint_of(r["wording"], r["hint_letter"], j["qid"])
            if src["hint_text"] not in src["rendered_prompt"]:
                raise SystemExit(f"run {r['run_id']}: its hint text is not in the rendered prompt")
        counts["kept, hinted" if hinted else "kept, no hint"] += 1
        out.append(src)
    return out, dict(counts)


def sources_path(out, system):
    return base_dir(out) / f"sources_{system}.jsonl.gz"


def items_path(out):
    return base_dir(out) / "items.jsonl"


def ensure_sources(out, system, eval_dir=None, write=True):
    """sources_<system>.jsonl.gz and items.jsonl in OUT/a18 (made once from OUT/eval, then read). write=False (a dry
    run): made in memory if missing, nothing written."""
    p = sources_path(out, system)
    if not write and not p.exists():
        srcs, counts = make_sources(eval_dir or Path(out) / "eval", system)
        print(f"sources for {system} (not written: a dry run): {counts}", flush=True)
        return {s["run_id"]: s for s in srcs}
    if not items_path(out).exists():
        base_dir(out).mkdir(parents=True, exist_ok=True)
        items_path(out).write_text("".join(json.dumps(it) + "\n" for it in items()))
    if not p.exists():
        srcs, counts = make_sources(eval_dir or Path(out) / "eval", system)
        tmp = p.with_name(p.name + ".tmp.gz")
        for s in srcs:
            append(tmp, s)
        tmp.replace(p)
        kit.write_json(base_dir(out) / f"sources_{system}_counts.json", counts)
        print(f"sources for {system}: {counts}", flush=True)
    return {s["run_id"]: s for s in load(p)}


# ---------------------------------------------------------------- the models
def model_dir(system, out):
    """base: the pinned snapshot; lora: the base with the chosen epoch's LoRA merged in, as the evaluation served it
    (eval_job.prepare: $TRACKA_OUT/models/lora_merged, made there if missing)."""
    path, _ = kit.snapshot()
    if system == "base":
        return path
    from finetune.gpu import eval_job
    return Path(eval_job.prepare(system, path, Path(out) / "train", Path(out) / "models")[0])


def tokenizer_dir():
    return kit.snapshot()[0]


# ---------------------------------------------------------------- Step 3: probes
def probe_text(src, cut):
    return src["rendered_prompt"] + cut + hs.FORCE


def probe_curve(model, tok, src, by_letter, check=True):
    """(sentence ends, [{"k", "probs", "floor"}] for k = 0..n, check): the forced answer after every sentence. The
    whole reasoning runs once into a cache without sliding layers (a sliding layer can't go back), and each probe,
    the last first, reuses it up to where its tokens depart from the whole's. check: the same probes by a fresh
    forward at k = n and n // 2."""
    import torch
    from transformers import DynamicCache

    from finetune.look import qwen8b_mech as qm
    from finetune.look import takeover as tk
    dev = next(model.parameters()).device
    reasoning = src["reasoning_text"]
    ends = [0] + tk.sentence_ends(reasoning)
    full = hs.tokenize(tok, src["rendered_prompt"] + reasoning)[0]
    letters = {L: by_letter[L] for L in pt.LETTERS[:src["n_options"]]}
    fed = len(full)
    with torch.no_grad():
        cache = model(input_ids=torch.tensor([full], device=dev), past_key_values=DynamicCache(), use_cache=True,
                      logits_to_keep=1).past_key_values
        curve, texts, last = {}, {}, len(ends) - 1
        for k in range(last, -1, -1):
            ids = hs.tokenize(tok, probe_text(src, reasoning[:ends[k]]))[0]
            c = min(qm.shared(ids, full), cache.get_seq_length(), len(ids) - 1)
            qm.trim(cache, c)
            logits = model(input_ids=torch.tensor([ids[c:]], device=dev), past_key_values=cache, use_cache=True,
                           logits_to_keep=1).logits[0, -1]
            qm.trim(cache, c)
            fed += len(ids) - c
            curve[k] = {"k": k, "probs": qm.letter_probs(logits, letters), "floor": 0.0}
            if k in (last, last // 2):
                texts[k] = ids
        del cache
        checks = []
        for k in sorted(texts) if check else ():
            logits = model(input_ids=torch.tensor([texts[k]], device=dev), logits_to_keep=1).logits[0, -1]
            fresh = qm.letter_probs(logits, letters)
            checks.append({"k": k, "max_abs_diff": round(max(abs(fresh[L] - curve[k]["probs"][L]) for L in letters), 6),
                           "same_top": tk.top_letter(fresh) == tk.top_letter(curve[k]["probs"])})
    return ends, [curve[k] for k in sorted(curve)], {"tokens_fed": fed, "checks": checks}


def to_probe(sources):
    """(followed wrong-hint sources on sure questions, sure): what Step 3 probes; own answer = the correct one."""
    rows = list(sources.values())
    sure = sure_questions(rows)
    out = [s for s in rows if followed({**s, "hint_letter": s["cue_letter"]}) and sure.get(s["item_id"])
           and s["reasoning_text"]]
    return sorted(out, key=lambda s: (s["item_id"], s["wording"], s["repeat"])), sure


def step3_dir(out, system):
    return base_dir(out) / f"step3_{system}"


def step3(system, out, model=None, device="auto", limit=None, dry_run=False, eval_dir=None):
    from finetune.look import qwen8b_mech as qm
    from finetune.look import takeover as tk
    sources = ensure_sources(out, system, eval_dir, write=not dry_run)
    todo_all, sure = to_probe(sources)
    if limit:
        todo_all = todo_all[:limit]
    d = step3_dir(out, system)
    done = {r["source_run_id"] for r in load(d / "probes.jsonl")}
    todo = [s for s in todo_all if s["run_id"] not in done]
    chars = sum(len(s["rendered_prompt"]) + len(s["reasoning_text"]) for s in todo)
    print(f"{system}: {len(todo_all)} followed runs on {sum(sure.values())} sure questions to probe; "
          f"{len(todo_all) - len(todo)} done, {len(todo)} to go (~{chars // 4:,} tokens)", flush=True)
    if dry_run:
        return None
    d.mkdir(parents=True, exist_ok=True)
    if not todo:
        return cases_from_probes(d, sources)
    path = Path(model) if model else model_dir(system, out)
    dev = kit.pick_device(device)
    tok = kit.load_tokenizer(path if (Path(path) / "tokenizer.json").exists() else tokenizer_dir())
    m = kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev)
    by_letter = qm.letter_token_ids(tok)
    t = kit.Timer()
    for i, s in enumerate(todo, 1):
        if _stop["asked"]:
            raise SystemExit("stopped by a signal; the probes saved so far count, a rerun does the rest")
        ends, curve, info = probe_curve(m, tok, s, by_letter)
        row = tk.analyse(s, ends, curve, s["correct_letter"], s["cue_letter"])
        row["takeover_type"] = tk.takeover_type(row)
        append(d / "probes.jsonl", {
            "source_run_id": s["run_id"], "source_timestamp_utc": s["timestamp_utc"], "system": system,
            "item_id": s["item_id"], "wording": s["wording"], "condition": s["condition"], "arm": s["arm"],
            "repeat": s["repeat"], "kind": row["kind"], "hint_letter": s["cue_letter"], "own_letter": s["correct_letter"],
            "final_letter": s["parsed_letter"], "n_sentences": row["n_sentences"], "takeover_k": row["takeover_k"],
            "takeover_frac": row["takeover_frac"], "takeover_type": row["takeover_type"], "mentions": row["mentions"],
            "top_letters": row["top_letters"], "hint_prob": row["hint_prob"], "own_prob": row["own_prob"],
            "forced_end_matches_final": row["forced_end_matches_final"], **info, "timestamp_utc": kit.now()})
        bad = [c for c in info["checks"] if c["max_abs_diff"] > 0.05]
        print(f"  {i}/{len(todo)} {s['run_id']} {s['wording']}: {row['n_sentences']} sentences, takeover "
              f"{row['takeover_k']} ({row['takeover_type']}); checks {'ok' if not bad else bad}; {t() / 60:.1f} min",
              flush=True)
    return cases_from_probes(d, sources)


def cases_from_probes(d, sources):
    """Step 10's cases from the probes: followed, late, sure (every probed run is followed and sure), written once
    per call in takeover_cases' format (the last line is the one read)."""
    from finetune.look import takeover as tk
    rows = latest([{**r, "run_id": r["source_run_id"]} for r in load(d / "probes.jsonl")])
    cases = [r for r in rows if r["kind"] == "followed" and r["takeover_type"] == "late"]
    tk.save_cases(cases, d / "cases.jsonl",
                  rule="A18: followed wrong-hint runs (6 main wordings, no tool call in the final answer) whose takeover "
                       "comes at or after half the reasoning, on questions whose 3 no-hint runs were all answered and "
                       "correct", use="A18's Step 10 and swap (at most 3 per question by deletion.choose)")
    print(f"{len(cases)} cases of {len(rows)} probed runs ({len({c['item_id'] for c in cases})} questions) -> "
          f"{d / 'cases.jsonl'}", flush=True)
    return cases


def chosen_cases(out, system):
    from finetune.look import deletion as dl
    saved = load(step3_dir(out, system) / "cases.jsonl")
    if not saved:
        raise SystemExit(f"no cases for {system}: run step3 --system {system} first")
    return dl.choose(saved[-1]["cases"])


def cut_ii(case, src):
    """(sentences kept, the reasoning up to the takeover) at cut (ii)."""
    cs, first = pt.cuts(case, src)
    name, kept_n, text = cs[-1]
    assert name == "ii"
    return kept_n, text, first


# ---------------------------------------------------------------- Step 10 at cut (ii)
def step10_dir(out, cases_of, weights):
    return base_dir(out) / f"step10_{weights}_on_{cases_of}"


def step10(cases_of, weights, out, model=None, device="auto", limit=None, dry_run=False):
    sources = ensure_sources(out, cases_of)
    its = {it["question_id"]: it for it in load(items_path(out))}
    cases = chosen_cases(out, cases_of)
    tok = kit.load_tokenizer(tokenizer_dir())
    jobs = []
    for c in cases:
        src = sources[c["source_run_id"]]
        if src["timestamp_utc"] != c["source_timestamp_utc"]:
            raise SystemExit(f"case {c['source_run_id']}: its source changed since the cases were saved")
        kept_n, text, first = cut_ii(c, src)
        jobs.append((c, src, kept_n, text, first, len(hs.tokenize(tok, probe_text(src, text))[0])))
    jobs.sort(key=lambda j: (j[5], j[0]["source_run_id"]))
    if limit:
        jobs = jobs[:limit]
    toks = [j[5] for j in jobs]
    print(f"step10, {weights} weights on {cases_of}'s cases: {len(jobs)} cuts at (ii) over "
          f"{len({j[0]['item_id'] for j in jobs})} questions; tokens median {statistics.median(toks) if toks else 0:,.0f}; "
          f"~{(3 * 32 + 4) * sum(toks) / TOK_PER_S / 60:.0f} min on an A100", flush=True)
    d = step10_dir(out, cases_of, weights)
    (d / "cuts").mkdir(parents=True, exist_ok=True)
    todo = [j for j in jobs if not (d / "cuts" / f"{j[0]['source_run_id']}_ii.json").exists()]
    if dry_run:
        return None
    if todo:
        path = Path(model) if model else model_dir(weights, out)
        dev = kit.pick_device(device)
        m = kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev)
        commit = kit.snapshot(path)[1]
        for i, (c, src, kept_n, text, first, n) in enumerate(todo, 1):
            if _stop["asked"]:
                raise SystemExit("stopped by a signal; the cuts saved so far count, a rerun does the rest")
            it = its[c["item_id"]]
            own, w = it["answer"], src["cue_letter"]
            lay, clean_ids, clean_kind = pt.pair(tok, src, text, own)
            res = pt.patch_cut(m, tok, lay, clean_ids, w, own, len(it["options"]))
            row = {"job": f"{c['source_run_id']}_ii", "source_run_id": c["source_run_id"], "item_id": c["item_id"],
                   "condition": c["condition"], "arm": c.get("arm"), "wording": src["wording"], "repeat": c["repeat"],
                   "cut": "ii", "sentences_kept": kept_n, "n_sentences": c["n_sentences"], "takeover_k": c["takeover_k"],
                   "first_mention": first, "tokens": len(lay["ids"]), "hint_letter": w, "own_letter": own,
                   "clean": clean_kind, "step4_forced_after_deleting_mentions": None, "weights": weights,
                   "cases_of": cases_of, **res, "snapshot_commit": commit, "timestamp_utc": kit.now()}
            kit.write_json(d / "cuts" / f"{row['job']}.json", row)
            print(f"  {i}/{len(todo)} {row['job']}: LD hinted {res['ld_hinted']:+.2f} ({res['top_hinted']}), clean "
                  f"{res['ld_clean']:+.2f}; sanity {'ok' if res['sanity']['ok'] else 'OFF'}", flush=True)
    summary = pt.report(d=d)
    kit.write_json(d / "step10_handoff.json", pt.handoff(summary, full=kit.full_attention_layers(model)))
    return d


# ---------------------------------------------------------------- the swap
def layer_sets(n_layers, readout=READOUT):
    lo, hi = min(readout), max(readout)
    return {"before": list(range(0, lo)), "readout": list(readout), "through": list(range(0, hi + 1)),
            "after": list(range(hi + 1, n_layers))}


@contextmanager
def swapped(a, b, layers):
    """Model a with model b's decoder layers in `layers` (the modules exchanged, and exchanged back after)."""
    la, lb = pt.decoder_layers(a), pt.decoder_layers(b)
    for i in layers:
        la[i], lb[i] = lb[i], la[i]
    try:
        yield a
    finally:
        for i in layers:
            la[i], lb[i] = lb[i], la[i]


def only_layers_differ(a, b):
    """The parameters outside the decoder layers (embeddings, the final norm, the output head) are equal: LoRA
    trained the attention and MLP projections only, so a swap of layers is a swap of what training changed."""
    import torch
    pa, pb = dict(a.named_parameters()), dict(b.named_parameters())
    outside = [k for k in pa if ".layers." not in k]
    return sorted(pa) == sorted(pb) and all(torch.equal(pa[k], pb[k]) for k in outside), outside


def head_masses(model, ids, lay, heads, w, o, letters):
    """(LD, top letter, {head: {hint, letter, control}}) at the answer position: attn_to_hint's capture on one row."""
    import torch

    from finetune.look import attn_to_hint as at
    dev = next(model.parameters()).device
    rows = torch.tensor([lay["answer"]], device=dev)
    sets = {n: torch.tensor(lay[n], device=dev) for n in at.SETS}
    cfg = model.config
    cap = at.Capture(rows, sets, torch.tensor([-1], device=dev), 1, cfg.num_hidden_layers, cfg.num_attention_heads)
    at._ACTIVE.append(cap)
    try:
        ld, probs = pt.forward(model, ids, w, o, letters)
    finally:
        at._ACTIVE.pop()
    return ld, max(probs, key=probs.get), {f"L{layer}H{h}": {n: float(cap.answer[i, layer, h]) for i, n in enumerate(at.SETS)}
                                           for layer, h in heads}


def swap(out, base_model=None, lora_model=None, device="auto", limit=None, dry_run=False, readout=READOUT, heads=None):
    import torch

    from finetune.look import attn_to_hint as at
    heads = heads or at.F12_HEADS
    sources = ensure_sources(out, "base")
    its = {it["question_id"]: it for it in load(items_path(out))}
    cases = chosen_cases(out, "base")
    tok = kit.load_tokenizer(tokenizer_dir())
    d = base_dir(out) / "swap"
    d.mkdir(parents=True, exist_ok=True)
    done = {r["job"] for r in load(d / "swap_rows.jsonl")}
    jobs = [(c, sources[c["source_run_id"]]) for c in cases]
    if limit:
        jobs = jobs[:limit]
    todo = [(c, s) for c, s in jobs if f"{c['source_run_id']}_ii" not in done]
    print(f"swap on base's cases at cut (ii): {len(jobs)} cases, {len(todo)} to go; per case 2 x {2 + len(SWAPS)} "
          f"forwards", flush=True)
    if dry_run or not todo:
        return d
    dev = kit.pick_device(device)
    dt = "bf16" if dev.type != "cpu" else "fp32"
    b = at.install(kit.load_model(base_model or model_dir("base", out), dt, dev))
    lm = at.install(kit.load_model(lora_model or model_dir("lora", out), dt, dev))
    same, outside = only_layers_differ(b, lm)
    if not same:
        raise SystemExit(f"base and LoRA differ outside the decoder layers ({len(outside)} parameters checked): no swap")
    sets = layer_sets(len(pt.decoder_layers(b)), readout)
    for i, (c, src) in enumerate(todo, 1):
        if _stop["asked"]:
            raise SystemExit("stopped by a signal; the cases saved so far count, a rerun does the rest")
        it = its[c["item_id"]]
        own, w_letter = it["answer"], src["cue_letter"]
        kept_n, text, _ = cut_ii(c, src)
        lay, clean_ids, clean_kind = pt.pair(tok, src, text, own)
        ctrl = hs.layout(tok, src, text, it["question"])
        lay = {**lay, "control": ctrl["control"]}
        letter = lambda L: tok(L, add_special_tokens=False)["input_ids"][0]  # noqa: E731
        w, o = letter(w_letter), letter(own)
        letters = [letter(L) for L in pt.LETTERS[:len(it["options"])]]
        hinted, clean = torch.tensor([lay["ids"]], device=dev), torch.tensor([clean_ids], device=dev)
        ld, top, masses = {}, {}, {}
        for name, model in (("base", b), ("lora", lm)):
            h, top[name], masses[name] = head_masses(model, hinted, lay, heads, w, o, letters)
            ld[name] = {"hinted": h, "clean": pt.forward(model, clean, w, o, letters)[0]}
        for name, layers in sets.items():
            with swapped(b, lm, layers) as hy:
                h, probs = pt.forward(hy, hinted, w, o, letters)
                top[f"base+lora_{name}"] = max(probs, key=probs.get)
                ld[f"base+lora_{name}"] = {"hinted": h, "clean": pt.forward(hy, clean, w, o, letters)[0]}
        row = {"job": f"{c['source_run_id']}_ii", "source_run_id": c["source_run_id"], "item_id": c["item_id"],
               "wording": src["wording"], "condition": c["condition"], "arm": c.get("arm"), "repeat": c["repeat"],
               "tokens": len(lay["ids"]), "sentences_kept": kept_n, "hint_letter": w_letter, "own_letter": own,
               "clean": clean_kind, "ld": ld, "te": {k: v["hinted"] - v["clean"] for k, v in ld.items()},
               "top_hinted": top, "heads": masses, "layer_sets": sets, "timestamp_utc": kit.now()}
        append(d / "swap_rows.jsonl", row)
        print(f"  {i}/{len(todo)} {row['job']}: TE base {row['te']['base']:+.2f}, lora {row['te']['lora']:+.2f}, "
              + ", ".join(f"{k[10:]} {row['te'][k]:+.2f}" for k in row["te"] if k.startswith("base+lora_")), flush=True)
    kit.write_json(d / "swap_primary.json", primary(load(d / "swap_rows.jsonl")))
    return d


# ---------------------------------------------------------------- Step 9 (attn_to_hint.py on the sources)
def step9(system, out, model=None, device="auto", limit=None, dry_run=False):
    from finetune.look import attn_to_hint as at
    ensure_sources(out, system)
    d = base_dir(out) / f"step9_{system}"
    path = model or (None if system == "base" else str(model_dir(system, out)))
    res = at.run(path, device, str(d), dry_run, limit, runs_from=str(sources_path(out, system)),
                 items_from=str(items_path(out)), step3_from=str(step3_dir(out, system) / "probes.jsonl"))
    if dry_run:
        return None
    s9 = kit.out_dir("step9", str(d))
    full = kit.full_attention_layers(path)
    rs = at.reduced(s9, full)
    if rs:
        print(f"{at.save_reduced(rs, full, s9 / at.REDUCED)}: {len(rs)} runs", flush=True)
    return res


# ---------------------------------------------------------------- the readings (numbers only)
def ratio_boot(num, den, n=20000, seed=0):
    """sum(num) / sum(den) over questions ({question: values}, the same cases in both), with a 95% percentile
    bootstrap clustered by question; resamples whose denominator isn't positive are dropped and counted."""
    qs = sorted(num, key=str)

    def ratio(sample):
        a, b = sum(sum(num[q]) for q in sample), sum(sum(den[q]) for q in sample)
        return a / b if b > 0 else None
    rng = random.Random(seed)
    vals = [ratio([rng.choice(qs) for _ in qs]) for _ in range(n)]
    ok = sorted(v for v in vals if v is not None)
    if not ok:
        return {"share": ratio(qs), "low": None, "high": None, "questions": len(qs), "dropped_resamples": n}
    return {"share": ratio(qs), "low": ok[int(0.025 * len(ok))], "high": ok[int(0.975 * len(ok)) - 1],
            "questions": len(qs), "dropped_resamples": n - len(ok)}


def clustered_mean(groups):
    if len(groups) < MIN_QUESTIONS:
        return {"mean": statistics.mean(v for vs in groups.values() for v in vs) if groups else None, "low": None,
                "high": None, "questions": len(groups)}
    m, lo, hi = boot_mean(groups)
    return {"mean": m, "low": lo, "high": hi, "questions": len(groups)}


def primary(rows):
    """The pre-registered primary reading (module docstring) from the swap's rows."""
    usable = [r for r in rows if r["te"]["base"] >= MIN_GAP]
    out = {"cases": len(rows), "usable": len(usable), "left_out_small_base_effect": len(rows) - len(usable),
           "questions": len({r["item_id"] for r in usable}), "min_gap": MIN_GAP, "strong": STRONG,
           "lora_still_answers_W": f"{sum(r['top_hinted']['lora'] == r['hint_letter'] for r in rows)} of {len(rows)}",
           "base_answers_W": f"{sum(r['top_hinted']['base'] == r['hint_letter'] for r in rows)} of {len(rows)}"}
    if out["questions"] < MIN_QUESTIONS:
        return {**out, "reading": "too few"}
    by_q = defaultdict(list)
    for r in usable:
        by_q[r["item_id"]].append(r)
    red = lambda name: {q: [r["te"]["base"] - r["te"][name] for r in rs] for q, rs in by_q.items()}  # noqa: E731
    rl = red("lora")
    out["reduction_lora"] = clustered_mean(rl)
    out["share_of_base_effect_removed"] = clustered_mean({q: [(r["te"]["base"] - r["te"]["lora"]) / r["te"]["base"]
                                                             for r in rs] for q, rs in by_q.items()})
    out["layer_split"] = {name: ratio_boot(red(f"base+lora_{name}"), rl) for name in SWAPS}
    if out["reduction_lora"]["low"] is None or out["reduction_lora"]["low"] <= 0:
        return {**out, "reading": "acts in the reasoning (no reduction of the hint's direct effect on base's tokens; "
                                  "the layer split is reported, not read)"}
    s = out["layer_split"]
    through, after = s["through"], s["after"]
    if through["low"] is None or after["low"] is None:
        return {**out, "reading": "unclear"}
    if through["low"] >= STRONG and after["high"] < STRONG:
        where = ("at the readout layers" if s["readout"]["low"] is not None and s["readout"]["low"] >= STRONG else
                 "before them" if s["before"]["low"] is not None and s["before"]["low"] >= STRONG else "spread over 0-23")
        return {**out, "reading": "stops the readout", "where": where}
    if after["low"] >= STRONG and through["high"] < STRONG:
        return {**out, "reading": "acts after the readout"}
    if through["low"] >= STRONG and after["low"] >= STRONG:
        return {**out, "reading": "either half suffices"}
    return {**out, "reading": "unclear"}


def heads_same_tokens(rows):
    """Reported, no decision: F12's heads under LoRA minus base on the same tokens (hint minus control, the mean
    over the three heads), per head too."""
    def a(r, sys_, head=None):
        hs_ = [head] if head else list(r["heads"][sys_])
        return statistics.mean(r["heads"][sys_][h]["hint"] - r["heads"][sys_][h]["control"] for h in hs_)
    by_q = defaultdict(list)
    for r in rows:
        by_q[r["item_id"]].append(r)
    out = {"mean over the three heads": clustered_mean({q: [a(r, "lora") - a(r, "base") for r in rs]
                                                         for q, rs in by_q.items()})}
    for head in (rows[0]["heads"]["base"] if rows else {}):
        out[head] = clustered_mean({q: [a(r, "lora", head) - a(r, "base", head) for r in rs] for q, rs in by_q.items()})
    m = out["mean over the three heads"]
    out["words"] = ("too few" if m["low"] is None else "LoRA's heads look at the hint less" if m["high"] < 0 else
                    "they look more" if m["low"] > 0 else "no change detected")
    return out


def readout_rule(handoff, readout=READOUT, full=None):
    """Set A's rule (Oct 29 00:20) on a handoff summary at cut (ii): replicates / partly / doesn't / too few."""
    cell = handoff["by_cut_type"]["ii"]["all"]
    share = cell.get("drop_share_readout")
    full = full or handoff.get("full_attention_layers") or kit.OLMO3_FULL_LAYERS
    even = len(readout) / len(full)
    if not share or share["low"] is None or cell["questions"] < MIN_QUESTIONS:
        return {"reading": "too few", "questions": cell.get("questions", 0)}
    drops = [(i, c["mean"]) for i, c in enumerate(cell["drop_by_layer"]) if c and c["mean"] is not None]
    top = sorted(i for i, _ in sorted(drops, key=lambda x: -x[1])[:len(readout)])
    a, b = share["low"] > even, top == sorted(readout)
    return {"reading": "replicates" if a and b else "partly" if a or b else "doesn't replicate",
            "share": share, "even_share": even, "largest_drops": top, "questions": cell["questions"]}


def readout(d):
    """Every reading from the numbers-only files copied back into d (a18/ as on Sol)."""
    from finetune.look import attn_to_hint as at
    d = Path(d)
    out = {}
    rows = load(d / "swap" / "swap_rows.jsonl")
    if rows:
        out["primary"] = primary(rows)
        out["heads_same_tokens"] = heads_same_tokens(rows)
    for w, c in (("lora", "lora"), ("lora", "base"), ("base", "base")):
        p = d / f"step10_{w}_on_{c}" / "step10_handoff.json"
        if p.exists():
            h = json.loads(p.read_text())
            key = f"step10 {w} weights on {c}'s cases"
            out[key] = {"rule": readout_rule(h)} if (w, c) == ("lora", "lora") else {
                "share_at_readout (no decision)": h["by_cut_type"]["ii"]["all"].get("drop_share_readout")}
    for s in SYSTEMS:
        p = d / f"step9_{s}" / "step9" / at.REDUCED
        if p.exists():
            out[f"step9 {s}, F32's rule"] = at.fixed_heads(at.load_reduced(p)[0])
    kit.write_json(d / "a18_readout.json", out)
    return out


# ---------------------------------------------------------------- plan (the Mac: numbers only)
def plan(eval_dir=EVAL_DIR):
    """Counts and GPU hours from the numbers-only evaluation rows, and the Sol lines in order."""
    from finetune.look import attn_to_hint as at
    res = {"systems": {}}
    hours = {}
    for system in SYSTEMS:
        rows = [r for r in eval_rows(eval_dir, system)]
        hinted = [r for r in rows if r["wording"] in MAIN and r.get("hint_correct") is False]
        keep = [r for r in rows if kept(r)]
        sure = sure_questions([r for r in keep])
        probe = [r for r in keep if followed(r) and sure.get(r["item_id"])]
        answered = [r for r in keep if r["wording"] != "none" and r.get("parsed_letter")]
        tok = lambda r: (r.get("prompt_tokens") or 0) + (r.get("completion_tokens") or 0)  # noqa: E731
        by_q = Counter(r["item_id"] for r in probe)
        cases = [sum(min(3, round(n * s)) for n in by_q.values()) for s in LATE_SHARE]
        mean_tok = statistics.mean(tok(r) for r in probe) if probe else 0
        cut_tok = statistics.mean((r.get("prompt_tokens") or 0) + CUT_SHARE * (r.get("completion_tokens") or 0)
                                  for r in probe) if probe else 0
        h3 = sum(tok(r) / TOK_PER_S + (r.get("completion_tokens") or 0) / TOKENS_PER_SENTENCE * PROBE_S
                 for r in probe) / 3600 + LOAD_H
        h10 = [n * (3 * 32 + 4) * cut_tok / TOK_PER_S / 3600 + LOAD_H for n in cases]
        h9 = at.estimate([tok(r) for r in answered]) / 3600 + LOAD_H if answered else 0
        res["systems"][system] = {
            "wrong_hint_main_runs": len(hinted), "kept_hinted": sum(r["wording"] != "none" for r in keep),
            "left_out_tool_call_in_final": sum(1 for r in hinted if r["status"] == "ok" and r.get("tool_calls_by_model")),
            "answered_hinted": len(answered), "sure_questions": sum(sure.values()),
            "followed_on_sure_to_probe": len(probe), "by_channel": dict(Counter(r["channel"] for r in probe)),
            "questions_with_a_run_to_probe": len(by_q), "expected_cases": cases,
            "mean_tokens_probed": round(mean_tok), "mean_tokens_at_cut_ii": round(cut_tok),
            "gpu_h": {"step3": round(h3, 2), "step10 (own cases)": [round(x, 2) for x in h10], "step9": round(h9, 2)}}
        hours[system] = (h3, h10, h9)
    bc = res["systems"]["base"]["expected_cases"]
    cut_b = res["systems"]["base"]["mean_tokens_at_cut_ii"]
    hs_ = [n * 2 * (2 + len(SWAPS)) * cut_b / TOK_PER_S / 3600 + 2 * LOAD_H for n in bc]
    est = lambda x: math.ceil(max(x) * 10) / 10 if isinstance(x, (list, tuple)) else math.ceil(x * 10) / 10  # noqa: E731
    jobs = [("step3 --system base", hours["base"][0]), ("step3 --system lora", hours["lora"][0]),
            ("step10 --cases base --weights base", hours["base"][1]), ("step10 --cases base --weights lora", hours["base"][1]),
            ("step10 --cases lora --weights lora", hours["lora"][1]), ("swap", hs_),
            ("step9 --system base", hours["base"][2]), ("step9 --system lora", hours["lora"][2])]
    res["jobs"] = [{"job": j, "hours": est(h), "line": f"cot-disclosure/finetune/gpu/sol/submit.sh a18 --estimate {max(est(h), 0.5):g} "
                    f"-- {j}"} for j, h in jobs]
    res["gpu_h_total"] = round(sum(max(est(h), 0.5) for _, h in jobs), 1)
    return res


def show_plan(res):
    lines = []
    for s, e in res["systems"].items():
        lines.append(f"{s}: {e['wrong_hint_main_runs']} wrong-hint runs (6 main wordings); kept {e['kept_hinted']} "
                     f"({e['left_out_tool_call_in_final']} left out: a tool call in the final answer); answered "
                     f"{e['answered_hinted']}; sure questions {e['sure_questions']}; followed on a sure question "
                     f"{e['followed_on_sure_to_probe']} over {e['questions_with_a_run_to_probe']} questions "
                     f"{e['by_channel']}; expected cases {e['expected_cases'][0]}-{e['expected_cases'][1]}; tokens "
                     f"{e['mean_tokens_probed']:,} a run, {e['mean_tokens_at_cut_ii']:,} at cut (ii); GPU h {e['gpu_h']}")
    lines.append(f"Sol, in order (each after the one before it; {res['gpu_h_total']} GPU-h at most):")
    lines += [f"  {j['line']}" for j in res["jobs"]]
    return "\n".join(lines)


# ---------------------------------------------------------------- command line
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--eval-dir", default=str(EVAL_DIR))
    for name in ("step3", "step10", "swap", "step9"):
        q = sub.add_parser(name)
        q.add_argument("--out", required=True)
        q.add_argument("--device", default="auto")
        q.add_argument("--limit", type=int)
        q.add_argument("--dry-run", action="store_true")
        if name in ("step3", "step9"):
            q.add_argument("--system", choices=SYSTEMS, required=True)
            q.add_argument("--model", help="a local model directory (a test's tiny model)")
    sub.choices["step3"].add_argument("--eval-dir", help="the evaluation's records (default OUT/eval)")
    s10 = sub.choices["step10"]
    s10.add_argument("--cases", choices=SYSTEMS, required=True)
    s10.add_argument("--weights", choices=SYSTEMS, required=True)
    s10.add_argument("--model")
    sw = sub.choices["swap"]
    sw.add_argument("--base-model")
    sw.add_argument("--lora-model")
    r = sub.add_parser("readout")
    r.add_argument("dir")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        res = plan(a.eval_dir)
        print(show_plan(res))
        return res
    if a.cmd == "readout":
        res = readout(a.dir)
        print(json.dumps(res, indent=1, default=str))
        return res
    if not a.dry_run:
        listen()
    if a.cmd == "step3":
        return step3(a.system, a.out, a.model, a.device, a.limit, a.dry_run, a.eval_dir)
    if a.cmd == "step10":
        return step10(a.cases, a.weights, a.out, a.model, a.device, a.limit, a.dry_run)
    if a.cmd == "swap":
        return swap(a.out, a.base_model, a.lora_model, a.device, a.limit, a.dry_run)
    return step9(a.system, a.out, a.model, a.device, a.limit, a.dry_run)


if __name__ == "__main__":
    main()
