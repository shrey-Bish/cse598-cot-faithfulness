"""The scratch pad's data (tools/demo_template/pad.py, Nov 23): highlights, counts and provenance.

- Highlights are verbatim spans of the recorded text, found by the analysis's own keyword matcher: every span is inside
  its text, its characters match detect.COMPILED, and a run has a span exactly when its own recorded flag says the text
  mentions the hint (the 54: trackB_report.flags(); the fixes and the dial: the run index's mention fields).
- Every count the pad shows is DATA's: pad.counts() resolves, path by path, to the frozen data (the explainer's
  compact(collect()) or the frozen summary named in the path).
- Every run traces to its file and line: the index or log line holds that run.
- The full Sol copy's remote script only reads, and its stream unpacks (sol.py plan_all / unpack_all).
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
              const run = panes[i].rows[PS.idx % panes[i].rows.length];
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
