"""The presentation pack (docs/presentation/pack/, Nov 24): every number against its source.

- 02_NUMBERS: each row's "k of n" and intervals are in its finding's section of FINDINGS (or the summary at FINDINGS'
  top, "STORY"), as frozen; each source file exists; in a JSON source, each "k of n" is a k and n pair and each interval
  bound is a number in the file (within rounding, as a rate or in points); a Markdown source holds the number as written.
  Per-run sources (.jsonl) are checked against FINDINGS only.
- Every "k of n" and interval in every pack file is in 02_NUMBERS, FINDINGS or (for the demo's finder counts) TALK_MAP.
- The pack's relative links resolve; the slide figures are 1920 px wide; PACK.pdf is there.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "docs" / "presentation" / "pack"
FIND = {p: (ROOT / p).read_text() for p in ("docs/FINDINGS.md", "docs/trackB/FINDINGS_B.md", "docs/trackC/FINDINGS_C.md")}
pytestmark = pytest.mark.skipif(not (PACK / "02_NUMBERS.md").exists(), reason="the pack is not written yet")

KN = re.compile(r"(\d{1,3}(?:,\d{3})+|\d+) of (\d{1,3}(?:,\d{3})+|\d+)")
_B = r"[+\-]?\d+(?:\.\d+)?(?:e[+\-]?\d+)?%?"
IV = re.compile(r"\[(\s*" + _B + r"\s*,\s*" + _B + r"\s*)\]")   # "[a, b]", numbers only (not link text)
NUM = re.compile(r"[+\-]?\d+(?:\.\d+)?(?:e[+\-]?\d+)?")


def norm(s):
    return re.sub(r"\s+", " ", s.replace("−", "-").replace("–", "-").replace(" ", " ").replace("**", ""))


def sections():
    out = {"STORY": ""}
    for p, t in FIND.items():
        parts = re.split(r"\n(?=## (?:F|FB|FC)\d+\. )", t)
        if p.endswith("docs/FINDINGS.md"):
            out["STORY"] = norm(parts[0])
        for s in parts:
            m = re.match(r"## ((?:F|FB|FC)\d+)\. ", s)
            if m:
                out[m.group(1)] = out.get(m.group(1), "") + norm(s)
    return out


SEC = sections()
ALLF = norm("\n".join(FIND.values()))


def rows():
    out = []
    for line in (PACK / "02_NUMBERS.md").read_text().splitlines():
        if re.match(r"\| N\d+ \|", line):
            c = [x.strip() for x in line.strip().strip("|").split(" | ")]
            out.append({"id": c[0], "claim": c[1], "numbers": c[2], "interval": c[3], "finding": c[4],
                        "sources": [x for x in re.findall(r"`([^`]+)`", c[5]) if re.search(r"\.(json|jsonl|md|csv)$", x)],
                        "status": c[6]})
    return out


ROWS = rows()


def tokens(text):
    t = norm(text)
    return [m.group(0) for m in KN.finditer(t)], ["[" + m.group(1) + "]" for m in IV.finditer(t)]


def walk(o, pairs, nums):
    if isinstance(o, dict):
        # a "k of n" is a k and an n in the same record, whatever the keys (k/n, num/den, answer_only_k/items, off_W/of)
        ints = {int(v) for v in o.values() if isinstance(v, (int, float)) and not isinstance(v, bool) and float(v).is_integer()}
        pairs.update((a, b) for a in ints for b in ints)
        for v in o.values():
            walk(v, pairs, nums)
    elif isinstance(o, list):
        for v in o:
            walk(v, pairs, nums)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        nums.append(float(o))


def near(b, nums):
    d = len(b.split(".")[1].split("e")[0]) if "." in b else 0
    v = float(b)
    tol = 0.5 * 10 ** -d + 1e-9
    return any(abs(x - v) <= tol or abs(100 * x - v) <= tol for x in nums)


def test_the_numbers_file_has_rows_for_every_finding():
    assert len(ROWS) > 120
    have = {r["finding"] for r in ROWS}
    assert {f"F{i}" for i in range(1, 46)} | {"FB1", "FC1", "FC2", "FC3", "FC4"} <= have


def test_every_number_is_in_its_findings_section():
    bad = []
    for r in ROWS:
        if r["status"].startswith("summary"):     # the deck's rows read from a frozen summary: checked against the JSON
            continue
        text = SEC.get(r["finding"], "") + " " + SEC["STORY"]
        kn, iv = tokens(" ".join((r["claim"], r["numbers"], r["interval"])))
        for t in kn + iv:
            if t not in text:
                bad.append((r["id"], r["finding"], t))
    assert not bad, bad


def test_every_source_exists():
    missing = [(r["id"], s) for r in ROWS for s in r["sources"] if not (ROOT / s).exists()]
    assert all(r["sources"] for r in ROWS)
    assert not missing, missing


S = ROOT / "cot-disclosure" / "results" / "summaries"


def _l6():
    return json.loads((S / "trackA/labels/l6_report.json").read_text())


def _b20_readings(where):
    o, out = json.loads((S / "trackB/b20_report.json").read_text()), []
    for m in o.values():
        for st in (m.get("settings") or {}).values() if isinstance(m, dict) else ():
            for ch in ((st.get(where) or {}).get("R2_tool_or_authority") or {}).values():
                out.append(ch.get("reading"))
    return out


# numbers a summary holds as parts, not as one record: each recomputed here from its source
DERIVED = {
    ("F45", "82 of 84"): lambda: round(_l6()["kappa"]["overall"]["agreement"] * _l6()["kappa"]["overall"]["rows"]) == 82,
    ("F45", "83 of 84"): lambda: _l6()["keyword_agrees"]["lora"]["k"] + _l6()["keyword_agrees"]["prompt_only"]["k"] == 83
    and _l6()["rows"] == 84,
    ("FB1", "5 of 10"): lambda: (lambda r: len(r) == 10 and r.count("tool beyond authority") == 5
                                 and r.count("authority moves it more") == 1)(_b20_readings("budget_32768")),
}
# counted from per-run rows (no numbers-only summary holds them): checked against FINDINGS only
PER_RUN = {("F16", "111 of 147"), ("F1", "[-2, +40] (-2)"), ("F1", "[-2, +40] (+40)"), ("F13", "7 of 19")}
# FINDINGS' number differs from its source in the last place (frozen as written; the pack says so)
KNOWN = {("F42", "[1.39, 4.82] (4.82)"): "a41_readout.json holds 4.8148 (4.81); FINDINGS writes 4.82"}


def source_check(r):
    """The row's numbers in its own source files: (problems, checked)."""
    js = [s for s in r["sources"] if s.endswith(".json")]
    md = [s for s in r["sources"] if s.endswith((".md", ".csv"))]
    if not js and not md:
        return [], False
    pairs, nums, text = set(), [], ""
    for s in js:
        walk(json.loads((ROOT / s).read_text()), pairs, nums)
    for s in md:
        text += norm((ROOT / s).read_text())
    kn, iv = tokens(" ".join((r["claim"], r["numbers"], r["interval"])))
    bad = []
    for t in kn:
        k, n = (int(x.replace(",", "")) for x in KN.match(t).groups())
        d = DERIVED.get((r["finding"], t))
        if d is not None:
            if not d():
                bad.append(t + " (derived)")
        elif (k, n) not in pairs and t not in text:
            bad.append(t)
    for t in iv:
        for b in NUM.findall(t):
            if not near(b, nums) and t not in text:
                bad.append(f"{t} ({b})")
    return bad, True


def test_the_decks_summary_rows_match_their_json_exactly():
    """The rows read from the frozen summaries for the final deck: each k of n is one record's k and n, and each
    interval is that record's stored Wilson bounds, rounded (Nov 25)."""
    rows = [r for r in ROWS if r["status"].startswith("summary")]
    assert len(rows) >= 13
    for r in rows:
        line = [l for l in (PACK / "02_NUMBERS.md").read_text().splitlines() if l.startswith(f"| {r['id']} |")][0]
        src, key = re.search(r"`([^`]+\.json)` \(key `([^`]+)`\)", line).groups()
        o = json.loads((ROOT / src).read_text())
        for k in key.replace("\\|", "|").split("/"):
            o = o[k]
        kn = KN.findall(norm(r["numbers"]))
        ivs = [[float(x) for x in NUM.findall(t)] for t in tokens(r["interval"])[1]]
        if r["claim"].startswith("Across models"):   # the strip: the user's channel, then the tool's
            recs = [o[c]["following"] for c in ("user", "tool_real" if "own tool call" in r["claim"] else "tool_injected")]
        else:                                        # one record
            recs = [o]
        assert len(recs) == len(kn) == len(ivs), r["id"]
        for rec, (k, n), (lo, hi) in zip(recs, kn, ivs):
            assert (rec["k"], rec["n"]) == (int(k), int(n)), r["id"]
            assert [round(100 * x) for x in rec["wilson"]] == [lo, hi], r["id"]


def test_the_decks_rates_are_their_k_of_n_rounded():
    """Slide 6 shows consistency training's rates as percents: each is its k of n (FINDINGS'), rounded (Nov 25)."""
    rows = [r for r in ROWS if r["status"].startswith("rates")]
    assert rows
    for r in rows:
        pairs = re.findall(r"(\d+) of (\d+) \((\d+)%\)", r["numbers"])
        assert len(pairs) == 4, r["id"]
        assert all(round(100 * int(k) / int(n)) == int(p) for k, n, p in pairs), r["id"]


def test_every_number_matches_its_source_file():
    bad, checked, per_run, known = [], 0, set(), set()
    for r in ROWS:
        b, c = source_check(r)
        checked += c
        for x in b:
            if (r["finding"], x) in PER_RUN and any(s.endswith(".jsonl") for s in r["sources"]):
                per_run.add((r["finding"], x))
            elif (r["finding"], x) in KNOWN:
                known.add((r["finding"], x))
            else:
                bad.append((r["id"], r["finding"], x))
    assert known == set(KNOWN), "a known mismatch is gone: update KNOWN and the pack's note"
    assert checked > 100
    assert not bad, bad


def pack_files():
    return sorted(p for p in PACK.glob("*.md"))


def test_every_number_in_the_pack_traces_to_the_numbers_file_or_findings():
    allowed = norm((PACK / "02_NUMBERS.md").read_text()) + ALLF + norm((ROOT / "docs/presentation/TALK_MAP.md").read_text())
    bad = []
    for p in pack_files():
        kn, iv = tokens(p.read_text())
        bad += [(p.name, t) for t in kn + iv if t not in allowed]
    assert len(pack_files()) >= 12, [p.name for p in pack_files()]
    assert not bad, bad


def test_the_packs_links_resolve():
    bad = []
    for p in pack_files():
        for t in re.findall(r"\]\(([^)\s]+)\)", p.read_text()):
            if re.match(r"(https?:|mailto:|#)", t):
                continue
            if not (p.parent / t.split("#")[0]).exists():
                bad.append((p.name, t))
    assert not bad, bad


def test_the_slide_figures_are_1920_wide_and_the_pdf_is_there():
    from PIL import Image
    figs = sorted((PACK / "figures").glob("*.png"))
    assert len(figs) >= 10
    assert all(Image.open(f).size[0] == 1920 for f in figs), [(f.name, Image.open(f).size) for f in figs]
    pdf = PACK / "PACK.pdf"
    assert pdf.exists() and pdf.stat().st_size > 50_000
    assert pdf.stat().st_size < 5_000_000
