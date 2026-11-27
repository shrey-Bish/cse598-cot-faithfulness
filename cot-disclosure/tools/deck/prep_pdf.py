"""Build docs/presentation/final/PREP_GUIDE.pdf from PREP_GUIDE.md: phone-sized pages (293 x 585 pt), readable type.

pandoc turns the markdown into HTML; headless Chrome prints it. Tables are turned into stacked cards so that a phone
page needs no sideways scrolling. Numbers and ids only: it reads the tracked guide and nothing else.

    python3 cot-disclosure/tools/deck/prep_pdf.py
"""
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MD = ROOT / "docs/presentation/final/PREP_GUIDE.md"
PDF = MD.with_suffix(".pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { size: 293pt 585pt; margin: 14pt 14pt 16pt 14pt; }
body { font: 9.6pt/1.38 -apple-system, "Helvetica Neue", Arial, sans-serif; color: #1c1c1c; }
h1 { font-size: 14pt; margin: 0 0 6pt; } h2 { font-size: 12pt; margin: 12pt 0 4pt; border-bottom: 1px solid #8c1d40; }
h2, h3 { break-after: avoid; } p, li { margin: 3pt 0; } ul, ol { padding-left: 14pt; }
code { font: 8.4pt Menlo, monospace; background: #f1f1f1; word-break: break-all; }
blockquote { margin: 4pt 0; padding-left: 7pt; border-left: 3px solid #ffc627; }
hr { border: 0; border-top: 1px solid #ccc; margin: 8pt 0; }
table, thead, tbody, tr, th, td { display: block; width: auto; } thead { display: none; }
tr { border: 1px solid #bbb; border-radius: 4pt; padding: 4pt 6pt; margin: 5pt 0; break-inside: avoid; }
td { padding: 1pt 0; } td:first-child { font-weight: 600; }
td[data-h]::before { content: attr(data-h) ": "; color: #8c1d40; font-weight: 600; }
td:first-child::before { content: ""; }
"""


def main():
    html = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", str(MD)], capture_output=True, text=True, check=True).stdout
    out = []
    for tbl in re.split(r"(?=<table)", html):
        heads = re.findall(r"<th[^>]*>(.*?)</th>", tbl, re.S)
        if heads:
            n = [0]

            def td(m):
                h = heads[n[0] % len(heads)]
                n[0] += 1
                return f'<td data-h="{re.sub("<[^>]+>", "", h)}"{m.group(1)}>'
            tbl = re.sub(r"<td([^>]*)>", td, tbl)
        out.append(tbl)
    page = f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>' + "".join(out)
    with tempfile.TemporaryDirectory() as d:
        h = Path(d) / "guide.html"
        h.write_text(page)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={PDF}", h.as_uri()],
                       check=True, capture_output=True)
    print(PDF)


if __name__ == "__main__":
    main()
