"""The answer-sheet demo (tools/demo_template/, Nov 22): its data, its draw, its runs, its two builds and its pages.

- DATA is compact() of the frozen summaries: template_data() reproduces the template's data.json exactly, and the page
  embeds exactly that.
- The bench's draw is seeded and reproducible; every recorded run traces to its file and line; the tracked page holds
  no run text.
- The Sol copy's remote script only reads; its stream unpacks.
- In a browser: no request but the file, no console error on any page of any part, no internal code in visible text.
"""
import base64
import gzip
import json
import re
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
TPL = CODE / "tools" / "demo_template"
sys.path.insert(0, str(TPL))
import build as B  # noqa: E402
import compact  # noqa: E402
import draw as D  # noqa: E402
import sol  # noqa: E402

RUNS = CODE / "results" / "demo" / "bench_runs.json"
CODES = re.compile(r"\b(A\d{2}|F\d{1,2}|FB\d|FC\d|B\d{1,2}(R2?)?|C\d{1,2}|E2|L[346]|Gate \d|Track [ABC]|J-(opus|qwen|olmo)|tool_(real|pasted|injected)|prompt_only|lora_\w+|a40\w*)\b")


def page_data(html, name):
    m = re.search(rf"const {name} = (.*?);\n", html)
    return json.loads(m.group(1)) if m and m.group(1) != "null" else None


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("sheet")
    out = B.build(out=d / "index.html", local_out=d / "demo.html", runs_path=RUNS)
    return {"tracked": out[0], "local": out[1] if len(out) > 1 else None}


def test_template_data_reproduces_data_json_exactly():
    assert json.dumps(compact.template_data(), sort_keys=True) == json.dumps(json.loads((TPL / "data.json").read_text()), sort_keys=True)


def test_the_page_embeds_compact_of_the_frozen_summaries(built):
    html = built["tracked"].read_text()
    assert page_data(html, "DATA") == json.loads(json.dumps(compact.template_data()))


def test_the_draw_is_seeded_and_reproducible():
    assert D.draw() == json.loads((TPL / "draw.json").read_text())
    for name, s in D.draw()["sets"].items():
        assert len(s["drawn"]) == s["k"] and len(set(s["drawn"])) == s["k"], name


def test_the_tracked_page_holds_no_run_text_and_embeds_its_fonts(built):
    html = built["tracked"].read_text()
    assert page_data(html, "RUNS") is None
    assert html.count("data:font/woff2;base64,") == 3 and "fonts.googleapis.com" not in html
    if RUNS.exists():
        runs = json.loads(RUNS.read_text())["runs"]
        texts = [r for r in runs if r.get("x")][:40]
        for r in texts:
            x = json.loads(gzip.decompress(base64.b64decode(r["x"])))
            for k in ("reasoning", "final"):
                if x.get(k) and len(x[k]) > 40:
                    assert x[k][:40] not in html


@pytest.mark.skipif(not RUNS.exists(), reason="the recorded runs are produced data, on this Mac only")
def test_every_recorded_run_traces_to_its_file_and_line():
    d = json.loads(RUNS.read_text())
    drawn = {i for s in d["draw"].values() for i in s["drawn"]} | {c.split("|")[0] for c in d["draw"]["c4_bad"]["drawn"]}
    for r in d["runs"]:
        assert r.get("file") and r.get("line") is not None
        assert r["q"] in drawn or r.get("case") in drawn, r["q"]
        f = r.get("text_file") or r["file"]
        if not f.startswith("Sol: ") and isinstance(r["line"], int) and r.get("x"):
            p = CODE / r["file"]
            op = gzip.open if p.suffix == ".gz" else open
            with op(p, "rt") as fh:
                for i, line in enumerate(fh, 1):
                    if i == r["line"]:
                        rec = json.loads(line)
                        assert rec.get("item_id") == r["q"]
                        break
    assert len(d["l6"]) == 84


def test_the_sol_script_only_reads(tmp_path):
    src = sol.REMOTE
    for bad in ("open(p, \"w", "os.remove", "unlink", "shutil", "rmtree", "sbatch", "scancel", "mkdir", ".write("):
        assert bad not in src.replace("sys.stdout.write(", ""), bad
    p = sol.plan()
    assert {g["group"] for g in p["groups"]} == {"fixes_120", "fixes_30", "qwen8b", "gptoss", "nemotron"}
    stream = [json.dumps({"kind": "run", "group": "qwen8b", "src": "<scratch>/x.jsonl.gz", "line": 3, "record": {"run_id": "r", "item_id": "pilot-2"}}),
              json.dumps({"kind": "train_log", "version": "lora", "src": "<scratch>/trackA/train/lora/train_log.jsonl", "lines": [{"step": 1, "loss": 0.5}]}),
              json.dumps({"kind": "sacct", "since": "2026-10-01", "rows": [{"job": "1", "name": "a", "gpus": 1, "seconds": 7200, "gpu_hours": 2.0}]})]
    m = sol.unpack(stream, tmp_path)
    assert m["runs"] == {"qwen8b": 1} and json.loads((tmp_path / "sacct.json").read_text())["gpu_hours"] == 2.0
    assert (tmp_path / "train/lora/train_log.jsonl").exists()


@pytest.fixture(scope="module")
def browser():
    pw = pytest.importorskip("playwright.sync_api")
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.mark.parametrize("which", ["tracked", "local"])
def test_every_page_loads_with_no_request_no_error_and_no_internal_code(browser, built, which):
    path = built[which]
    if path is None:
        pytest.skip("no local build")
    pg = browser.new_page(viewport={"width": 1920, "height": 1080})
    errors, requests = [], []
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("request", lambda r: requests.append(r.url))
    pg.goto(path.as_uri())
    counts = pg.evaluate("PARTS.map((p) => p.pages.length)")
    assert counts[1] == 6 and counts[2] == 10 and counts[0] >= 1
    seen = []
    for part, n in zip(("map", "bench", "found"), counts):
        for i in range(n):
            pg.evaluate(f"INSTANT = true; go('{part}', {i})")
            if part == "bench" and which == "local":
                pg.evaluate("BENCH_ONKEY(new KeyboardEvent('keydown', {key: 'Enter'}))")
                pg.wait_for_timeout(150)
            text = pg.inner_text("#sheet")
            hit = CODES.search(text)
            seen.append((part, i, hit.group(0) if hit else None))
    assert not errors, errors[:5]
    assert all(u.startswith(("file:", "data:", "blob:")) for u in requests), [u for u in requests if not u.startswith(("file:", "data:", "blob:"))][:5]
    assert not [s for s in seen if s[2]], [s for s in seen if s[2]]
