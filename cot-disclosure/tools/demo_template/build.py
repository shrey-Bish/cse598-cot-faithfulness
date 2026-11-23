"""The demo, one offline page in the answer-sheet look (Nov 22; brief archive/demo_build/DEMO_SPEC.md, design TEMPLATE_GUIDE.md).

  python tools/demo_template/build.py               # -> docs/demo/index.html (tracked: numbers, ids, paths and our own
                                                    #    templates only) and, when results/demo/bench_runs.json exists,
                                                    #    results/demo/demo.html (gitignored: the same page with the
                                                    #    recorded runs and, from method_local.json, the training pairs)
  python tools/demo_template/build.py --web-fonts   # link the fonts from Google instead of embedding them (development)
  python tools/demo_template/build.py --out X --local-out Y

Three parts on one sheet: how we did it (map.js, METHOD), run it (bench.js, RUNS in the local build), what we found
(sheets.js, the template's ten items). DATA is compact.template_data(): the frozen summaries mapped to the template's
keys (tests/test_demo_template.py checks it reproduces data.json). METHOD is method.json (method.py; every fact with its
source). The fonts are embedded from fonts/*.woff2 (Latin subsets; SIL Open Font License, see fonts/README.md).
"""
import argparse
import base64
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CODE = HERE.parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(HERE))
OUT = ROOT / "docs" / "demo" / "index.html"
LOCAL_OUT = CODE / "results" / "demo" / "demo.html"
RUNS = CODE / "results" / "demo" / "bench_runs.json"
METHOD_LOCAL = CODE / "results" / "demo" / "method_local.json"
CSS = ["style.css", "map.css", "bench.css"]
JS = ["marks.js", "sheets.js", "map.js", "bench.js", "shell.js"]
FONTS = [("Archivo", "Archivo.woff2", "100 900", "62% 125%"), ("Archivo Narrow", "ArchivoNarrow.woff2", "400 700", None),
         ("Nanum Pen Script", "NanumPenScript.woff2", "400", None)]
WEB = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
       '<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,400..700&family=Archivo+Narrow:wght@400..700'
       '&family=Nanum+Pen+Script&display=swap" rel="stylesheet">\n')


def js_json(obj):
    """JSON safe inside a <script> element."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True).replace("</", "<\\/")


def font_css():
    out = ["/* Fonts: Archivo, Archivo Narrow (Omnibus-Type) and Nanum Pen Script (Sandoll), each under the SIL Open Font "
           "License 1.1 (https://openfontlicense.org); Latin subsets as served by Google Fonts. See fonts/README.md. */"]
    for fam, fn, weight, stretch in FONTS:
        b64 = base64.b64encode((HERE / "fonts" / fn).read_bytes()).decode()
        st = f"font-stretch:{stretch};" if stretch else ""
        out.append(f'@font-face{{font-family:"{fam}";font-style:normal;font-weight:{weight};{st}font-display:block;'
                   f'src:url(data:font/woff2;base64,{b64}) format("woff2");}}')
    return "\n".join(out)


def page(data, method, runs=None, web_fonts=False):
    css = "\n".join((HERE / f).read_text() for f in CSS if (HERE / f).exists())
    js = "\n".join((HERE / f).read_text() for f in JS if (HERE / f).exists())
    body = (HERE / "body.html").read_text()
    fonts = WEB if web_fonts else ""
    if not web_fonts:
        css = font_css() + "\n" + css
    consts = f"const DATA = {js_json(data)};\nconst METHOD = {js_json(method)};\nconst RUNS = {js_json(runs) if runs else 'null'};\n"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Answer sheet: do thinking modes make chain-of-thought more honest?</title>
{fonts}<style>
{css}
</style>
</head>
<body>
{body}
<script>
{consts}{js}
</script>
</body>
</html>
"""


def load_inputs():
    import compact
    data = compact.template_data()
    mp = HERE / "method.json"
    method = json.loads(mp.read_text()) if mp.exists() else {}
    return data, method


def build(out=OUT, local_out=LOCAL_OUT, runs_path=RUNS, web_fonts=False):
    data, method = load_inputs()
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page(data, method, None, web_fonts))
    written = [out]
    runs = json.loads(Path(runs_path).read_text()) if runs_path and Path(runs_path).exists() else None
    if METHOD_LOCAL.exists():
        runs = dict(runs or {}, method_local=json.loads(METHOD_LOCAL.read_text()))
    if runs:
        lo = Path(local_out)
        lo.parent.mkdir(parents=True, exist_ok=True)
        lo.write_text(page(data, method, runs, web_fonts))
        written.append(lo)
    return written


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--local-out", default=str(LOCAL_OUT))
    ap.add_argument("--runs", default=str(RUNS))
    ap.add_argument("--web-fonts", action="store_true")
    a = ap.parse_args(argv)
    for p in build(a.out, a.local_out, a.runs, a.web_fonts):
        print(p, p.stat().st_size)


if __name__ == "__main__":
    main()
