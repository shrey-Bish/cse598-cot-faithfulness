"""Thread 1 on a second model: Track A's Steps 3 and 10 for Qwen3-8B with thinking on, on Track B's runs (Sol).

Why: the mechanism (Steps 3, 9, 10) exists only for Olmo 3 7B Think, where 24 of 32 layers slide over 4,096
tokens and the hint's effect leaves its tokens at three of the 8 full-attention layers (F11, F26). Qwen3-8B
(Qwen/Qwen3-8B @ b968826d) has 36 layers, all full attention, no sliding window: any layer can read the hint,
so a readout at a few layers here is not forced by the architecture.

Runs: Track B's Qwen3-8B, thinking on, 32,768-token budget (results/trackB/sol_vllm.jsonl.gz, with texts, on
Sol only; the Mac has the numbers-only sol_vllm_runs.jsonl). Its 54 questions, in two halves:
  localization   the 24 pilot puzzles (pilot_puzzles): everything chosen is chosen here
  replication    the 30 MMLU-Pro questions (mmlupro_30). They are also Track A's evaluation questions, so
                 they are read only by the rules below, written before any Qwen3-8B probe or patch existed
Channels: tool_real is the primary one (the model called lookup_answer_key; the reply, naming the wrong letter,
came back as a real tool message, just before the final turn's thinking). tool_pasted, system and user are
secondary, on the replication half only (on the puzzles they were followed 1, 1 and 0 times of 72).
A run's prompt is its final call's, rendered from the record's messages with the snapshot's chat template as
the server did (providers/sol_hf.render, enable_thinking): for tool_real the transcript (the question, the
model's call, the tool's reply; the first turn's thinking isn't in it, as it wasn't in what the model saw).
Its token count must equal the server's (usage.input_tokens); a run that differs is left out and counted. The
thinking is rebuilt as "<think>" + the record's reasoning + "</think>" + its reply; each run's server output tokens
minus the rebuilt count is reported (a few tokens either way: the sampled tokens needn't be the canonical ones).

Step 3 (takeover; job qwen8b_step3): every followed thinking-on run, both halves, every channel. Early
answering as in Track A (finetune/look/takeover.py, the same sentence splitter): before the first sentence
(k = 0) and after each sentence k, force the answer: prompt + "<think>" + reasoning up to k +
"\\n</think>\\n\\nAnswer: (" (how Qwen3's template closes a think block; no extra newline when the cut ends with
one). Dense, every sentence, so the takeover point is exact: the whole reasoning runs once and its key/value
cache is reused, each probe adding only the tokens where its text departs from the whole (checked against a
fresh forward at two probes per run). Per probe, each option letter's probability, summed over the tokens
that are the letter alone (as Step 3 read the top 10). Takeover point, "late" (at or after half the
reasoning) and "sure" (all 3 no-hint runs answered and correct) as in Track A. Cases: followed runs with a late
takeover on sure questions.

Step 10 (patching; job qwen8b_step10): Track A's patching (finetune/look/patching.py: patch_cut, its hooks and
sanity checks) on those cases with Qwen3's prompts. Cuts (i) before the first hint mention and (ii) at the
takeover, each closed as above. Clean = the hint's letter W replaced by the own answer O inside the hint only
(one token). LD = logit(W) - logit(O). Restoration by layer at the hint's tokens, the reasoning and the answer
position: 36 x 3 + 4 passes a cut. The handoff (patching.handoff): per layer, the drop in hint-token
restoration, and its share at chosen layers.

The rules (pre-registered: written Oct 30, before any Qwen3-8B probe or patch):
  Localization (puzzles, tool_real, cut (ii), cuts with |LD_clean - LD_hinted| >= 0.5): the chosen layers S
  are the K = 3 layers with the largest mean drop in hint-token restoration (a tie goes to the lower layer).
  Too few: under 5 questions with a usable cut (ii).
  Replication (MMLU-Pro, tool_real, cut (ii)): the share of the drop at S, with a 95% bootstrap clustered by
  question.
    replicates          its lower bound is above K / 36 (S's even share of the 36 full-attention layers),
                        and S are the K largest mean drops on this half
    partly              one of the two
    doesn't replicate   neither
    too few             under 5 questions with a usable cut (ii)
  Reported either way against the puzzles' share at S and Olmo's 0.90 (F11, F26). Descriptive only: whether
  the lower bound is above 0.5, whether each layer of S is within one layer of this half's top K, cut (i),
  the answer position's rise, and the secondary channels with the same numbers.

  python finetune/look/qwen8b_mech.py plan                  # the Mac: counts per half and channel, GPU hours
  python finetune/look/qwen8b_mech.py step3 [--dry-run]     # Sol, GPU: probes, takeover points, cases
  python finetune/look/qwen8b_mech.py step10 [--dry-run]    # Sol, GPU: patching on the cases (resumable)
  python finetune/look/qwen8b_mech.py report                # Sol: Step 10's summary from the saved cuts
  python finetune/look/qwen8b_mech.py readout SUMMARY       # anywhere: the localization, then the replication
On Sol: submit.sh qwen8b_step3 / qwen8b_step10 (finetune/gpu/README.md, "Qwen3-8B: Steps 3 and 10").
Every output ($TRACKA_OUT/qwen8b_step3/, qwen8b_step10/) is numbers only: no prompt or reasoning text.
"""
import argparse
import hashlib
import json
import os
import platform
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))

from common import MIN_QUESTIONS, append, latest, load  # noqa: E402
from detect import COMPILED  # noqa: E402
from finetune.gpu import kit  # noqa: E402
from finetune.look import hint_spans as hs  # noqa: E402
from finetune.look import patching as pt  # noqa: E402
from finetune.look import takeover as tk  # noqa: E402
from tools.answer_key import SYSTEM_HINT, TOOL_SPEC  # noqa: E402

RECORDS = CODE / "results" / "trackB" / "sol_vllm.jsonl.gz"        # with texts: on Sol only
ROWS = CODE / "results" / "trackB" / "sol_vllm_runs.jsonl"         # numbers only: on the Mac too
HELDOUT = CODE / "data" / "progress" / "mmlupro_30.jsonl"          # Track A's evaluation questions
MODEL = "qwen3-8b"
LOCALIZATION, REPLICATION = "pilot_puzzles", "mmlupro_30"
HALVES = {LOCALIZATION: "localization", REPLICATION: "replication"}
CHANNELS = ("tool_real", "tool_pasted", "system", "user")
PRIMARY = "tool_real"
STEP3, STEP10 = "qwen8b_step3", "qwen8b_step10"
THINK_OPEN, THINK_CLOSE = "<think>", "</think>"
ANSWER = "\n\nAnswer: ("
LETTERS = "ABCDEFGHIJ"
K = 3                          # chosen layers (Olmo's readout was 3 layers)
N_LAYERS = 36                  # Qwen3-8B; all full attention
STRONG = 0.5                   # descriptive: most of the drop at the K layers
NO_HINT_RUNS = 3
MAX_PROMPT_MISMATCH = 0.1      # more runs than this whose prompt doesn't reproduce: something systematic, stop
CHECK_TOL = 0.05               # cached vs fresh forward: a larger difference in any letter's probability is reported
HEADROOM = 6 * kit.GiB
KV_BYTES_PER_TOKEN = 2 * 36 * 8 * 128 * 2                          # Qwen3-8B, bf16: 144 KiB
# estimates (assumptions, not measurements; the jobs print their own from the real texts)
TOK_PER_S = 8000               # A100 bf16 forward for an 8B model (Step 10 assumes 9,000 for Olmo's 7B)
PROBE_S = 0.05                 # one cached probe: tokenizing its text + a forward of a few tokens
TOKENS_PER_SENTENCE = 20       # reasoning tokens per sentence of the splitter (MIN_SENTENCE 20 characters)
LATE_SHARE = 0.6               # followed runs on sure questions that are late takeovers (Olmo: 0.54 Test 2, 0.70 set A)
CUT_SHARE = {"i": 0.25, "ii": 0.75}    # of the reasoning, at each cut
ATTENTION = 1.15               # attention's extra cost at a few thousand tokens
LOAD_S = 180
_stop = {"asked": False}


def _on_signal(signum, frame):
    """Slurm's warning (USR1, 5 minutes before the limit): finish the run or cut in flight, start no new one."""
    _stop["asked"] = True


def listen():
    import signal
    for s in (signal.SIGUSR1, signal.SIGTERM):
        signal.signal(s, _on_signal)


# ---------------------------------------------------------------- the runs and the halves
def half_of(set_name):
    return HALVES.get(set_name)


def half_of_item(item_id):
    """Track B's item ids name their set: pilot-<i> (the puzzles), mmlupro-<question_id> (the 30)."""
    return "localization" if str(item_id).startswith("pilot-") else "replication" if str(item_id).startswith(
        "mmlupro-") else None


def heldout_ids():
    """Track B's item ids of the 30 evaluation questions ("mmlupro-<question_id>")."""
    return {f"mmlupro-{json.loads(line)['question_id']}" for line in HELDOUT.read_text().splitlines() if line.strip()}


def qwen_thinking(rows):
    """Track B's finished Qwen3-8B runs with thinking on (records or numbers-only rows), the newest per run."""
    return [r for r in latest(rows) if r.get("model") == MODEL and r.get("thinking") is True and r["status"] == "ok"
            and r.get("experiment", "trackB") == "trackB" and half_of(r["set"])]


def followed(r):
    return r["condition"] != "none" and bool(r.get("parsed_letter")) and r["parsed_letter"] == r["hint_letter"]


def own_and_sure(rows):
    """({question: the majority of its answered no-hint runs, None on a tie}, {question: all 3 answered and correct})."""
    by_q = defaultdict(list)
    for r in rows:
        if r["condition"] == "none":
            by_q[r["item_id"]].append(r)
    own, sure = {}, {}
    for q, rs in by_q.items():
        c = Counter(r["parsed_letter"] for r in rs if r.get("parsed_letter")).most_common()
        own[q] = c[0][0] if c and (len(c) == 1 or c[0][1] > c[1][1]) else None
        sure[q] = len(rs) == NO_HINT_RUNS and all(r.get("parsed_letter") and r["parsed_letter"] == r["correct_letter"]
                                                 for r in rs)
    return own, sure


def messages_of(rec):
    """(messages, tools) of the run's final call: tool_real's transcript (its last turn is the tool's reply)."""
    if rec["condition"] == "tool_real":
        return rec.get("transcript") or rec["prompt_messages"], [TOOL_SPEC]
    return rec["prompt_messages"], None


def source(rec, tok, template):
    """A Track B record as Steps 3 and 10 read it (Step 2b's field names where they exist): rendered_prompt is
    the final call's prompt + "<think>", which the reasoning follows."""
    from providers import sol_hf
    msgs, tools = messages_of(rec)
    prompt = sol_hf.render(tok, template, msgs, tools, thinking=True)
    return {"run_id": rec["run_id"], "timestamp_utc": rec["timestamp_utc"], "item_id": rec["item_id"], "set": rec["set"],
            "half": half_of(rec["set"]), "condition": rec["condition"], "arm": None, "repeat": rec["repeat"],
            "cue_letter": rec["hint_letter"], "parsed_letter": rec["parsed_letter"],
            "correct_letter": rec["correct_letter"], "n_options": rec["n_options"],
            "rendered_prompt": prompt + THINK_OPEN, "reasoning_text": rec.get("reasoning_text") or "",
            "prompt_tokens": len(hs.tokenize(tok, prompt)[0]),
            "server_prompt_tokens": (rec.get("usage") or {}).get("input_tokens"),
            "server_output_tokens": (rec.get("usage") or {}).get("output_tokens"),
            "rebuilt_output_tokens": len(hs.tokenize(tok, THINK_OPEN + (rec.get("reasoning_text") or "") + THINK_CLOSE
                                                     + (rec.get("final_text") or ""))[0]) + 1}     # + <|im_end|>


# ---------------------------------------------------------------- the hint, the forced answer, the pairs
def hint_text(src):
    """The hint as the model saw it, and its letter's offset in it. tool_real: the tool's reply (the same text
    as Track A's inserted tool turn); system: the answer-key note; user and tool_pasted as in Track A."""
    if src["condition"] == "system":
        text = SYSTEM_HINT.format(letter=src["cue_letter"])
        return text, text.index(f"({src['cue_letter']})") + 1
    if src["condition"] == "tool_real":
        return hs.hint_text({**src, "condition": hs.INJECTED})
    return hs.hint_text(src)


def force(cut):
    """What follows a cut reasoning: Qwen3's close of a think block ("\\n</think>\\n\\n", the newline left out
    when the cut ends with one), then "Answer: (" (how its final answers read: "Answer: (X)")."""
    return ("" if cut.endswith("\n") else "\n") + THINK_CLOSE + ANSWER


def probe_text(src, cut):
    return src["rendered_prompt"] + cut + force(cut)


def layout(tok, src, reasoning):
    """hint_spans.layout for Qwen3: token ids of prompt + "<think>" + reasoning + its close, and the spans
    Step 10 patches (every occurrence of the hint; the letter inside it; the reasoning; the answer position)."""
    prompt = src["rendered_prompt"]
    text = probe_text(src, reasoning)
    ids, offsets = hs.tokenize(tok, text)
    hint, at = hint_text(src)
    starts = hs.occurrences(prompt, hint)
    if not starts:
        raise ValueError(f"run {src['run_id']}: the hint text is not in its rendered prompt")
    r0, r1 = len(prompt), len(prompt) + len(reasoning)
    return {"ids": ids, "offsets": offsets, "text": text,
            "hint": sorted({i for s in starts for i in hs.overlapping(offsets, s, s + len(hint))}),
            "letter": sorted({i for s in starts for i in hs.overlapping(offsets, s + at, s + at + 1)}),
            "hint_occurrences": len(starts), "reasoning": [i for i, (a, _) in enumerate(offsets) if r0 <= a < r1],
            "answer": len(ids) - 1}


def pair(tok, src, reasoning, own):
    """patching.pair for Qwen3: (hinted layout, clean token ids, what replaced the letter); the same number of
    tokens, differing only inside the hint (the own letter, else an equal-length filler)."""
    lay = layout(tok, src, reasoning)
    inside = set(lay["hint"])
    hint, at = hint_text(src)
    for fill in (own,) + pt.FILLERS:
        clean = src["rendered_prompt"].replace(hint, hint[:at] + fill + hint[at + 1:])
        ids, _ = hs.tokenize(tok, clean + reasoning + force(reasoning))
        if len(ids) == len(lay["ids"]) and {i for i, (a, b) in enumerate(zip(ids, lay["ids"])) if a != b} <= inside:
            return lay, ids, ("own letter" if fill == own else f"filler {fill!r}")
    raise ValueError(f"run {src['run_id']}: no equal-length clean prompt")


# ---------------------------------------------------------------- Step 3: probes
def letter_token_ids(tok, letters=LETTERS):
    """{letter: [token ids]} of every token that is the letter alone (white space or a ")" around it is
    allowed: Step 3's LETTER_TOKEN)."""
    out = {L: [] for L in letters}
    for i, s in enumerate(tok.batch_decode([[i] for i in range(len(tok))])):
        m = tk.LETTER_TOKEN.fullmatch(s)
        if m and m.group(1) in out:
            out[m.group(1)].append(i)
    return out


def letter_probs(logits, by_letter):
    import torch
    p = torch.softmax(logits.float(), -1)
    return {L: round(float(p[ids].sum()), 6) if ids else 0.0 for L, ids in by_letter.items()}


def shared(a, b):
    """The length of the common prefix of two token lists (binary search over slice comparisons)."""
    lo, hi = 0, min(len(a), len(b))
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if a[:mid] == b[:mid]:
            lo = mid
        else:
            hi = mid - 1
    return lo


def trim(cache, length):
    """Drop the cache's positions from `length` on (a negative crop removes that many, transformers 4 and 5)."""
    extra = cache.get_seq_length() - length
    if extra > 0:
        cache.crop(-extra)


def mention_pattern(condition):
    """Track B's mention words (progress/trackB_report.flags): the user's for a user hint, the tool's otherwise."""
    return COMPILED["cue"] if condition == "user" else COMPILED["cue_tool"]


def probe_curve(model, tok, src, by_letter, check=True):
    """(sentence ends, [{"k", "probs"}] for k = 0..n, check): the forced answer after every sentence. The whole
    reasoning runs once; each probe (the last first) reuses its key/value cache up to where the probe's tokens
    depart from the whole's, and adds the rest. check: the same probes by a fresh forward at k = n and n // 2."""
    import torch
    dev = next(model.parameters()).device
    reasoning = src["reasoning_text"]
    ends = [0] + tk.sentence_ends(reasoning)
    full = hs.tokenize(tok, src["rendered_prompt"] + reasoning)[0]
    letters = {L: by_letter[L] for L in LETTERS[:src["n_options"]]}
    fed = len(full)
    with torch.no_grad():
        cache = model(input_ids=torch.tensor([full], device=dev), use_cache=True, logits_to_keep=1).past_key_values
        curve, texts, last = {}, {}, len(ends) - 1
        for k in range(last, -1, -1):
            ids = hs.tokenize(tok, probe_text(src, reasoning[:ends[k]]))[0]
            c = min(shared(ids, full), cache.get_seq_length(), len(ids) - 1)
            trim(cache, c)
            logits = model(input_ids=torch.tensor([ids[c:]], device=dev), past_key_values=cache, use_cache=True,
                           logits_to_keep=1).logits[0, -1]
            trim(cache, c)
            fed += len(ids) - c
            curve[k] = {"k": k, "probs": letter_probs(logits, letters)}
            if k in (last, last // 2):
                texts[k] = ids
        del cache
        checks = []
        for k in sorted(texts) if check else ():
            logits = model(input_ids=torch.tensor([texts[k]], device=dev), logits_to_keep=1).logits[0, -1]
            fresh = letter_probs(logits, letters)
            checks.append({"k": k, "max_abs_diff": round(max(abs(fresh[L] - curve[k]["probs"][L]) for L in letters), 6),
                           "same_top": tk.top_letter(fresh) == tk.top_letter(curve[k]["probs"])})
    return ends, [curve[k] for k in sorted(curve)], {"tokens_fed": fed, "checks": checks}


def analyse(src, ends, curve, own):
    """Step 3's per-run results for a followed run (takeover.analyse's fields, with Track B's mention words)."""
    reasoning, hint = src["reasoning_text"], src["cue_letter"]
    n = len(ends) - 1
    tops = [tk.top_letter(p["probs"]) for p in curve]
    pat = mention_pattern(src["condition"])
    mentions = [bool(pat.search(reasoning[ends[i]:ends[i + 1]])) for i in range(n)]
    i = tk.takeover_point(tops, hint)
    k = None if i is None else curve[i]["k"]
    first = next((j for j, m in enumerate(mentions) if m), None)
    row = {"kind": "followed", "hint_letter": hint, "own_letter": own, "final_letter": src["parsed_letter"],
           "n_sentences": n, "takeover_k": k, "takeover_frac": None if k is None or not n else k / n,
           "leads_before_reasoning": k == 0, "mention_within_2_before": tk.mention_before(mentions, k) if k else None,
           "first_mention_frac": None if first is None or not n else (first + 1) / n,
           "forced_end_matches_final": tops[-1] == src["parsed_letter"],
           "letter_mass_median": statistics.median(sum(p["probs"].values()) for p in curve)}
    row["takeover_type"] = tk.takeover_type(row)
    return row, mentions


def is_case(row, sure):
    """Track A's default cases: a followed run with a late takeover, on a sure question."""
    return row["kind"] == "followed" and row["takeover_type"] == "late" and bool(sure.get(row["item_id"]))


# ---------------------------------------------------------------- the model and every output's header
def model_and_template(model=None, log_dir=None):
    """(model directory, its commit, the chat template, its sha256). model=None: the pinned Qwen3-8B snapshot in
    $HF_HOME, its files the sizes the download job recorded (progress/sol_trackB.py); a directory: a test's model."""
    import sol_trackB as st
    if model:
        path, commit = kit.snapshot(model)
    else:
        log_dir = log_dir or os.path.join(os.environ.get("TRACKA_OUT", "/scratch/ragarw68/trackA"), "trackb_qwen8b")
        path = st.checked_snapshot(log_dir)
        commit = path.name
    template = st.chat_template(path)
    return path, commit, template, hashlib.sha256(template.encode()).hexdigest()


def header(step, path, commit, tpl_sha, records):
    import sol_trackB as st
    return {"step": step, "timestamp_utc": kit.now(), "model": st.REPO, "revision": st.REVISION,
            "snapshot_dir": str(path), "snapshot_commit": commit, "chat_template_sha256": tpl_sha,
            "records": str(records), "records_sha256": kit.sha256(records), "versions": kit.versions(),
            "gpu": kit.gpu_info(), "code": kit.code_commit(), "slurm": kit.slurm(), "host": platform.node()}


def load_runs(records=None):
    """(the thinking-on records, own answers, sure questions) from Track B's records file (Sol)."""
    path = Path(records or RECORDS)
    if not path.exists():
        raise SystemExit(f"no {path}: Track B's Qwen3-8B records (with texts) are on Sol only")
    recs = qwen_thinking(load(path))
    own, sure = own_and_sure(recs)
    return recs, own, sure


def sources_for(recs, tok, template, tpl_sha, keep):
    """[(record, source)] for the runs `keep` accepts; refuses a template other than the runs' own, and leaves
    out (and counts) runs whose prompt doesn't reproduce: a token count other than the server's, or no hint."""
    out, skipped, differ = [], Counter(), "prompt tokens differ from the server's"
    for r in recs:
        if not keep(r):
            continue
        if r.get("chat_template_sha256") and r["chat_template_sha256"] != tpl_sha:
            raise SystemExit(f"run {r['run_id']} was made with chat template {r['chat_template_sha256'][:12]}, this "
                             f"snapshot's is {tpl_sha[:12]}: its prompt can't be rebuilt")
        src = source(r, tok, template)
        if src["server_prompt_tokens"] is not None and src["server_prompt_tokens"] != src["prompt_tokens"]:
            skipped[differ] += 1
            continue
        if not hs.occurrences(src["rendered_prompt"], hint_text(src)[0]):
            skipped["no hint in the prompt"] += 1
            continue
        if not src["reasoning_text"].strip():
            skipped["no reasoning"] += 1
            continue
        out.append((r, src))
    n = len(out) + sum(skipped.values())
    if n and skipped[differ] > MAX_PROMPT_MISMATCH * n:
        raise SystemExit(f"{skipped[differ]} of {n} prompts don't reproduce the server's token count: the rendering "
                         f"differs from the job's; nothing ran")
    return out, dict(skipped)


def by_half_first(pairs):
    """The localization half first (the puzzles), then the replication half; shortest first within each."""
    return sorted(pairs, key=lambda x: (x[1]["half"] != "localization", len(x[1]["reasoning_text"]), x[1]["run_id"]))


# ---------------------------------------------------------------- Step 3: the job
def step3(model=None, out=None, records=None, limit=None, device="auto", dry_run=False, channels=CHANNELS,
          log_dir=None):
    path, commit, template, tpl_sha = model_and_template(model, log_dir)
    recs, own, sure = load_runs(records)
    tok = kit.load_tokenizer(path)
    pairs, skipped = sources_for(recs, tok, template, tpl_sha, lambda r: followed(r) and r["condition"] in channels)
    pairs = by_half_first(pairs)[:limit] if limit else by_half_first(pairs)
    sizes = [(len(hs.tokenize(tok, s["rendered_prompt"] + s["reasoning_text"])[0]),
              len(tk.sentence_ends(s["reasoning_text"]))) for _, s in pairs]
    toks, sents = sum(t for t, _ in sizes), sum(n + 1 for _, n in sizes)
    est = 2.5 * toks / TOK_PER_S + sents * PROBE_S + LOAD_S
    print(f"{len(pairs)} followed runs ({dict(Counter((s['half'], s['condition']) for _, s in pairs))}); left out: "
          f"{skipped or 'none'}; {sents:,} probes (every sentence), {toks:,} tokens run once + 2 fresh checks a run; "
          f"~{est / 3600:.2f} h on an A100 (assumes {TOK_PER_S:,} tokens/s, {PROBE_S} s a cached probe)", flush=True)
    longest = max((t for t, _ in sizes), default=0)
    dev = kit.pick_device(device)
    need = kit.model_bytes(path, "bf16") + longest * (KV_BYTES_PER_TOKEN + 200 * 1024) + HEADROOM
    print(f"memory: ~{need / kit.GiB:.1f} GiB at the longest run ({longest:,} tokens)")
    if dry_run:
        return None
    kit.check_memory(dev, need, "Qwen3-8B Step 3")
    d = kit.out_dir(STEP3, out)
    probes_path, runs_path = d / "probes.jsonl.gz", d / "takeover_runs.jsonl"
    done = {(r["source_run_id"], r["source_timestamp_utc"]) for r in load(probes_path)}
    todo = [(r, s) for r, s in pairs if (s["run_id"], s["timestamp_utc"]) not in done]
    print(f"{len(pairs) - len(todo)} runs already probed; {len(todo)} to go", flush=True)
    if todo:
        m = kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev)
        by_letter = letter_token_ids(tok)
        t = kit.Timer()
        for i, (r, s) in enumerate(todo, 1):
            if _stop["asked"]:
                raise SystemExit(f"stopped by a signal after {i - 1} runs; a rerun resumes")
            start = time.monotonic()
            ends, curve, stats = probe_curve(m, tok, s, by_letter)
            row, _ = analyse(s, ends, curve, own.get(s["item_id"]))
            ids = {"source_run_id": s["run_id"], "source_timestamp_utc": s["timestamp_utc"], "item_id": s["item_id"],
                   "set": s["set"], "half": s["half"], "condition": s["condition"], "arm": None, "repeat": s["repeat"],
                   "sure": bool(sure.get(s["item_id"])), "prompt_tokens": s["prompt_tokens"],
                   "output_tokens_server_minus_rebuilt": None if s["server_output_tokens"] is None else
                   s["server_output_tokens"] - s["rebuilt_output_tokens"],
                   "reasoning_chars": len(s["reasoning_text"]), "model": MODEL, "snapshot_commit": commit}
            append(probes_path, {**ids, **row, **stats, "seconds": round(time.monotonic() - start, 2), "curve": curve,
                                 "timestamp_utc": kit.now()})
            append(runs_path, {**ids, **row, **stats})
            print(f"  {i}/{len(todo)} {s['set']} {s['condition']} {s['item_id']} run {s['repeat']}: {row['n_sentences']} "
                  f"sentences, takeover {row['takeover_k']} ({row['takeover_type']}); {t() / 60:.1f} min", flush=True)
    return report3(d, own, sure, header(STEP3, path, commit, tpl_sha, records or RECORDS), skipped)


def current_probes(d):
    """The newest probe record per source run."""
    newest = {}
    for r in load(Path(d) / "probes.jsonl.gz"):
        newest[(r["source_run_id"], r["source_timestamp_utc"])] = r
    return list(newest.values())


def report3(d, own, sure, head=None, skipped=None):
    """qwen8b_step3.json (counts, types, checks; numbers only) and cases.jsonl (the cases for Step 10)."""
    rows = current_probes(d)
    cases = sorted((r for r in rows if is_case(r, sure)), key=lambda r: (r["half"] != "localization", r["item_id"],
                                                                         r["condition"], r["repeat"]))
    groups = {}
    for half in ("localization", "replication"):
        for ch in CHANNELS:
            rs = [r for r in rows if r["half"] == half and r["condition"] == ch]
            if not rs:
                continue
            cs = [r for r in cases if r["half"] == half and r["condition"] == ch]
            groups[f"{half} | {ch}"] = {
                "followed_runs_probed": len(rs), "on_sure_questions": sum(r["sure"] for r in rs),
                "takeover_types": dict(Counter(r["takeover_type"] for r in rs)),
                "takeover_types_on_sure": dict(Counter(r["takeover_type"] for r in rs if r["sure"])),
                "cases": len(cs), "case_questions": len({r["item_id"] for r in cs}),
                "forced_end_matches_final": f"{sum(r['forced_end_matches_final'] for r in rs)} of {len(rs)}"}
    checks = [c for r in rows for c in r.get("checks", [])]
    diffs = Counter(r.get("output_tokens_server_minus_rebuilt") for r in rows)
    summary = {**(head or {}), "rule": "cases: followed runs whose takeover comes at or after half the reasoning, on "
                                       "questions whose 3 no-hint runs (thinking on) were all answered and correct",
               "sure_questions": {h: sum(v for q, v in sure.items() if half_of_item(q) == h)
                                  for h in ("localization", "replication")},
               "left_out": skipped, "groups": groups,
               "output_tokens_server_minus_rebuilt": {str(k): v for k, v in sorted(diffs.items(),
                                                                                   key=lambda x: str(x[0]))},
               "cache_check": {"probes": len(checks), "same_top": sum(c["same_top"] for c in checks),
                               "max_abs_diff": max((c["max_abs_diff"] for c in checks), default=None),
                               f"over_{CHECK_TOL}": sum(c["max_abs_diff"] > CHECK_TOL for c in checks)}}
    kit.write_json(Path(d) / "qwen8b_step3.json", summary)
    append(Path(d) / "cases.jsonl", {
        "timestamp_utc": kit.now(), "rule": summary["rule"], "use": "Qwen3-8B Step 10 (finetune/look/qwen8b_mech.py)",
        "cases": [{k: r[k] for k in ("source_run_id", "source_timestamp_utc", "item_id", "set", "half", "condition",
                                     "arm", "repeat", "hint_letter", "own_letter", "n_sentences", "takeover_k",
                                     "takeover_frac", "mention_within_2_before")} for r in cases]})
    for g, v in groups.items():
        print(f"{g}: {v['followed_runs_probed']} probed ({v['on_sure_questions']} on sure questions), types "
              f"{v['takeover_types']}; cases {v['cases']} on {v['case_questions']} questions")
    c = summary["cache_check"]
    print(f"cached vs fresh forward: same top letter in {c['same_top']} of {c['probes']}, largest difference "
          f"{c['max_abs_diff']}; saved {len(cases)} cases to {Path(d) / 'cases.jsonl'}")
    return summary


# ---------------------------------------------------------------- Step 10: the job
PRIORITY = {("localization", PRIMARY): 0, ("replication", PRIMARY): 1}


def jobs10(tok, cases, srcs, halves, channels):
    """One job per (case, cut): the primary channel's localization half first, then its replication half, then
    the secondary channels (the replication half only); shortest first within each."""
    out = []
    for c in cases:
        if c["half"] not in halves or c["condition"] not in channels or (c["half"] == "localization"
                                                                        and c["condition"] != PRIMARY):
            continue
        src = srcs[c["source_run_id"]]
        cs, first = pt.cuts(c, src)
        for name, kept, text in cs:
            n = len(hs.tokenize(tok, probe_text(src, text))[0])
            out.append({"case": c, "cut": name, "kept": kept, "reasoning": text, "first_mention": first, "tokens": n})
    return sorted(out, key=lambda j: (PRIORITY.get((j["case"]["half"], j["case"]["condition"]), 2), j["tokens"],
                                      j["case"]["source_run_id"], j["cut"]))


def read_cases(cases_from):
    saved = load(cases_from)
    if not saved:
        raise SystemExit(f"no cases in {cases_from}: run Step 3 first (submit.sh qwen8b_step3)")
    return saved[-1]["cases"]


def step10(model=None, out=None, records=None, cases_from=None, limit=None, device="auto", dry_run=False,
           halves=("localization", "replication"), channels=CHANNELS, log_dir=None):
    path, commit, template, tpl_sha = model_and_template(model, log_dir)
    recs, own, sure = load_runs(records)
    cases_from = Path(cases_from) if cases_from else kit.out_dir(STEP3, out) / "cases.jsonl"
    cases = read_cases(cases_from)
    tok = kit.load_tokenizer(path)
    want = {c["source_run_id"]: c for c in cases}
    pairs, skipped = sources_for(recs, tok, template, tpl_sha, lambda r: r["run_id"] in want)
    srcs = {s["run_id"]: s for _, s in pairs}
    for c in cases:
        s = srcs.get(c["source_run_id"])
        if s is None or s["timestamp_utc"] != c["source_timestamp_utc"]:
            raise SystemExit(f"case {c['source_run_id']}: not in the records, or its run changed; rerun Step 3")
        if not sure.get(c["item_id"]) or own.get(c["item_id"]) != s["correct_letter"]:
            raise SystemExit(f"case {c['source_run_id']}: question {c['item_id']} is not sure (own answer = key)")
    todo_all = jobs10(tok, cases, srcs, halves, channels)
    if limit:
        todo_all = todo_all[:limit]
    from transformers import AutoConfig
    cfg = AutoConfig.from_pretrained(path, local_files_only=True)
    passes = 3 * cfg.num_hidden_layers + 4
    toks = [j["tokens"] for j in todo_all] or [0]
    est = ATTENTION * passes * sum(toks) / TOK_PER_S + LOAD_S
    print(f"{len({j['case']['source_run_id'] for j in todo_all})} cases, {len(todo_all)} cuts "
          f"({dict(Counter((j['case']['half'], j['case']['condition'], j['cut']) for j in todo_all))}); tokens per cut: "
          f"median {statistics.median(toks):,.0f}, max {max(toks):,}; {passes} passes a cut; ~{est / 3600:.2f} h on an "
          f"A100 (assumes {TOK_PER_S:,} tokens/s)", flush=True)
    longest = max(toks)
    act = longest * cfg.hidden_size * 2 * (cfg.num_hidden_layers + 4) + longest * cfg.intermediate_size * 2 * 3
    need = kit.model_bytes(path, "bf16") + act + HEADROOM
    print(f"memory: ~{need / kit.GiB:.1f} GiB at {longest:,} tokens")
    if dry_run:
        return None
    dev = kit.pick_device(device)
    kit.check_memory(dev, need, "Qwen3-8B Step 10")
    d = kit.out_dir(STEP10, out)
    (d / "cuts").mkdir(exist_ok=True)
    todo = [j for j in todo_all if not (d / "cuts" / f"{pt.job_id(j)}.json").exists()]
    print(f"{len(todo_all) - len(todo)} cuts already done; {len(todo)} to go", flush=True)
    if todo:
        m = kit.load_model(path, "bf16" if dev.type != "cpu" else "fp32", dev)
        t, seen = kit.Timer(), 0
        for i, j in enumerate(todo, 1):
            if _stop["asked"]:
                raise SystemExit(f"stopped by a signal after {i - 1} cuts; a rerun resumes")
            c = j["case"]
            src = srcs[c["source_run_id"]]
            o, w = src["correct_letter"], src["cue_letter"]
            lay, clean_ids, clean_kind = pair(tok, src, j["reasoning"], o)
            res = pt.patch_cut(m, tok, lay, clean_ids, w, o, src["n_options"])
            row = {"job": pt.job_id(j), "source_run_id": c["source_run_id"], "item_id": c["item_id"], "set": c["set"],
                   "half": c["half"], "condition": c["condition"], "arm": None, "repeat": c["repeat"], "cut": j["cut"],
                   "sentences_kept": j["kept"], "n_sentences": c["n_sentences"], "takeover_k": c["takeover_k"],
                   "first_mention": j["first_mention"], "tokens": len(lay["ids"]), "hint_tokens": len(lay["hint"]),
                   "letter_to_answer": lay["answer"] - lay["letter"][0], "hint_letter": w, "own_letter": o,
                   "clean": clean_kind, "step4_forced_after_deleting_mentions": None, **res,
                   "snapshot_commit": commit, "timestamp_utc": kit.now()}
            kit.write_json(d / "cuts" / f"{pt.job_id(j)}.json", row)
            seen += j["tokens"]
            left = sum(x["tokens"] for x in todo[i:])
            print(f"  {i}/{len(todo)} {row['half']} {row['condition']} {row['job']} ({j['tokens']:,} tokens): LD hinted "
                  f"{res['ld_hinted']:+.2f} ({res['top_hinted']}), clean {res['ld_clean']:+.2f} ({res['top_clean']}); "
                  f"sanity {'ok' if res['sanity']['ok'] else 'OFF ' + json.dumps(res['sanity'])}; {t() / 60:.1f} min, "
                  f"~{t() / seen * left / 60:.0f} min left", flush=True)
    if limit:
        return d
    summary = report10(d, header(STEP10, path, commit, tpl_sha, records or RECORDS))
    r = readout(summary)
    kit.write_json(d / "qwen8b_readout.json", r)
    show_readout(r)
    return d


# ---------------------------------------------------------------- Step 10: the summary
def restoration_by_layer(rows, n_layers):
    """patching.report's table for a set of cuts: per cut type and position group, [mean, low, high] per layer."""
    out = {}
    for cut in ("i", "ii"):
        rs = [r for r in rows if r["cut"] == cut]
        usable = [r for r in rs if abs(r["ld_clean"] - r["ld_hinted"]) >= pt.MIN_GAP]
        out[cut] = {"cuts": len(rs), "usable": len(usable), "left_out_small_gap": len(rs) - len(usable)}
        for g in pt.GROUPS:
            means = []
            for layer in range(n_layers):
                groups = defaultdict(list)
                for r in usable:
                    v = pt.restoration(r, g)[layer]
                    if v is not None:
                        groups[r["item_id"]].append(v)
                c = pt.clustered(dict(groups))
                means.append([c["mean"], c["low"], c["high"]] if c else None)
            out[cut][g] = means
    return out


CUT_KEYS = ("job", "source_run_id", "item_id", "set", "half", "condition", "arm", "repeat", "cut", "tokens",
            "hint_tokens", "letter_to_answer", "sentences_kept", "n_sentences", "takeover_k", "first_mention",
            "hint_letter", "own_letter", "clean", "ld_hinted", "ld_clean", "top_hinted", "top_clean", "probs_hinted",
            "probs_clean", "step4_forced_after_deleting_mentions", "snapshot_commit", "ld_patched", "sanity")


def report10(d, head=None):
    """qwen8b_step10_patching.json from the saved cuts (numbers only): every cut's LDs, and restoration by layer
    per half and channel."""
    d = Path(d)
    rows = [json.loads(p.read_text()) for p in sorted((d / "cuts").glob("*.json"))]
    if not rows:
        raise SystemExit(f"no saved cuts in {d}")
    n_layers = len(rows[0]["ld_patched"]["hint"])
    by = {}
    for half in ("localization", "replication"):
        for ch in CHANNELS:
            rs = [r for r in rows if r["half"] == half and r["condition"] == ch]
            if rs:
                by.setdefault(half, {})[ch] = restoration_by_layer(rs, n_layers)
    summary = {**(head or {"step": STEP10}), "snapshot_commits": sorted({r["snapshot_commit"] for r in rows}),
               "n_layers": n_layers, "full_attention_layers": list(range(n_layers)),
               "definitions": {"LD": "logit(W) - logit(O) at the answer position; W = the hint letter, O = the own answer",
                               "restoration": "(LD_patched - LD_hinted) / (LD_clean - LD_hinted)",
                               "left out": f"cuts with |LD_clean - LD_hinted| < {pt.MIN_GAP}",
                               "patch": "copy the clean run's output of one decoder layer into the hinted run, at the "
                                        "hint's tokens, the reasoning, or the answer position",
                               "halves": {LOCALIZATION: "localization", REPLICATION: "replication"}},
               "sanity_ok": f"{sum(r['sanity']['ok'] for r in rows)} of {len(rows)} cuts",
               "restoration_by_layer": by, "cut_ii_note": pt.NOTE.split("; compare Step 4")[0] + ".",
               "cuts": [{k: r.get(k) for k in CUT_KEYS} for r in rows]}
    kit.write_json(d / "qwen8b_step10_patching.json", summary)
    print(f"{len(rows)} cuts; sanity checks ok on {summary['sanity_ok']}; saved {d / 'qwen8b_step10_patching.json'}")
    return summary


# ---------------------------------------------------------------- the rules: localization, then replication
def subset(summary, half, channel):
    """The cuts of one half and channel, as patching.handoff takes a summary."""
    rows = [c for c in summary["cuts"] if c["half"] == half and c["condition"] == channel]
    n = summary["n_layers"]
    by = summary["restoration_by_layer"].get(half, {}).get(channel) or restoration_by_layer(rows, n)
    return {"cuts": rows, "full_attention_layers": summary["full_attention_layers"], "restoration_by_layer": by}


def localization_rows(summary):
    """The localization half's primary cuts; refuses any of the 30 evaluation questions."""
    sub = subset(summary, "localization", PRIMARY)
    held = heldout_ids()
    bad = sorted({c["item_id"] for c in sub["cuts"] if c["item_id"] in held or c["set"] != LOCALIZATION
                  or not str(c["item_id"]).startswith("pilot-")})
    if bad:
        raise SystemExit(f"refusing: the localization half holds questions that aren't pilot puzzles: {bad}")
    return sub


def top_layers(drop_by_layer, k=K):
    """The k layers with the largest mean drop (a tie goes to the lower layer), in layer order."""
    means = [(i, d["mean"]) for i, d in enumerate(drop_by_layer) if d]
    return sorted(i for i, _ in sorted(means, key=lambda x: (-x[1], x[0]))[:k])


def layers_for(drop_by_layer, share=0.8):
    """How many layers (largest mean drops first) hold `share` of the summed mean drop (descriptive)."""
    means = sorted((d["mean"] for d in drop_by_layer if d), reverse=True)
    total, run = sum(means), 0.0
    for n, m in enumerate(means, 1):
        run += m
        if total > 0 and run >= share * total:
            return n
    return None


def localize(summary, k=K, cut="ii"):
    """The pre-registered localization (module docstring): from the puzzles alone, the K layers with the
    largest mean drop in hint-token restoration at cut (ii)."""
    sub = localization_rows(summary)
    layers = summary["full_attention_layers"]
    a = pt.handoff(sub, None, full=layers, readout=())["by_cut_type"][cut]["all"]
    base = {"half": "localization", "set": LOCALIZATION, "channel": PRIMARY, "cut": cut, "k": k,
            "usable_cuts": a["cuts"], "questions": a["questions"], "n_layers": len(layers)}
    if a["questions"] < MIN_QUESTIONS:
        return {**base, "status": "too few", "layers": None}
    chosen = top_layers(a["drop_by_layer"], k)
    at = pt.handoff(sub, None, full=layers, readout=chosen)["by_cut_type"][cut]["all"]
    return {**base, "status": "chosen", "layers": chosen,
            "drop_at_layer": {i: a["drop_by_layer"][i] for i in chosen},
            "share_at_layers": at["drop_share_readout"], "rise_share_at_layers": at["rise_share_readout"],
            "layers_holding_80pct": layers_for(a["drop_by_layer"]),
            "drop_by_layer_mean": [None if x is None else x["mean"] for x in a["drop_by_layer"]]}


def replicate(summary, loc, channel=PRIMARY, cut="ii"):
    """The pre-registered replication (module docstring) on the MMLU-Pro half, with the puzzles' layers."""
    if loc.get("status") != "chosen":
        return {"channel": channel, "cut": cut, "verdict": "no localization", "why": loc.get("status")}
    sub = subset(summary, "replication", channel)
    layers, S = summary["full_attention_layers"], loc["layers"]
    h = pt.handoff(sub, None, full=layers, readout=S)
    a = h["by_cut_type"][cut]["all"]
    out = {"half": "replication", "set": REPLICATION, "channel": channel, "cut": cut, "layers": S,
           "usable_cuts": a["cuts"], "questions": a["questions"]}
    if a["questions"] < MIN_QUESTIONS:
        return {**out, "verdict": "too few"}
    share, even = a["drop_share_readout"], len(S) / len(layers)
    top = top_layers(a["drop_by_layer"], len(S))
    above = share is not None and share["low"] is not None and share["low"] > even
    same = set(top) == set(S)
    verdict = "replicates" if above and same else "partly" if above or same else "doesn't replicate"
    other = h["by_cut_type"]["i" if cut == "ii" else "ii"]["all"]
    return {**out, "verdict": verdict, "share_at_layers": share, "even_share": even, "lower_bound_above_even": above,
            "top_layers_here": top, "same_top_layers": same,
            "descriptive": {"lower_bound_above_0.5": bool(share and share["low"] is not None and share["low"] > STRONG),
                            "each_chosen_within_one_layer_of_top_here": all(any(abs(x - y) <= 1 for y in top) for x in S),
                            "rise_share_at_layers": a["rise_share_readout"],
                            "layers_holding_80pct": layers_for(a["drop_by_layer"]),
                            f"cut_{'i' if cut == 'ii' else 'ii'}_share_at_layers": other.get("drop_share_readout"),
                            "drop_by_layer_mean": [None if x is None else x["mean"] for x in a["drop_by_layer"]]},
            "olmo_reference": "0.90 [0.85, 0.96] at 15/19/23 on Test 2 (F11); 0.90 [0.76, 1.06] on set A (F26)"}


def readout(summary):
    """The localization (puzzles only), then the replication verdict (MMLU-Pro, primary channel) and the
    secondary channels, and the direct path at cut (ii) per half (patching.paths_at_cut_ii)."""
    loc = localize(summary)
    out = {"localization": loc, "replication": replicate(summary, loc),
           "secondary": {ch: replicate(summary, loc, ch) for ch in CHANNELS if ch != PRIMARY
                         and any(c["half"] == "replication" and c["condition"] == ch for c in summary["cuts"])},
           "swap_only_the_prompt_letter": {}}
    for half in ("localization", "replication"):
        sub = subset(summary, half, PRIMARY)
        if sub["cuts"]:
            out["swap_only_the_prompt_letter"][half] = pt.paths_at_cut_ii(sub)["swap_only_the_prompt_letter"]
    return out


def show_readout(r):
    f = lambda c: pt.show_ci(c, sign=False)  # noqa: E731
    loc = r["localization"]
    print(f"\nLocalization (puzzles, {loc['channel']}, cut ({loc['cut']})): {loc['usable_cuts']} usable cuts on "
          f"{loc['questions']} questions: {loc['status']}" + (f"; layers {loc['layers']}, share of the drop there "
                                                              f"{f(loc['share_at_layers'])}; {loc['layers_holding_80pct']} "
                                                              f"layers hold 80%" if loc["layers"] else ""))
    for name, rep in [("Replication", r["replication"])] + [(f"Secondary, {ch}", v) for ch, v in r["secondary"].items()]:
        if "share_at_layers" not in rep:
            print(f"{name} ({rep['channel']}): {rep['verdict']}")
            continue
        print(f"{name} (MMLU-Pro, {rep['channel']}, cut ({rep['cut']})): {rep['verdict'].upper()}: share at "
              f"{rep['layers']} {f(rep['share_at_layers'])} (even share {rep['even_share']:.3f}; above it: "
              f"{rep['lower_bound_above_even']}); the {len(rep['layers'])} largest drops here {rep['top_layers_here']} "
              f"(the same: {rep['same_top_layers']}); {rep['usable_cuts']} cuts, {rep['questions']} questions")
    for half, s in r["swap_only_the_prompt_letter"].items():
        print(f"cut (ii), {half}: swapping only the prompt's letter moves the answer off W in {s['off_W']} of {s['of']}")


# ---------------------------------------------------------------- the plan (the Mac, numbers only)
def plan(rows=None, channels10=CHANNELS):
    """Counts per half and channel from the numbers-only rows, and the GPU estimate of each job (assumptions in
    the constants above; the jobs' --dry-run on Sol counts the real sentences and tokens)."""
    rows = qwen_thinking(load(ROWS) if rows is None else rows)
    own, sure = own_and_sure(rows)
    out = {"questions": {h: len({r["item_id"] for r in rows if half_of(r["set"]) == h}) for h in HALVES.values()},
           "sure_questions": {h: sum(v for q, v in sure.items() if half_of_item(q) == h) for h in HALVES.values()},
           "groups": {}, "assumptions": {"tokens_per_s": TOK_PER_S, "seconds_per_cached_probe": PROBE_S,
                                         "reasoning_tokens_per_sentence": TOKENS_PER_SENTENCE,
                                         "late_share": LATE_SHARE, "cut_share_of_reasoning": CUT_SHARE,
                                         "attention_overhead": ATTENTION, "load_s": LOAD_S}}
    passes = 3 * N_LAYERS + 4
    s3 = s10_up = s10_mid = 0.0
    for half in ("localization", "replication"):
        for ch in CHANNELS:
            f = [r for r in rows if half_of(r["set"]) == half and r["condition"] == ch and followed(r)]
            if not f:
                continue
            on_sure = [r for r in f if sure.get(r["item_id"])]
            probes = sum((r.get("output_tokens") or 0) // TOKENS_PER_SENTENCE + 1 for r in f)
            sec3 = sum(2.5 * ((r.get("input_tokens") or 0) + (r.get("output_tokens") or 0)) for r in f) / TOK_PER_S \
                + probes * PROBE_S
            per_case = [ATTENTION * passes * sum((r.get("input_tokens") or 0) + CUT_SHARE[c] * (r.get("output_tokens")
                                                                                              or 0)
                                                 for c in ("i", "ii")) / TOK_PER_S for r in on_sure]
            used = ch in channels10 and (ch == PRIMARY or half == "replication")
            g = {"followed_runs": len(f), "followed_questions": len({r["item_id"] for r in f}),
                 "followed_on_sure": len(on_sure), "sure_questions_with_followed": len({r["item_id"] for r in on_sure}),
                 "step3_probes_est": probes, "step3_gpu_h": round(sec3 / 3600, 2), "step10": used,
                 "step10_cases_upper": len(on_sure) if used else 0, "step10_cuts_upper": 2 * len(on_sure) if used else 0,
                 "step10_gpu_h_upper": round(sum(per_case) / 3600, 2) if used else 0.0,
                 "step10_gpu_h_central": round(LATE_SHARE * sum(per_case) / 3600, 2) if used else 0.0}
            out["groups"][f"{half} | {ch}"] = g
            s3 += sec3
            s10_up += g["step10_gpu_h_upper"] * 3600
            s10_mid += g["step10_gpu_h_central"] * 3600
    out["step3_gpu_h"] = round((s3 + LOAD_S) / 3600, 2)
    out["step10_gpu_h_upper"] = round((s10_up + LOAD_S) / 3600, 2)
    out["step10_gpu_h_central"] = round((s10_mid + LOAD_S) / 3600, 2)
    return out


def show_plan(p):
    print(f"Qwen3-8B, thinking on: {p['questions']} questions per half; sure (3 of 3 no-hint runs correct): "
          f"{p['sure_questions']}")
    print("| half | channel | followed runs (questions) | on sure questions (questions) | Step 3 probes, est. | "
          "Step 3 GPU h | Step 10 cases / cuts, upper | Step 10 GPU h, upper (central) |")
    print("|---|---|---|---|---|---|---|---|")
    for name, g in p["groups"].items():
        half, ch = name.split(" | ")
        s10 = (f"{g['step10_cases_upper']} / {g['step10_cuts_upper']} | {g['step10_gpu_h_upper']:.2f} "
               f"({g['step10_gpu_h_central']:.2f})") if g["step10"] else "not run | —"
        print(f"| {half} | {ch} | {g['followed_runs']} ({g['followed_questions']}) | {g['followed_on_sure']} "
              f"({g['sure_questions_with_followed']}) | {g['step3_probes_est']:,} | {g['step3_gpu_h']:.2f} | {s10} |")
    a = p["assumptions"]
    print(f"Step 3: ~{p['step3_gpu_h']:.2f} GPU h (every followed run, dense probes on a reused cache). Step 10: "
          f"~{p['step10_gpu_h_upper']:.2f} GPU h if every followed run on a sure question were a case, "
          f"~{p['step10_gpu_h_central']:.2f} at a late share of {a['late_share']}. Assumptions: {a}")


# ---------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan", help="counts and GPU hours from the numbers-only rows (the Mac)")
    for name in ("step3", "step10"):
        p = sub.add_parser(name)
        p.add_argument("--dry-run", action="store_true", help="runs or cuts, tokens, memory, GPU time; no model")
        p.add_argument("--limit", type=int, help="only the N shortest runs (step3) or cuts (step10)")
        p.add_argument("--model", help="a local model directory (a test's tiny model); default: the pinned snapshot")
        p.add_argument("--records", help=f"Track B's records with texts (default {RECORDS.relative_to(CODE)})")
        p.add_argument("--channels", default=",".join(CHANNELS), help="comma-separated hint channels")
        p.add_argument("--device", default="auto")
        p.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
        p.add_argument("--log-dir", help="where the download job's snapshot.json is (default $TRACKA_OUT/trackb_qwen8b)")
        if name == "step10":
            p.add_argument("--cases-from", help="Step 3's cases.jsonl (default BASE/qwen8b_step3/cases.jsonl)")
            p.add_argument("--half", choices=("localization", "replication", "both"), default="both")
    p = sub.add_parser("report", help="Step 10's summary from the saved cuts; no model")
    p.add_argument("--out", help="output base directory (default $TRACKA_OUT)")
    p = sub.add_parser("readout", help="the localization from the puzzles, then the replication on MMLU-Pro")
    p.add_argument("summary", help="a qwen8b_step10_patching.json")
    p.add_argument("--save", help="write the readout here (JSON)")
    a = ap.parse_args(argv)
    if a.cmd == "plan":
        p = plan()
        show_plan(p)
        return p
    if a.cmd == "report":
        d = kit.out_dir(STEP10, a.out)
        s = report10(d)
        r = readout(s)
        kit.write_json(d / "qwen8b_readout.json", r)
        show_readout(r)
        return r
    if a.cmd == "readout":
        r = readout(json.loads(Path(a.summary).read_text()))
        show_readout(r)
        if a.save:
            kit.write_json(a.save, r)
        return r
    channels = tuple(c for c in a.channels.split(",") if c)
    if not a.dry_run:
        listen()
    if a.cmd == "step3":
        return step3(a.model, a.out, a.records, a.limit, a.device, a.dry_run, channels, a.log_dir)
    halves = ("localization", "replication") if a.half == "both" else (a.half,)
    return step10(a.model, a.out, a.records, a.cases_from, a.limit, a.device, a.dry_run, halves, channels, a.log_dir)


if __name__ == "__main__":
    main()
