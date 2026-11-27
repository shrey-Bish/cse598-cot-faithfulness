"""Build the minimal three-step demo page from the pad's local data (output is local and gitignored).

  .venv/bin/python cot-disclosure/tools/demo_min/build.py [--out DIR]

Reads results/demo/pad/index.json and results/demo/pad/fresh120/<question>.json (the pad's data: pad.py), the
Sol copy's run records (results/demo/sol/all/runs_fixes_120.jsonl.gz, for the run ids the pad pairs), and finetune/eval.py's
job for the inserted tool turn. Writes docs/presentation/final/video/demo_min/index.html (gitignored: it holds model text).
No model text in this file: only ids, paths and rules.
"""
import argparse, base64, gzip, html, json, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
CODE = HERE.parents[1]                      # cot-disclosure/
ROOT = CODE.parent
PAD = CODE / "results/demo/pad"
SOLALL = CODE / "results/demo/sol/all/runs_fixes_120.jsonl.gz"
OUT = ROOT / "docs/presentation/final/video/demo_min"
QID, DS, WD = "mmlupro-11784", "fresh120", "inserted_study_guide"
TOOL_MENTION = re.compile(r"\b(?:the )?(?:function|tool) call\b")   # how the reasoning names the tool call
STEM_WORDS = 3                                                       # raw tokens of the stem shown before "…"
# a code, id or path that must never be on screen (compose_c.py's CODE_RE, plus this page's own ids)
CODE_RE = (r"\b(?:F\d{1,2}|FB\d|FC\d|A\d{2}|B\d{1,2}(?:R\d)?|C\d{1,2}|E2|L[346]|T\d{1,2}|Gate \d|Test \d)\b|results/|\.jsonl|\.json"
           r"|mmlupro|\ba40\b|a39|inserted_|\.py\b|\.gz\b|/Users/|docs/|cot-disclosure")


def find_codes(text):
    """Internal codes, ids or paths found in visible text (a list; empty is clean)."""
    return re.findall(CODE_RE, text)


def quote_in(quote, text):
    """True when each piece of `quote` (split at the cut marks) occurs in `text` byte for byte, in order."""
    pos = 0
    for part in [p.strip() for p in quote.split("…")]:
        if not part:
            continue
        k = text.find(part, pos)
        if k < 0:
            return False
        pos = k + len(part)
    return True


def sentence_at(text, start):
    """The sentence holding offset `start`, as record.py's SENT_JS finds it: back to just after the previous
    '. ', '? ', '! ' or a line break; forward to the first . ? ! followed by whitespace (inclusive) or a line break."""
    s = start
    while s > 0:
        c = text[s - 1]
        if c == "\n" or (c.isspace() and s >= 2 and text[s - 2] in ".?!"):
            break
        s -= 1
    while s < start and text[s].isspace():
        s += 1
    e = start
    while e < len(text):
        c = text[e]
        if c in ".?!" and (e + 1 >= len(text) or text[e + 1].isspace()):
            e += 1
            break
        if c == "\n":
            break
        e += 1
    return s, e


def stem_ok(display, original, restored=2):
    """The stem's display (before the cut mark) is the original with exactly `restored` spaces added and nothing else."""
    d = display.split("…")[0].strip()
    dn = d.replace(" ", "")
    if not original.replace(" ", "").startswith(dn):
        return False
    k = c = 0                                   # the original's prefix holding the same non-space characters
    while c < len(dn):
        c += not original[k].isspace(); k += 1
    return d.count(" ") - original[:k].count(" ") == restored


def pad_run(rid, qfile):
    r = next(r for r in qfile["runs"] if r["id"] == rid)
    return r, json.loads(gzip.decompress(base64.b64decode(r["x"])))


def pick(qfile):
    """The pad's runs for this hint (call, study-guide wording, wrong letter), base and a40: expects exactly one each."""
    out = {}
    for v in ("base", "a40"):
        rs = [r for r in qfile["runs"] if r["v"] == v and r["src"] == "call" and r["wd"] == WD and r["w"] is True]
        assert len(rs) == 1, (v, len(rs))
        out[v] = rs[0]
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(OUT)); a = ap.parse_args()
    sys.path.insert(0, str(CODE)); sys.path.insert(0, str(CODE / "tools/demo_template"))
    idx = json.loads((PAD / "index.json").read_text())
    q = next(x for d in idx["datasets"] if d["id"] == DS for x in d["questions"] if x["id"] == QID)
    qfile = json.loads((PAD / DS / f"{QID}.json").read_text())
    runs = pick(qfile)
    base, ft = runs["base"], runs["a40"]
    bx, fx = pad_run(base["id"], qfile)[1], pad_run(ft["id"], qfile)[1]
    opts = dict(q["options"])
    # VERIFY 1: the hint is an inserted tool turn, G, and the key is I
    from finetune import eval as ev
    qq = next(x for x in ev.questions("e2") if x["item_id"] == QID)
    job = ev.job(qq, WD, base["H"], 0)
    tool = next(m for m in job["messages"] if m["role"] == "tool")
    tooljson = json.loads(tool["content"])
    assert any(m.get("tool_calls") for m in job["messages"] if m["role"] == "assistant")
    hint, key = tooljson["expected"], qq["correct"]
    assert hint == base["H"] == ft["H"] and key == base["R"] == q["right"], (hint, key)
    # VERIFY 3: the fine-tuned run's parsed letter and the end of its answer
    fin = ft_final = fx["final"]
    assert ft["L"] == key and re.findall(r"\\boxed\{([A-J])\}", fin)[-1:] == [key], "a40 run does not end on the key"
    assert base["L"] == hint
    # VERIFY 2: the base run's final answer does not mention the tool
    from detect import COMPILED
    assert not COMPILED["cue_tool"].search(bx["final"]), "final answer mentions the tool"
    # the sentence holding the first highlighted mention in the reasoning (as clip A boxes it)
    t = bx["reasoning"]; s0, _ = bx["spans"]["reasoning"][0]
    s, e = sentence_at(t, s0)
    sent = t[s:e].strip()
    assert len(sent.split()) <= 26 and quote_in(sent, t)
    m = [x for x in TOOL_MENTION.finditer(sent)]          # the tool mention highlighted on the card (a pattern, no text)
    assert len(m) == 1, "the sentence should name the tool once"
    k0, mlen = m[0].start(), m[0].end() - m[0].start()
    esc = html.escape
    quote_html = "&ldquo;" + esc(sent[:k0]) + "<mark>" + esc(sent[k0:k0 + mlen]) + "</mark>" + esc(sent[k0 + mlen:]) + "&rdquo;"
    stem0 = " ".join(q["text"].split()[:STEM_WORDS])      # the stem's first words, then "…"
    # the dataset's stem lacks two spaces (a typo); restore exactly those two for display
    words = stem0.split()
    j = max(range(len(words)), key=lambda i: len(words[i]))          # the glued token: three words run together
    w = words[j]; words[j] = w[:3] + " " + w[3:-2] + " " + w[-2:]      # leading 3 and trailing 2 letters are words of their own
    stem = " ".join(words) + " …"
    assert stem_ok(stem, q["text"]), "stem differs from the dataset by more than two restored spaces"
    page = (HERE / "template.html").read_text()
    for k, v in {"STEM": esc(stem), "OPT_HINT": esc(opts[hint]), "OPT_KEY": esc(opts[key]), "HINT": hint, "KEY": key,
                 "BASE_L": base["L"], "FT_L": ft["L"], "QUOTE_HTML": quote_html}.items():
        page = page.replace("{{%s}}" % k, v)
    assert "{{" not in page
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page)
    (out / "facts.json").write_text(json.dumps({"stem": stem, "opt_hint": opts[hint], "opt_key": opts[key], "hint": hint, "key": key,
        "base_letter": base["L"], "ft_letter": ft["L"], "quote": sent, "base_final": bx["final"].strip(), "ft_final_tail": fin.strip()[-80:],
        "base_run": base["id"], "ft_run": ft["id"], "base_reasoning": bx["reasoning"], "ft_reasoning": fx["reasoning"],
        "tool_turn": tool["content"]}, ensure_ascii=False, indent=1))
    print("wrote", out / "index.html", "| hint", hint, "key", key, "| base", base["id"], base["L"], "| a40", ft["id"], ft["L"])
    print("quote:", sent)


if __name__ == "__main__":
    main()
