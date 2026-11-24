"""The scratch pad's data (tools/demo_template/pad.py, Nov 23): highlights, counts and provenance.

- Highlights are verbatim spans of the recorded text, found by the analysis's own keyword matcher: every span is inside
  its text, its characters match detect.COMPILED, and a run has a span exactly when its own recorded flag says the text
  mentions the hint (the 54: trackB_report.flags(); the fixes and the dial: the run index's mention fields).
- Every count the pad shows is DATA's: pad.counts() resolves, path by path, to the frozen data (the explainer's
  compact(collect()) or the frozen summary named in the path).
- Every run traces to its file and line: the index or log line holds that run.
- The full Sol copy's remote script only reads, and its stream unpacks (sol.py plan_all / unpack_all).
- The case finder ("Show me", Nov 23): the index's compact rows are each run's own outcome fields; for every dataset,
  hint, model, version and pattern, the page's count (k of n questions) and its seeded order equal a count made here
  from the per-question files; each run it pins fits the pattern; the verdict line says what the shown runs did; a
  finished pad is scrolled to its first highlighted mention; the page lands on "No fix took the wrong hint", the 120,
  a tool call's reply.
These read results/demo/pad/ (gitignored) and skip when it has not been built.
"""
import base64
import glob
import gzip
import json
import random
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
TPL = CODE / "tools" / "demo_template"
for p in (TPL, CODE, CODE / "progress", CODE / "tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import pad  # noqa: E402
import sol  # noqa: E402

PAD = CODE / "results" / "demo" / "pad"
pytestmark = pytest.mark.skipif(not (PAD / "index.json").exists(), reason="the pad's data is local (pad.py)")


def unblob(b):
    return json.loads(gzip.decompress(base64.b64decode(b)))


def u16slice(t, s, e):
    b = t.encode("utf-16-le")
    return b[2 * s:2 * e].decode("utf-16-le")


@pytest.fixture(scope="module")
def index():
    return json.loads((PAD / "index.json").read_text())


@pytest.fixture(scope="module")
def sample(index):
    """Every drawn question's file, plus 6 more per dataset drawn by a fixed seed."""
    out = {}
    for d in index["datasets"]:
        qs = d["questions"]
        pick = [q for q in qs if q["id"] in set(d["drawn"])]
        rest = [q for q in qs if q not in pick]
        pick += random.Random(f"pad-test:{d['id']}").sample(rest, min(6, len(rest)))
        out[d["id"]] = [json.loads((PAD / q["file"]).read_text()) for q in pick]
    return out


def test_the_index_covers_the_four_datasets(index):
    ids = [d["id"] for d in index["datasets"]]
    assert ids == ["test54", "held30", "fresh120", "review"]
    n = {d["id"]: len(d["questions"]) for d in index["datasets"]}
    assert n["test54"] == 54 and n["held30"] == 30 and n["fresh120"] == 120 and n["review"] >= 173
    for d in index["datasets"]:
        for q in d["questions"]:
            assert (PAD / q["file"]).exists()
            assert q["right"] in {o[0] for o in q["options"]}


def test_highlights_are_verbatim_spans_of_the_recorded_text(sample):
    from detect import COMPILED
    checked = 0
    for ds, files in sample.items():
        if ds == "review":
            continue
        for f in files:
            for r in f["runs"]:
                if not r.get("x"):
                    continue
                x = unblob(r["x"])
                sp = x.get("spans")
                if r["w"] is None:
                    assert sp is None
                    continue
                pat = COMPILED["cue"] if r["src"] == "user" else COMPILED["cue_tool"]
                for key in ("reasoning", "final"):
                    t = x.get(key) or ""
                    n16 = len(t.encode("utf-16-le")) // 2
                    for s, e in sp[key]:
                        assert 0 <= s < e <= n16
                        frag = u16slice(t, s, e)
                        assert frag and frag in t
                        if key == "reasoning":
                            assert pat.search(frag), (r["file"], r["line"], frag)
                # a span exactly when the run's own recorded flag says the text mentions the hint
                if r["out"]["private"] is not None and x.get("reasoning"):
                    assert bool(sp["reasoning"]) == bool(r["out"]["private"]), (r["file"], r["line"])
                if r["out"]["final"] is not None and x.get("final") is not None:
                    assert bool(sp["final"]) == bool(r["out"]["final"]), (r["file"], r["line"])
                checked += 1
    assert checked > 500


def _resolve(frozen, path):
    if ": " in path:
        f, keys = path.split(": ", 1)
        o = json.loads((pad.SUM / f).read_text())
    else:
        o, keys = frozen, path
    base = keys.endswith(".base")
    if base:
        keys = keys[: -len(".base")]
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", keys):
        o = o[int(part[1:-1])] if part.startswith("[") else o[part]
    return ({"k": o["base_k"], "n": o["base_n"]} if base else {"k": o["k"], "n": o["n"]})


def test_every_count_is_the_frozen_datas():
    sys.path[:0] = [str(CODE / "tools"), str(CODE / "progress")]
    import build_demo as bd
    frozen = bd.compact(bd.collect(bd.SUM))
    c = pad.counts(frozen)
    seen = 0

    def walk(o):
        nonlocal seen
        if isinstance(o, dict) and "path" in o and "k" in o:
            got = _resolve(frozen, o["path"])
            assert (got["k"], got["n"]) == (o["k"], o["n"]), o["path"]
            seen += 1
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(c)
    assert seen > 150
    # and the local page carries exactly these counts
    html = (CODE / "results" / "demo" / "demo.html")
    if html.exists():
        m = re.search(r"const DATA = (.*?);\n", html.read_text())
        assert json.loads(m.group(1))["pad"] == json.loads(json.dumps(c))


def _line(path, n):
    p = Path(path)
    op = gzip.open if p.suffix == ".gz" else open
    with op(p, "rt", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if i == n:
                return json.loads(line)
    raise AssertionError(f"{path} has no line {n}")


def _sol_line(src, n):
    for p in [pad.ALL / f for f in ("runs_fixes_120.jsonl.gz", "runs_fixes_30.jsonl.gz", "runs_dial.jsonl.gz", "runs_qwen8b.jsonl.gz",
                                   "runs_gptoss.jsonl.gz", "runs_nemotron.jsonl.gz")] + sorted(pad.SOL.glob("runs_*.jsonl")):
        if not p.exists():
            continue
        op = gzip.open if p.suffix == ".gz" else open
        with op(p, "rt", encoding="utf-8") as f:
            for line in f:
                if src in line[:400]:
                    o = json.loads(line)
                    if o["src"] == src and o["line"] == n:
                        return o["record"]
    raise AssertionError(f"no Sol record {src}:{n}")


def test_every_run_traces_to_its_file_and_line(sample):
    checked = 0
    for ds, files in sample.items():
        for f in files:
            for r in f["runs"][:40]:
                if r["file"].startswith("Sol: "):
                    rec = _sol_line(r["file"][5:], r["line"])
                else:
                    rec = _line(CODE / r["file"], r["line"])
                assert rec.get("item_id") == r["q"], (r["file"], r["line"])
                if r.get("id"):
                    assert rec.get("run_id") == r["id"]
                if r.get("text_file"):
                    assert _sol_line(r["text_file"][5:], r["text_line"]).get("run_id") == r["id"]
                checked += 1
    assert checked > 300


def test_the_full_copy_only_reads_and_unpacks(tmp_path):
    p = sol.plan_all()
    script = sol.REMOTE_ALL.replace("__PLAN__", repr(json.dumps(p)))
    assert not re.search(r"\bopen\([^)]*['\"][wa]", script) and "os.remove" not in script and "shutil" not in script
    assert "Z.write" in script and "subprocess" not in script
    stream = tmp_path / "s.gz"
    with gzip.open(stream, "wt") as f:
        f.write(json.dumps({"kind": "start"}) + "\n")
        f.write(json.dumps({"kind": "run", "group": "dial", "src": "<scratch>/x.jsonl.gz", "line": 3, "record": {"run_id": "r1"}}) + "\n")
        f.write(json.dumps({"kind": "end"}) + "\n")
    m = sol.unpack_all(stream, tmp_path / "all", tmp_path / "none.json")
    assert m["runs"] == {"dial": 1} and m["complete"]
    cut = tmp_path / "cut.gz"
    cut.write_bytes(stream.read_bytes()[:20])
    assert not sol.unpack_all(cut, tmp_path / "all2", tmp_path / "none.json")["complete"]


@pytest.mark.skipif(not (pad.ALL / "manifest.json").exists(), reason="the full Sol copy is unpacked on Ritik's Mac")
def test_the_full_copy_is_complete_against_the_plan():
    m = json.loads((pad.ALL / "manifest.json").read_text())
    assert m["complete"], m.get("cut")
    for g, n in m["expected_ids"].items():
        if n is not None:
            assert m["runs"].get(g, 0) >= n, g


@pytest.fixture(scope="module")
def browser():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


HTML = CODE / "results" / "demo" / "demo.html"


@pytest.mark.skipif(not HTML.exists(), reason="the local build is produced data")
def test_the_pads_marks_are_the_recorded_spans_offline(browser):
    """On the page itself, with the network blocked: on each drawn question of the 120 and the 30, for a wrong tool-call
    hint, then the fine-tuned version beside no fix, the highlighted text in each pad is exactly the run's recorded spans,
    in order; no console error, no request but the file."""
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, offline=True)
    pg = ctx.new_page()
    errors, requests = [], []
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("request", lambda r: requests.append(r.url))
    pg.goto(HTML.as_uri() + "#pad")
    checked = pg.evaluate("""async () => {
      const out = [];
      for (const ds of ["fresh120", "held30"]) {
        const d = PAD.index.datasets.find((x) => x.id === ds);
        for (const q of d.drawn) {
          for (const ver of ["base", "lora"]) {
            await pSetDataset(ds); PS.q = q; await pLoad();
            PS.src = "call"; PS.wd = pDefWord(d, "call"); PS.w = "wrong"; PS.ver = ver; PS.idx = 0; pEnsure(); pRender();
            await new Promise((r) => setTimeout(r, 600)); pFinish(); await new Promise((r) => setTimeout(r, 200));
            const panes = pPanes(), boxes = [...document.querySelectorAll(".padpad")];
            for (let i = 0; i < panes.length; i++) {
              const run = pAt(panes[i]).run;
              if (!run || !run.x) continue;
              const X = await unpack(run.x), t = X.reasoning || "";
              const want = ((X.spans && X.spans.reasoning) || []).map(([s, e]) => t.slice(s, e));
              const got = [...boxes[i].querySelectorAll("mark")].map((m) => m.textContent);
              out.push([ds, q, ver, i, JSON.stringify(want) === JSON.stringify(got), want.length]);
            }
          }
        }
      }
      return out;
    }""")
    ctx.close()
    assert checked and all(c[4] for c in checked), [c for c in checked if not c[4]]
    assert sum(c[5] for c in checked) > 0          # some pads do highlight
    assert not errors, errors[:5]
    assert all(u.startswith(("file:", "data:", "blob:")) for u in requests)


# ---------------- the case finder ----------------
PEXP = {"g3": 0, "a39": 1, "dial": 2}
PATTERNS = {   # key: (the hint's letter, needs a version, the control's test, the version's test) on a run's own outcome
    "took": ("wrong", False, lambda o: o.get("took") is True, None),
    "hid": ("wrong", False, lambda o: o.get("took") is True and o.get("final") is False, None),
    "named": ("wrong", False, lambda o: o.get("took") is True and o.get("final") is True, None),
    "fixed": ("wrong", True, lambda o: o.get("took") is True, lambda o: o.get("took") is False),
    "both": ("wrong", True, lambda o: o.get("took") is True, lambda o: o.get("took") is True),
    "cost": ("right", True, lambda o: o.get("took") is True, lambda o: o.get("took") is False),
}


def fnv(s):
    h = 0x811c9dc5
    for ch in s.encode():
        h = ((h ^ ch) * 0x01000193) & 0xffffffff
    return h


@pytest.fixture(scope="module")
def files(index):
    """Every question's runs (texts dropped), read from the per-question files."""
    out = {}
    for d in index["datasets"]:
        if d["id"] == "review":
            continue
        out[d["id"]] = {e["id"]: [{k: v for k, v in r.items() if k != "x"} for r in json.loads((PAD / e["file"]).read_text())["runs"]]
                        for e in d["questions"]}
    return out


def test_each_runs_outcome_sums_to_the_frozen_counts(files):
    """Every frozen count on the 54, the 30 and the 120 (DATA.pad) is the sum of its runs' own outcomes: k the runs that
    took the hint, n the runs with an outcome (a run with no answer is out of Gate 3's, A39's and the 54's counts, not
    taken in the dial's)."""
    C, n = pad.counts(), 0
    for ds in ("held30", "fresh120"):
        agg = {}
        for rows in files[ds].values():
            for r in rows:
                if r.get("src") in (None, "none"):
                    continue
                src = "call_undeclared" if r["src"] == "call" and (r.get("wd") or "").endswith("_undeclared") else r["src"]
                a = agg.setdefault((r.get("exp"), r["v"], "wrong" if r["w"] else "right", src), [0, 0])
                t = (r.get("out") or {}).get("took")
                a[0] += t is True
                a[1] += t is not None
        for ck, e in C[ds].items():
            exp, v = ck.split(":") if ds == "held30" else ("dial" if ck in ("dial", "dial_off") else "a39", ck)
            for w in ("wrong", "right"):
                for src, o in (e.get(w) or {}).items():
                    if isinstance(o, dict) and "k" in o and (exp, v, w, src) in agg:
                        assert agg[(exp, v, w, src)] == [o["k"], o["n"]], (ds, ck, w, src, agg[(exp, v, w, src)], o)
                        n += 1
    # the 54: per model and setting, the wrong hint's count by source (models with no runs in this build are skipped)
    agg = {}
    for rows in files["test54"].values():
        for r in rows:
            if r.get("w") is True:
                a = agg.setdefault((f"{r['m']}|{r['s']}", r["src"]), [0, 0])
                t = (r.get("out") or {}).get("took")
                a[0] += t is True
                a[1] += t is not None
    for mk, row in C["test54"].items():
        for src, o in row.items():
            if isinstance(o, dict) and "k" in o and (mk, src) in agg:
                assert agg[(mk, src)] == [o["k"], o["n"]], (mk, src, agg[(mk, src)], o)
                n += 1
    assert n > 130


def test_the_finders_rows_are_each_runs_own_outcome_fields(index, files):
    def tri(v):
        return None if v is None else int(bool(v))
    n = 0
    for d in index["datasets"]:
        if d["id"] == "review":
            assert "fk" not in d
            continue
        fk = [tuple(k) for k in d["fk"]]
        for e in d["questions"]:
            runs = files[d["id"]][e["id"]]
            assert len(e["o"]) == len(runs), e["id"]
            for (ki, took, final), r in zip(e["o"], runs):
                o = r.get("out") or {}
                assert fk[ki] == tuple(r.get(f) for f in index["finder"]["key"]) and (took, final) == (tri(o.get("took")), tri(o.get("final")))
                n += 1
    assert n > 25000


def _count(d, runs_by_q, st, key, seed):
    """The finder's count, made here from the per-question files: k questions fit of n with runs, and their order."""
    w, need_v, fb, fx = PATTERNS[key]
    multi_model = len(d["models"]) > 1

    def match(r, v):
        if r.get("v") != v or r.get("kind") is not None:
            return False
        if multi_model and [r.get("m"), r.get("s")] != st["model"]:
            return False
        return r.get("src") == st["src"] and r.get("w") == (w == "wrong") and (not st["wd"] or r.get("wd") == st["wd"])

    def of(rows, v):
        rows = [r for r in rows if match(r, v) and (r.get("out") or {}).get("took") is not None]
        return sorted(rows, key=lambda r: (PEXP.get(r.get("exp"), 0), str(r.get("exp"))))
    n, hits = 0, []
    for qid, rows in runs_by_q.items():
        if not need_v:
            B = of(rows, "base")
            if not B:
                continue
            n += 1
            if any(fb(r.get("out") or {}) for r in B):
                hits.append(qid)
            continue
        V = st["ver"]
        ctrl = "dial_off" if V == "dial" else "base"
        X0 = of(rows, V)
        if not X0:
            continue
        exp = X0[0].get("exp")
        X, B = [r for r in X0 if r.get("exp") == exp], [r for r in of(rows, ctrl) if r.get("exp") == exp]
        if not B:
            continue
        n += 1
        if any(fb(r.get("out") or {}) for r in B) and any(fx(r.get("out") or {}) for r in X):
            hits.append(qid)
    return len(hits), n, sorted(hits, key=lambda q: (fnv(f"{seed}:{q}"), q))


def _combos(index):
    vers = {k for k, _ in pad.VERSIONS} - {"base"}
    for d in index["datasets"]:
        if d["id"] == "review":
            continue
        right = d["id"] in ("held30", "fresh120")
        for mi, m in enumerate(d["models"]):
            for src, wds in d["sources"].items():
                if src == "none":
                    continue
                for wd in [w for w in wds if w] or [None]:
                    st = {"ds": d["id"], "mi": mi, "model": m, "src": src, "wd": wd, "ver": "base"}
                    for key in ("took", "hid", "named"):
                        yield d, st, key
                    for v in sorted(vers & set(d["versions"])):
                        for key in ("fixed", "both") + (("cost",) if right else ()):
                            yield d, {**st, "ver": v}, key


@pytest.mark.skipif(not HTML.exists(), reason="the local build is produced data")
def test_the_finders_counts_equal_the_per_question_outcome_fields(browser, index, files):
    """Every dataset, hint, wording, model, version and pattern: the page's k of n and its seeded order are the ones
    counted here from the per-question files."""
    combos = list(_combos(index))
    want = [_count(d, files[d["id"]], st, key, index["finder"]["seed"]) for d, st, key in combos]
    ctx = browser.new_context(offline=True)
    pg = ctx.new_page()
    pg.goto(HTML.as_uri() + "#pad")
    pg.wait_for_function("typeof PAD_API !== 'undefined' && PAD_API && PS.ds")
    got = pg.evaluate("""(cs) => cs.map(([st, key]) => {
      PS.ds = st.ds; PS.mi = st.mi; PS.src = st.src; PS.wd = st.wd; PS.ver = st.ver;
      const M = pMatches(key);
      return [M.k, M.n, M.order];
    })""", [[{k: st[k] for k in ("ds", "mi", "src", "wd", "ver")}, key] for _, st, key in combos])
    ctx.close()
    assert len(combos) > 500
    # on the 120, where each question has one No fix run per wording (a tool call's reply), the finder's k of n summed
    # over the source's wordings is the frozen count beside the run (DATA.pad); where it has two (pasted), it is not
    frozen, checked = pad.counts()["fresh120"]["base"]["wrong"], []
    for src in ("call", "pasted", "user"):
        per = {}
        for q, rows in files["fresh120"].items():
            for r in rows:
                if r["v"] == "base" and r.get("src") == src and r.get("w") is True and (r.get("out") or {}).get("took") is not None:
                    per[(q, r.get("wd"))] = per.get((q, r.get("wd")), 0) + 1
        if max(per.values()) > 1:
            continue
        ks = [g for (d, st, key), w, g in zip(combos, want, got) if st["ds"] == "fresh120" and st["src"] == src and key == "took"]
        assert [sum(g[0] for g in ks), sum(g[1] for g in ks)] == [frozen[src]["k"], frozen[src]["n"]], src
        checked.append(src)
    assert "call" in checked
    bad = [(st["ds"], st["src"], st["wd"], st["ver"], key, w[:2], g[:2]) for (d, st, key), w, g in zip(combos, want, got) if list(w[:2]) != g[:2] or w[2] != g[2]]
    assert not bad, bad[:5]
    assert sum(w[0] for w in want) > 0 and any(w[0] < w[1] for w in want)


@pytest.fixture(scope="module")
def served():
    import threading
    import serve
    srv, port = serve.make_server(8840)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    yield f"http://127.0.0.1:{port}/demo.html"
    srv.shutdown()


def _verdict(runs, names, w):
    def say(name, r):
        if not r.get("L"):
            return f"{name} gave no answer."
        L = f"({r['L']})"
        t = (r.get("out") or {}).get("took")
        return f"{name} answered {L}." if t is None else f"{name} took it {L}." if t else f"{name} didn\u2019t {L}."
    return f"Same question, same {w} hint: {say(names[0], runs[0])} {say(names[1], runs[1])}"


@pytest.mark.skipif(not HTML.exists(), reason="the local build is produced data")
def test_the_found_runs_fit_and_the_verdict_says_what_they_did(browser, served):
    """Served: the page lands on the finder's first match of "No fix took the wrong hint" (the 120, a tool call's
    reply); for each pattern, the first three questions found each fit it, every pinned run fits it, the verdict line
    across a split is what the shown runs' own fields say, and each finished pad shows its first highlighted mention."""
    names = dict(pad.VERSIONS)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.goto(served + "#pad")
    pg.wait_for_function("PS.state === 'ok' && PS.find === 'took'")
    land = pg.evaluate("() => [PS.ds, PS.src, PS.wd, PS.w, PS.ver, pAt(pPanes()[0]).run.out.took]")
    assert land == ["fresh120", "call", "inserted_study_guide", "wrong", "base", True]
    cases = [("fresh120", None, "took"), ("fresh120", None, "hid"), ("fresh120", None, "named"), ("fresh120", "a40", "fixed"),
             ("fresh120", "a40", "both"), ("fresh120", "a40", "cost"), ("fresh120", "dial", "fixed"), ("held30", None, "took"),
             ("held30", "lora_attn3", "fixed"), ("held30", "lora", "cost"), ("test54", None, "took"), ("test54", None, "named")]
    seen = 0
    for ds, ver, key in cases:
        for fi in range(3):
            o = {"ds": ds, "find": key, "fi": fi, **({"ver": ver} if ver else {})}
            pg.evaluate("(o) => PAD_API.set(o)", o)
            pg.wait_for_function("PS.state === 'ok'")
            pg.evaluate("pFinish()")
            pg.wait_for_timeout(500)
            r = pg.evaluate("""() => {
              const P = PAD_API.pattern(PS.find), M = pMatches(PS.find), ctrl = PS.ver === "dial" ? "dial_off" : "base";
              const panes = pPanes(), shown = panes.map((p) => { const a = pAt(p); return { v: p.v, run: a.run }; });
              const fits = shown.map(({ v, run }) => {
                const f = v === PS.ver && PS.ver !== "base" ? (P.needV ? P.x : null) : (P.needV ? v === ctrl : v === "base") ? P.b : null;
                return f ? f(run.out) : null;
              });
              const pads = [...document.querySelectorAll(".padpad")].map((b) => { const m = b.querySelector("mark");
                return m ? m.offsetTop >= b.scrollTop && m.offsetTop < b.scrollTop + b.clientHeight : null; });
              const vb = document.querySelector(".padverdict");
              return { k: M.k, inOrder: M.order.includes(PS.q), fi: PS.fi, fits, pads, w: PS.w, ver: PS.ver,
                       runs: shown.map((s) => ({ L: s.run.L, out: s.run.out })), verdict: vb ? vb.getAttribute("aria-label") : null };
            }""")
            if not r["k"]:
                continue
            seen += 1
            assert r["inOrder"] and r["fi"] == fi % r["k"], (ds, ver, key, fi, r)
            assert all(f is not False for f in r["fits"]) and any(f for f in r["fits"]), (ds, ver, key, fi, r)
            assert all(x is not False for x in r["pads"]), (ds, ver, key, fi, r["pads"])
            if ver:
                want = _verdict(r["runs"], ["The dial at 1" if ver == "dial" else "No fix", names[ver]], r["w"])
                assert r["verdict"] == want, (r["verdict"], want)
    ctx.close()
    assert seen >= 25
    assert not errors, errors[:5]
