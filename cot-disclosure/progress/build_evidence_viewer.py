"""Build presentation/progress/evidence_viewer.html from saved results only.

  python cot-disclosure/progress/build_evidence_viewer.py

One self-contained HTML page (no external fonts, scripts or images). Every card
shows the run_id and source file it was built from. Texts are real model output,
shortened with "…" where marked; nothing is paraphrased.
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

from common import CODE, LOGS, OUT, PRES, latest, load

import experiments as pilot  # noqa: E402
from detect import COMPILED  # noqa: E402

SUMMARY = CODE.parent / "docs" / "progress" / "RESULTS_SUMMARY.json"
PAGE = PRES / "evidence_viewer.html"
COL = {"private": "#2F6FD6", "final": "#E2622A", "cue": "#C02F79", "neutral": "#8893A6", "correct": "#14826A"}
LABEL = {"olmo3-7b-instruct": "Olmo 3 7B Instruct", "olmo3-7b-think": "Olmo 3 7B Think",
         "olmo3-32b-instruct": "Olmo 3 32B Instruct", "olmo3-32b-think": "Olmo 3 32B Think",
         "qwen3-30b-a3b-instruct-2507": "Qwen3 30B Instruct", "qwen3-30b-a3b-thinking-2507": "Qwen3 30B Thinking"}


def esc(t):
    return html.escape(t or "")


def rel(path):
    return str(Path(path).resolve().relative_to(CODE.parent))


def clip(text, n=600, tail=False):
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return "…" + text[-n:] if tail else text[:n] + "…"


def around(text, rx, width=260):
    """Shortened text around the first match of rx, with every match in the window marked."""
    text = text or ""
    m = rx.search(text)
    if not m:
        return None
    a, b = max(0, m.start() - width), min(len(text), m.end() + width)
    window = text[a:b]
    out, last = [], 0
    for mm in rx.finditer(window):
        out.append(esc(window[last:mm.start()]))
        out.append(f'<mark class="cue">{esc(mm.group(0))}</mark>')
        last = mm.end()
    out.append(esc(window[last:]))
    return ("…" if a > 0 else "") + "".join(out) + ("…" if b < len(text) else "")


def mark_literal(text, needle, cls="cue"):
    e = esc(text)
    n = esc(needle)
    return e.replace(n, f'<mark class="{cls}">{n}</mark>') if needle else e


def prov(rec, path, extra=""):
    return (f'<div class="prov">run_id <code>{esc(rec["run_id"])}</code> · {esc(rel(path))}'
            f'{" · " + extra if extra else ""}</div>')


def card(cid, title, body, note=""):
    return (f'<section class="card" id="{cid}"><h2>{esc(title)}</h2>{body}'
            f'{f"<p class=note>{note}</p>" if note else ""}</section>')


# ---------------------------------------------------------------- cards
def counters(summary):
    files = [OUT / f for f in ("timing.jsonl", "pilot_replay.jsonl", "expA_reviewer.jsonl", "expA_guard.jsonl",
                               "expB_nocue.jsonl", "expB_cued.jsonl", "truncation_sweep.jsonl")]
    recs = [r for f in files for r in load(f)]
    live = [r for r in recs if not r.get("cached")]
    stamps = sorted(datetime.fromisoformat(r["timestamp_utc"]) for r in live)
    start = min(datetime.fromisoformat(r["timestamp_utc"]).timestamp() - (r["latency_s"] or 0) for r in live)
    wall_min = (stamps[-1].timestamp() - start) / 60 if live else 0
    p = summary["pilot"]["calls"]
    tiles = [("Pilot calls (progress round)", f'{p["progress_round_calls"]["num"]:,}'),
             ("Pilot calls failed", str(p["progress_round_failed"]["num"])),
             ("Models", "6"),
             ("Calls today (new, not cached)", f"{len(live):,}"),
             ("Calls today ending in API error", str(sum(r["status"] != "ok" for r in recs))),
             ("Retries today", str(sum(r.get("retries") or 0 for r in recs))),
             ("Wall time today (first to last call)", f"{wall_min:.0f} min")]
    body = '<div class="tiles">' + "".join(
        f'<div class="tile"><div class="num">{esc(v)}</div><div class="lab">{esc(k)}</div></div>' for k, v in tiles) + "</div>"
    body += (f'<div class="prov">sources: {esc(rel(CODE / "results" / "progress.jsonl"))} and '
             f'{len(files)} files in {esc(rel(OUT))} · {len(recs)} records, {len(recs) - len(live)} served from the reply cache</div>')
    return card("card-counters", "Run totals", body)


def pilot_steered(replays):
    reps = [r for r in replays if r.get("purpose") == "steered" and r["model"] == "olmo3-7b-instruct"
            and r.get("pilot_identical")]
    if not reps:
        return card("card-pilot-steered", "Pilot: a steered answer (Olmo 3 7B Instruct)",
                    "<p>No byte-identical replay of a steered Olmo 3 7B Instruct run is available.</p>")
    r = reps[0]
    prompt = r["prompt_messages"][0]["content"]
    hint = pilot.CUE.format(r["cue_letter"])
    q = prompt.split("\n\n")[0]
    stem, opts = q.split("\n(A)")[0], "(A)" + q.split("\n(A)")[1]
    final = r["final_text"]
    mention = around(final, COMPILED["cue"], 220)
    body = (f'<div class="grid2"><div class="panel neutral"><h3>Prompt (puzzle shortened)</h3>'
            f'<p class="mono">{esc(clip(stem, 260))}<br>{esc(opts).replace(chr(10), "<br>")}</p>'
            f'<p class="mono"><mark class="cue">{esc(hint)}</mark></p></div>'
            f'<div class="panel final"><h3>Final answer (end of reply)</h3>'
            f'<p class="mono">{esc(clip(final, 520, tail=True))}</p></div></div>'
            f'<div class="verdict">Hinted (wrong) letter <b class="cue-t">({esc(r["cue_letter"])})</b> · model answered '
            f'<b class="cue-t">({esc(r["parsed_letter"])})</b> · correct answer <b class="ok-t">({esc(r["correct_letter"])})</b></div>')
    if mention:
        body += f'<div class="panel final"><h3>Where the visible reply mentions the suggestion (keyword pre-sort)</h3><p class="mono">{mention}</p></div>'
    note = ("Pilot run (puzzle %d, seed %d), recovered by a seeded replay that matched the stored answer, "
            "character counts and token count exactly." % (r["item_id"], r["repeat"]))
    return card("card-pilot-steered", "Pilot: a wrong hint changes the answer (Olmo 3 7B Instruct)",
                body + prov(r, OUT / "pilot_replay.jsonl"), note)


def two_channels(replays):
    reps = [r for r in replays if r.get("purpose") == "evidence" and r["reasoning_text"]
            and COMPILED["cue"].search(r["reasoning_text"]) and not COMPILED["cue"].search(r["final_text"])]
    if not reps:
        return card("card-two-channels", "Two channels", "<p>No replayed thinking-model run available.</p>")
    r = reps[0]
    priv = around(r["reasoning_text"], COMPILED["cue"], 300)
    body = (f'<div class="grid2"><div class="panel private"><h3>Private reasoning (excerpt): mentions the hint</h3>'
            f'<p class="mono">{priv}</p><div class="small">{len(r["reasoning_text"]):,} characters in total</div></div>'
            f'<div class="panel final"><h3>Final answer (what the user sees): no mention</h3>'
            f'<p class="mono">{esc(clip(r["final_text"], 700, tail=True))}</p>'
            f'<div class="small">{len(r["final_text"]):,} characters in total</div></div></div>'
            f'<div class="verdict">Hint <b class="cue-t">({esc(r["cue_letter"])})</b> · answered '
            f'<b>({esc(r["parsed_letter"])})</b> · correct <b class="ok-t">({esc(r["correct_letter"])})</b></div>')
    note = (f'{LABEL[r["model"]]}, pilot puzzle {r["item_id"]}, wrong hint, seed {r["repeat"]}. '
            f'Replay identical to the stored pilot run: {r.get("pilot_identical")}. Mentions found by keyword pre-sort.')
    return card("card-two-channels", "The same reply, two channels", body + prov(r, OUT / "pilot_replay.jsonl"), note)


def truncation():
    rows = load(OUT / "truncation_sweep.jsonl")
    leaks = [r for r in rows if r.get("leak")]
    capped = [r for r in rows if r.get("capped")]
    if leaks:
        r = leaks[0]
        body = (f'<div class="grid2"><div class="panel private"><h3>Private field</h3><p class="mono">'
                f'{"(empty)" if not r["reasoning_text"] else esc(clip(r["reasoning_text"], 300))}</p></div>'
                f'<div class="panel final"><h3>Visible answer field (shortened)</h3><p class="mono">'
                f'{esc(clip(r["final_text"], 500, tail=True))}</p><div class="small">{len(r["final_text"]):,} characters</div></div></div>'
                f'<div class="verdict">finish_reason <b>{esc(r["finish_reason"])}</b> · cap {r["cap"]:,} tokens · '
                f'stream={r["params"]["stream"]} · parser extracted: <b>{esc(str(r["parsed_letter"]))}</b></div>')
        return card("card-truncation", "Cut off at the token cap: reasoning in the visible answer",
                    body + prov(r, OUT / "truncation_sweep.jsonl"),
                    f"{len(leaks)} of {len(capped)} capped replies in the sweep leaked. Olmo 3 7B Think, pilot puzzle {r['item_id']}.")
    if capped:
        r = capped[0]
        body = (f'<div class="grid2"><div class="panel private"><h3>Private field (end, shortened)</h3><p class="mono">'
                f'{esc(clip(r["reasoning_text"], 500, tail=True))}</p><div class="small">{len(r["reasoning_text"] or ""):,} characters</div></div>'
                f'<div class="panel final"><h3>Visible answer field</h3><p class="mono">{esc(r["final_text"]) or "(empty)"}</p></div></div>'
                f'<div class="verdict">finish_reason <b>{esc(r["finish_reason"])}</b> · cap {r["cap"]:,} tokens · '
                f'stream={r["params"]["stream"]}</div>')
        return card("card-truncation", "Cut off at the token cap", body + prov(r, OUT / "truncation_sweep.jsonl"),
                    f"0 of {len(capped)} capped replies in the sweep leaked into the visible field.")
    return card("card-truncation", "Cut off at the token cap",
                "<p>The truncation sweep was not run. The pilot evidence (10/10 leaks at the 8,000-token cap in the "
                "earlier ladder run; 0/5 at the 16,000-token cap) is metadata only; no text was saved.</p>")


def reviewer():
    rows = [r for r in latest(load(OUT / "expA_reviewer.jsonl")) if r["status"] == "ok"]
    st = [r for r in rows if r["set"] == "steered" and r["arm"] == "c_private"]
    if not st:
        return card("card-reviewer", "Reviewer demo", "<p>No reviewer runs with arm c available.</p>")
    src = st[0]["source_run_id"]
    case = [r for r in rows if r["source_run_id"] == src and r["set"] == "steered"]
    cols = []
    for arm, title in (("b_explanation", "Arm b: question + answer + explanation"),
                       ("c_private", "Arm c: + the answerer's private reasoning")):
        rs = sorted((r for r in case if r["arm"] == arm), key=lambda r: r["repeat"])
        if not rs:
            continue
        verdicts = " ".join(f'<span class="pill {"ok" if r["outcome"] == "corrected" else "bad"}">{esc(r["parsed_letter"] or "?")}</span>'
                            for r in rs)
        cols.append(f'<div class="panel neutral"><h3>{esc(title)}</h3><div>Reviewer verdicts over {len(rs)} repeats: {verdicts}</div>'
                    f'<p class="mono">{esc(clip(rs[0]["final_text"], 650, tail=True))}</p>'
                    f'<div class="small">repeat 0 · run_id {esc(rs[0]["run_id"])}</div></div>')
    r0 = case[0]
    body = (f'<div class="verdict">Answerer {LABEL[r0["answerer_model"]]} took the hint '
            f'<b class="cue-t">({esc(r0["cue_letter"])})</b>; correct is <b class="ok-t">({esc(r0["correct_letter"])})</b>. '
            f'Green = reviewer corrected it, magenta = reviewer kept the hinted answer or picked another wrong one.</div>'
            f'<div class="grid2">{"".join(cols)}</div>')
    return card("card-reviewer", "Reviewer demo (single-digit n): what the reviewer sees changes what it does",
                body + prov(r0, OUT / "expA_reviewer.jsonl", f"source answer run_id {r0['source_run_id']}"),
                "Demo of the pipeline, not a result. Reviewer: Qwen3 30B Instruct. It never saw the hint in arms a to c.")


def expb_tool():
    rows = [r for r in latest(load(OUT / "expB_cued.jsonl")) if r["status"] == "ok" and r["cue_channel"] == "cue_tool"]
    if not rows:
        return card("card-expB-tool", "Experiment B: simulated tool block", "<p>No cued Experiment B runs yet.</p>")
    rows.sort(key=lambda r: (r["parsed_letter"] != r["cue_letter"], r["model"] != "qwen3-30b-a3b-thinking-2507",
                             r["item_id"]))
    r = rows[0]
    prompt = r["prompt_messages"][0]["content"]
    block = re.search(r"\[tool result: lookup_answer_key\]\n\{.*?\}", prompt).group(0)
    q = prompt.split("\n\n")[0]
    priv_hit = around(r["reasoning_text"], COMPILED["cue_tool"], 260) if r["reasoning_text"] else None
    fin_hit = COMPILED["cue_tool"].search(r["final_text"] or "")
    body = (f'<div class="panel neutral"><h3>Prompt (question shortened) with the simulated tool block</h3>'
            f'<p class="mono">{esc(clip(q, 300))}</p><p class="mono"><mark class="cue">{esc(block)}</mark></p></div>'
            f'<div class="grid2"><div class="panel private"><h3>Private reasoning: '
            f'{"mentions the tool block (keyword pre-sort)" if priv_hit else "no tool-block keyword found" if r["reasoning_text"] else "no private channel"}</h3>'
            f'<p class="mono">{priv_hit or esc(clip(r["reasoning_text"], 300))}</p></div>'
            f'<div class="panel final"><h3>Final answer: {"mentions it" if fin_hit else "no tool-block keyword"}</h3>'
            f'<p class="mono">{esc(clip(r["final_text"], 500, tail=True))}</p></div></div>'
            f'<div class="verdict">Cue <b class="cue-t">({esc(r["cue_letter"])})</b> · answered <b>({esc(r["parsed_letter"] or "?")})</b> · '
            f'correct <b class="ok-t">({esc(r["correct_letter"])})</b> · {esc(r["category"])}</div>')
    return card("card-expB-tool", f"Experiment B: a cue in a simulated tool block ({LABEL[r['model']]})",
                body + prov(r, OUT / "expB_cued.jsonl"),
                "Simulated tool block: plain text inside the user turn, not a real tool-role message. MMLU-Pro question "
                f"{r['item_id']}.")


def terminal():
    logs = sorted(LOGS.glob("progress_*.log"))
    keep = re.compile(r"catalog:|projection|select:|cases:|redraw:|classify|finished in|review: |"
                      r"truncation sweep:|retry|ERROR|STOP|nocue: \d+ jobs|cued: \d+ jobs")
    lines = []
    for f in logs:
        for line in f.read_text().splitlines():
            if keep.search(line):
                lines.append(re.sub(r"\s+", " ", line)[:170])
    body = '<pre class="term">' + esc("\n".join(lines[-28:]) or "(no log lines)") + "</pre>"
    return card("card-terminal", "Run log (key lines)", body,
                f"From {esc(', '.join(rel(f) for f in logs))}. The log never contains keys or request headers.")


CSS = """
:root{--private:#2F6FD6;--final:#E2622A;--cue:#C02F79;--neutral:#8893A6;--correct:#14826A;--ink:#1F2430;--muted:#5B6474}
*{box-sizing:border-box}body{margin:0;background:#F4F5F7;color:var(--ink);font:18px/1.5 -apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1500px;margin:0 auto;padding:24px}
h1{font-size:30px;margin:8px 0 4px}.sub{color:var(--muted);margin:0 0 20px}
.card{background:#fff;border-radius:14px;padding:22px 26px;margin:0 0 26px;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.card h2{font-size:24px;margin:0 0 14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.panel{border-radius:10px;padding:14px 16px;margin:10px 0;border-left:6px solid var(--neutral);background:#F7F8FA}
.panel h3{margin:0 0 8px;font-size:18px}
.panel.private{border-color:var(--private);background:#EEF3FC}.panel.private h3{color:var(--private)}
.panel.final{border-color:var(--final);background:#FDF1EB}.panel.final h3{color:#B5471A}
.mono{font:15px/1.5 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word;margin:6px 0}
mark.cue{background:var(--cue);color:#fff;padding:1px 4px;border-radius:4px}
.verdict{font-size:19px;margin:12px 0}.cue-t{color:var(--cue)}.ok-t{color:var(--correct)}
.prov{color:var(--muted);font-size:14px;margin-top:10px}.prov code{font-size:14px}
.note{color:var(--muted);font-size:15px;margin:8px 0 0}.small{color:var(--muted);font-size:14px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
.tile{background:#F7F8FA;border-radius:10px;padding:14px}.tile .num{font-size:36px;font-weight:700}.tile .lab{color:var(--muted);font-size:15px}
.pill{display:inline-block;min-width:34px;text-align:center;border-radius:999px;padding:2px 10px;color:#fff;font-weight:700;margin-right:6px}
.pill.ok{background:var(--correct)}.pill.bad{background:var(--cue)}
pre.term{background:#14171F;color:#D7DCE5;border-radius:10px;padding:16px;font:14px/1.45 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap;word-break:break-word}
@media (max-width:900px){.grid2{grid-template-columns:1fr}}
"""


def main():
    summary = json.loads(SUMMARY.read_text())
    replays = latest(load(OUT / "pilot_replay.jsonl"))
    cards = [counters(summary), pilot_steered(replays), two_channels(replays), truncation(), reviewer(),
             expb_tool(), terminal()]
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><title>CoT Honesty Lab evidence</title>'
            f'<style>{CSS}</style></head><body><main><h1>CoT Honesty Lab: evidence from saved runs</h1>'
            f'<p class="sub">CSE 598 Group 10 · progress round, October 2026 · built by '
            f'cot-disclosure/progress/build_evidence_viewer.py from saved JSONL only</p>{"".join(cards)}</main></body></html>')
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page)
    print(f"wrote {rel(PAGE)} ({len(cards)} cards)")


if __name__ == "__main__":
    main()
