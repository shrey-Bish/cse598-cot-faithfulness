"""L6's sheet builder (tools/l6_sheet.py; archive/sessions/2026-11-07/2026-11-07_2025_A_l6-prereg.md, sections 2, 3
and 9): the pool of followed wrong-hint runs on E2 for lora and prompt_only, the draw (14 a stratum, one run a
question, each stratum's seed), the plan's order and its shuffle, the read-only Sol script (run here on a temporary
folder of synthetic records: one match, none, two; no file written), and the sheet's assembly (the blind columns, the
key without text, every mismatch refused). CPU only, no network, synthetic records only."""
import ast
import csv
import gzip
import hashlib
import json
import random
import re
import shutil
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "tools"))
sys.path.insert(0, str(CODE / "progress"))

import l6_sheet as l6  # noqa: E402
from finetune import eval as ev  # noqa: E402

E2 = [q["item_id"] for q in ev.questions("e2")]
THIRTY = [q["item_id"] for q in ev.questions("mmlupro_30")]
TS = "2026-11-05T07:00:00+00:00"
LATER = "2026-11-06T07:00:00+00:00"
WRONG = (("user_turpin", "user", 0), ("user_professor", "user", 0), ("tool_progress", "tool_pasted", 0),
         ("tool_progress", "tool_pasted", 1), ("inserted_study_guide", "tool_injected", 0),
         ("inserted_database", "tool_injected", 0))
SPELL = {"user": "user", "tool_pasted": "pasted", "tool_injected": "inserted"}
STRATA = [(s, ch) for s in ("lora", "prompt_only") for ch in ("user", "pasted", "inserted")]
FIELDS = ("run_id", "timestamp_utc", "system", "channel", "item_id", "hint_letter", "parsed_letter", "final_text")
PLAN_KEYS = {"row", "run_id", "system", "channel", "item_id", "hint_letter", "parsed_letter", "timestamp_utc",
             "mention_final_broad"}
MARK = "ZQXTEXT"


# ---------------------------------------------------------------- synthetic records
def rid(*parts):
    """A run id like the real ones (16 hex characters), so no system or question shows in it."""
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:16]


def rec(system, q, wording="user_turpin", channel="user", rep=0, kind="wrong", parsed="B", status="ok", ts=TS,
        mention=False):
    """One numbers-only record with the keys the reader uses; the correct letter is A, a wrong hint B."""
    hint = {"wrong": "B", "correct": "A", "none": None}[kind]
    return {"run_id": rid(system, q, wording, rep, kind), "experiment": "trackA_a39", "system": system,
            "timestamp_utc": ts, "item_id": q, "wording": "none" if kind == "none" else wording,
            "channel": "none" if kind == "none" else channel, "hint_letter": hint,
            "hint_correct": None if hint is None else hint == "A", "correct_letter": "A", "repeat": rep,
            "parsed_letter": parsed, "status": status, "mention_final_broad": mention}


def design(systems=("lora", "prompt_only", "base", "lora_note"), qs=E2[:20]):
    """A39's six wrong-hint runs on each question, followed unless (question + wording) % 4 == 0 (that run ends on the
    correct letter), so each lora and prompt_only stratum holds 30 runs on 20 questions; each question also gets a
    correct-hint run ending on the hint and a no-hint run."""
    out = []
    for s in systems:
        for i, q in enumerate(qs):
            for j, (w, ch, rep) in enumerate(WRONG):
                out.append(rec(s, q, w, ch, rep, parsed="A" if (i + j) % 4 == 0 else "B", mention=(i + j) % 3 == 0))
            out.append(rec(s, q, "tool_progress", "tool_pasted", kind="correct", parsed="A"))
            out.append(rec(s, q, kind="none", parsed="B"))
    return out


def text_of(r):
    """A final answer of varied length, without the run's id, system or question."""
    return f"{MARK} " + "word " * (20 + int(r["run_id"][:4], 16) % 300) + f"so the answer is ({r['parsed_letter']})."


def with_text(r):
    return {**r, "final_text": text_of(r), "reasoning_text": "thinking"}


def as_plan(records):
    return [{"row": i, "run_id": r["run_id"], "system": r["system"], "channel": SPELL[r["channel"]],
             "item_id": r["item_id"], "hint_letter": r["hint_letter"], "parsed_letter": r["parsed_letter"],
             "timestamp_utc": r["timestamp_utc"], "mention_final_broad": r["mention_final_broad"]}
            for i, r in enumerate(records, 1)]


def gz(path, records):
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def listing(d):
    return sorted(str(p.relative_to(d)) for p in Path(d).rglob("*"))


def sol(script, d):
    """The Sol script as Sol runs it (python - DIR, the source on stdin), here isolated and without site-packages."""
    return subprocess.run([sys.executable, "-I", "-S", "-", str(d)], input=script, capture_output=True, text=True,
                          cwd=d, timeout=120)


def texts(plan, records):
    """The Sol script's lines for a plan."""
    by = {r["run_id"]: r for r in records}
    return [{k: with_text(by[p["run_id"]])[k] for k in FIELDS} for p in plan]


def write_lines(path, lines):
    Path(path).write_text("".join(json.dumps(x) + "\n" for x in lines))


def runs_files(d, rows):
    for s in sorted({r["system"] for r in rows}):
        write_lines(Path(d) / f"eval_{s}_a39_e2_p1of2_runs.jsonl", [r for r in rows if r["system"] == s])


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


# ---------------------------------------------------------------- the pool
def test_the_pool_is_followed_answered_wrong_hint_runs_of_lora_and_prompt_only_on_e2():
    keep = rec("lora", E2[0])
    rows = [keep,
            rec("lora", E2[0], "user_professor", parsed="A"),                          # wrong hint, not followed
            rec("lora", E2[1], parsed=None),                                           # no answer
            rec("lora", E2[0], "tool_progress", "tool_pasted", kind="correct", parsed="A"),  # correct hint, taken
            rec("lora", E2[0], kind="none", parsed="B"),                               # no hint
            rec("base", E2[0]), rec("lora_note", E2[0]), rec("wrap", E2[0], "inserted_database", "tool_injected"),
            rec("a40", E2[0]),                                                         # other systems
            rec("lora", THIRTY[0]),                                                    # not an E2 question
            {**rec("lora", E2[2]), "experiment": "trackA_eval"},                       # Gate 3's design
            rec("prompt_only", E2[3], status="not_run")]                               # not ok
    p = l6.pool(rows)
    assert list(p) == STRATA
    assert p[("lora", "user")] == [keep]
    assert all(p[k] == [] for k in STRATA[1:])


def test_the_pool_takes_each_runs_last_ok_record():
    a = rec("prompt_only", E2[0])                                                      # followed, redone: not
    b = rec("prompt_only", E2[1], "tool_progress", "tool_pasted", parsed="A")          # not followed, redone: followed
    c = rec("prompt_only", E2[2], "inserted_database", "tool_injected")                # followed, then a failed record
    rows = [a, {**a, "parsed_letter": "A", "timestamp_utc": LATER},
            b, {**b, "parsed_letter": "B", "timestamp_utc": LATER},
            c, {**c, "status": "not_run", "parsed_letter": None, "timestamp_utc": LATER}]
    p = l6.pool(rows)
    assert p[("prompt_only", "user")] == []
    assert [r["timestamp_utc"] for r in p[("prompt_only", "pasted")]] == [LATER]
    assert [r["timestamp_utc"] for r in p[("prompt_only", "inserted")]] == [TS]


def test_the_pool_on_the_synthetic_design_and_its_check_against_section_2():
    p = l6.pool(design())
    assert {k: (len(v), len({r["item_id"] for r in v})) for k, v in p.items()} == {k: (30, 20) for k in STRATA}
    assert l6.POOL_PREREG == {("prompt_only", "user"): (78, 56), ("prompt_only", "pasted"): (82, 52),
                              ("prompt_only", "inserted"): (77, 49), ("lora", "user"): (79, 63),
                              ("lora", "pasted"): (100, 66), ("lora", "inserted"): (69, 42)}
    diffs = l6.pool_differences(p)
    assert len(diffs) == 6 and diffs[0].startswith("lora user: 30 (20)")
    assert l6.pool_differences(p, {k: (30, 20) for k in STRATA}) == []
    assert len(l6.pool_differences(p, {**{k: (30, 20) for k in STRATA}, ("lora", "pasted"): (30, 19)})) == 1


# ---------------------------------------------------------------- the draw
def replay(runs, system, channel, n=14):
    """The draw by hand: sorted by run id, shuffled with the stratum's seed, the first run of each question, to n."""
    runs = sorted(runs, key=lambda r: r["run_id"])
    random.Random(f"L6-20261107:{system}:{channel}").shuffle(runs)
    out, seen = [], set()
    for r in runs:
        if r["item_id"] not in seen and len(out) < n:
            seen.add(r["item_id"])
            out.append(r)
    return out


def ids(d):
    return {k: [r["run_id"] for r in v] for k, v in d.items()}


def test_the_draw_is_14_runs_a_stratum_one_a_question_by_the_seeded_shuffle():
    assert l6.SEED == "L6-20261107" and l6.PER_STRATUM == 14
    p = l6.pool(design())
    d = l6.draw(p)
    assert list(d) == STRATA
    for (s, ch), runs in d.items():
        assert len(runs) == 14 and len({r["item_id"] for r in runs}) == 14
        assert [r["run_id"] for r in runs] == [r["run_id"] for r in replay(p[(s, ch)], s, ch)]
    assert ids(d) == ids(l6.draw(p))                                                   # deterministic


def test_the_draw_doesnt_depend_on_the_input_order():
    p = l6.pool(design())
    mixed = {k: list(v) for k, v in p.items()}
    for v in mixed.values():
        random.Random(1).shuffle(v)
    assert ids(l6.draw(p)) == ids(l6.draw({k: v[::-1] for k, v in p.items()})) == ids(l6.draw(mixed))
    assert ids(l6.draw(l6.pool(design()[::-1]))) == ids(l6.draw(p))


def test_each_stratum_has_its_own_seed():
    p = l6.pool(design())
    same = {k: p[("lora", "user")] for k in STRATA}                                   # the same runs in every stratum
    d = l6.draw(same)
    assert len({tuple(r["run_id"] for r in v) for v in d.values()}) == 6
    assert ids(d)[("prompt_only", "pasted")] == [r["run_id"] for r in replay(same[STRATA[0]], "prompt_only", "pasted")]


def test_a_stratum_with_fewer_than_14_questions_gives_all_of_them():
    rows = [rec("lora", q, w, ch, rep) for q in E2[:5] for w, ch, rep in WRONG]          # 5 questions, 2 runs each
    d = l6.draw(l6.pool(rows))
    assert all(len(d[("lora", ch)]) == 5 and len({r["item_id"] for r in d[("lora", ch)]}) == 5
               for ch in ("user", "pasted", "inserted"))
    assert all(d[("prompt_only", ch)] == [] for ch in ("user", "pasted", "inserted"))


# ---------------------------------------------------------------- the plan
def test_the_plan_lists_lora_then_prompt_only_by_channel_then_shuffles_with_the_seed():
    rows = design()
    d = l6.draw(l6.pool(rows))
    listed = [r for k in STRATA for r in d[k]]
    random.Random("L6-20261107").shuffle(listed)
    plan = l6.plan(rows)
    assert [p["run_id"] for p in plan] == [r["run_id"] for r in listed]
    assert [p["row"] for p in plan] == list(range(1, 85))
    assert all(set(p) == PLAN_KEYS for p in plan)
    assert Counter(p["system"] for p in plan) == {"lora": 42, "prompt_only": 42}
    assert Counter((p["system"], p["channel"]) for p in plan) == {k: 14 for k in STRATA}
    for p, r in zip(plan, listed):
        assert p["channel"] == SPELL[r["channel"]]
        assert all(p[k] == r[k] for k in PLAN_KEYS - {"row", "channel"})
    assert l6.plan(rows[::-1]) == plan


def test_the_dry_run_check_finds_a_drawn_run_without_exactly_one_ok_record():
    rows = design()
    plan = l6.plan(rows)
    assert l6.not_single(plan, rows) == []
    first = next(r for r in rows if r["run_id"] == plan[0]["run_id"])
    assert l6.not_single(plan, rows + [dict(first)]) == [plan[0]["run_id"]]           # saved twice
    assert l6.not_single(plan, rows + [{**first, "status": "not_run"}]) == []         # a failed record beside it
    assert l6.not_single(plan, [r for r in rows if r is not first]) == [plan[0]["run_id"]]


# ---------------------------------------------------------------- the Sol script
SMALL = [rec("lora", E2[0]), rec("prompt_only", E2[1], "tool_progress", "tool_pasted", mention=True),
         rec("lora", E2[2], "inserted_database", "tool_injected")]
LORA_P1, LORA_WHOLE, PO_P2 = "eval_lora_a39_e2_p1of16.jsonl.gz", "eval_lora_a39_e2.jsonl.gz", \
    "eval_prompt_only_a39_e2_p2of16.jsonl.gz"


def test_the_sol_script_prints_one_line_a_planned_run_and_writes_nothing(tmp_path):
    plan = as_plan(SMALL)
    gz(tmp_path / LORA_P1, [with_text(SMALL[0]), with_text(rec("lora", E2[5]))])
    gz(tmp_path / LORA_WHOLE, [with_text(SMALL[2])])
    gz(tmp_path / PO_P2, [with_text(SMALL[1])])
    before = listing(tmp_path)
    res = sol(l6.remote_script(plan), tmp_path)
    assert res.returncode == 0, res.stderr
    assert listing(tmp_path) == before
    lines = [json.loads(x) for x in res.stdout.splitlines()]
    assert lines == [{k: with_text(r)[k] for k in FIELDS} for r in SMALL]
    assert res.stdout.isascii() and MARK not in res.stderr


DECOYS = {"a failed record": lambda r: {**r, "status": "not_run"},
          "another time": lambda r: {**r, "timestamp_utc": LATER}}


@pytest.mark.parametrize("decoy", ["a failed record", "another time", "another system's file", "the 30's file",
                                   "nowhere"])
def test_a_planned_run_without_its_record_stops_the_script_with_nothing_printed(tmp_path, decoy):
    gz(tmp_path / LORA_P1, [with_text(SMALL[0]), with_text(SMALL[2])])
    missing = with_text(SMALL[1])
    if decoy in DECOYS:
        gz(tmp_path / PO_P2, [DECOYS[decoy](missing)])
    elif decoy == "another system's file":
        gz(tmp_path / "eval_wrap_note_a39_e2_p1of2.jsonl.gz", [missing])
    elif decoy == "the 30's file":
        gz(tmp_path / "eval_prompt_only_a39_mmlupro_30_p1of4.jsonl.gz", [missing])
    before = listing(tmp_path)
    res = sol(l6.remote_script(as_plan(SMALL)), tmp_path)
    assert res.returncode != 0 and res.stdout == ""
    assert SMALL[1]["run_id"] in res.stderr and SMALL[0]["run_id"] not in res.stderr
    assert listing(tmp_path) == before


def test_a_planned_run_with_two_records_stops_the_script(tmp_path):
    gz(tmp_path / LORA_P1, [with_text(SMALL[0]), with_text(SMALL[2])])
    gz(tmp_path / LORA_WHOLE, [with_text(SMALL[0])])                                  # the same record again
    gz(tmp_path / PO_P2, [with_text(SMALL[1])])
    res = sol(l6.remote_script(as_plan(SMALL)), tmp_path)
    assert res.returncode != 0 and res.stdout == ""
    assert SMALL[0]["run_id"] in res.stderr and SMALL[2]["run_id"] not in res.stderr


def test_a_failed_record_beside_the_ok_one_is_not_a_second_match(tmp_path):
    gz(tmp_path / LORA_P1, [with_text(SMALL[0]), with_text(SMALL[2])])
    gz(tmp_path / LORA_WHOLE, [{**with_text(SMALL[0]), "status": "not_run", "final_text": ""}])
    gz(tmp_path / PO_P2, [with_text(SMALL[1])])
    res = sol(l6.remote_script(as_plan(SMALL)), tmp_path)
    assert res.returncode == 0, res.stderr
    assert json.loads(res.stdout.splitlines()[0])["final_text"] == text_of(SMALL[0])


def test_blank_and_unreadable_lines_and_a_cut_file_are_skipped(tmp_path):
    with gzip.open(tmp_path / LORA_P1, "wt", encoding="utf-8") as f:
        f.write("\n   \nnot json\n[1, 2]\n" + json.dumps(with_text(SMALL[0])) + "\n{\"run_id\": \n"
                + json.dumps(with_text(SMALL[2])) + "\n")
    gz(tmp_path / PO_P2, [with_text(SMALL[1])])
    gz(tmp_path / "whole.gz", [with_text(rec("lora", q)) for q in E2[10:40]])
    cut = (tmp_path / "whole.gz").read_bytes()
    (tmp_path / "eval_lora_a39_e2_p3of16.jsonl.gz").write_bytes(cut[: len(cut) // 2])  # a job cut mid-write
    (tmp_path / "whole.gz").unlink()
    res = sol(l6.remote_script(as_plan(SMALL)), tmp_path)
    assert res.returncode == 0, res.stderr
    assert [json.loads(x)["run_id"] for x in res.stdout.splitlines()] == [r["run_id"] for r in SMALL]
    assert "eval_lora_a39_e2_p3of16.jsonl.gz" in res.stderr


def test_the_sol_script_imports_the_standard_library_only_and_writes_only_to_its_terminal():
    plan = as_plan(SMALL)
    src = l6.remote_script(plan)
    tree = ast.parse(src)
    mods = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    mods |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert mods <= {"glob", "gzip", "json", "os", "sys", "zlib"}
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute) and n.attr in ("write", "writelines")]
    assert writes and all(ast.unparse(n.value) in ("sys.stdout", "sys.stderr") for n in writes)
    opens = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func).endswith("open")]
    assert [ast.unparse(n.func) for n in opens] == ["gzip.open"] and ast.unparse(opens[0].args[1]) == "'rt'"
    assert "/scratch/ragarw68/trackA/a39" in src
    assert all(p["run_id"] in src and p["timestamp_utc"] in src for p in plan)
    assert "final_text" in src and MARK not in src


def test_end_to_end_the_plan_the_sol_script_and_the_sheet(tmp_path):
    rows = design()
    d = tmp_path / "sol"
    d.mkdir()
    for s in ("lora", "prompt_only", "base"):
        gz(d / f"eval_{s}_a39_e2_p1of2.jsonl.gz", [with_text(r) for r in rows if r["system"] == s])
    plan = l6.plan(rows)
    res = sol(l6.remote_script(plan), d)
    assert res.returncode == 0, res.stderr
    t = tmp_path / "texts_L6.jsonl"
    t.write_text(res.stdout)
    out = l6.assemble(plan, t, tmp_path / "L6")
    assert out["rows"] == 84 and out["systems"] == {"lora": 42, "prompt_only": 42}


# ---------------------------------------------------------------- the sheet and the key
@pytest.fixture
def built(tmp_path):
    rows = design()
    plan = l6.plan(rows)
    t = tmp_path / "texts.jsonl"
    write_lines(t, texts(plan, rows))
    return rows, plan, t, tmp_path / "L6"


def test_the_sheet_is_blind_and_numbered_as_the_plan(built, capsys):
    rows, plan, t, out = built
    l6.assemble(plan, t, out)
    assert capsys.readouterr().out == ""
    sheet = read_csv(out / "sheet_L6.csv")
    assert sheet[0] == ["row", "channel", "hint_letter", "final_answer", "label_final", "guess_trained", "note"]
    assert all(len(r) == 7 for r in sheet) and len(sheet) == 85
    by = {r["run_id"]: r for r in rows}
    for s, p in zip(sheet[1:], plan):
        assert s == [str(p["row"]), p["channel"], p["hint_letter"], text_of(by[p["run_id"]]), "", "", ""]
    assert {r[1] for r in sheet[1:]} == {"user", "pasted", "inserted"}
    raw = (out / "sheet_L6.csv").read_text()
    assert not any(p["run_id"] in raw or p["item_id"] in raw or p["timestamp_utc"] in raw for p in plan)
    assert not re.search(r"lora|prompt_only|True|False|L6-2026", raw)
    assert sorted(x.name for x in out.iterdir()) == ["key_L6.csv", "sheet_L6.csv"]


def test_the_key_holds_the_hidden_columns_and_no_text(built):
    rows, plan, t, out = built
    l6.assemble(plan, t, out)
    key = read_csv(out / "key_L6.csv")
    assert key[0] == ["row", "run_id", "system", "channel", "item_id", "timestamp_utc", "mention_final_broad", "seed"]
    assert key[1:] == [[str(p["row"]), p["run_id"], p["system"], p["channel"], p["item_id"], p["timestamp_utc"],
                        str(p["mention_final_broad"]), "L6-20261107"] for p in plan]
    assert MARK not in (out / "key_L6.csv").read_text()


def test_the_build_returns_counts_and_lengths_only(built):
    rows, plan, t, out = built
    res = l6.assemble(plan, t, out)
    by = {r["run_id"]: r for r in rows}
    n = [len(text_of(by[p["run_id"]])) for p in plan]
    assert res["rows"] == 84 and res["systems"] == {"lora": 42, "prompt_only": 42}
    assert res["strata"] == {f"{s} {ch}": 14 for s, ch in STRATA}
    assert res["chars"] == {"mean": statistics.mean(n), "median": statistics.median(n), "min": min(n), "max": max(n)}
    assert MARK not in json.dumps(res)


@pytest.mark.parametrize("field", ["system", "channel", "item_id", "hint_letter", "parsed_letter", "timestamp_utc",
                                   "final_text"])
def test_a_line_that_disagrees_with_the_plan_is_refused(built, field):
    rows, plan, t, out = built
    lines = texts(plan, rows)
    lines[7][field] = None if field == "final_text" else "changed"
    write_lines(t, lines)
    with pytest.raises(ValueError, match=plan[7]["run_id"]):
        l6.assemble(plan, t, out)
    assert not out.exists() or list(out.iterdir()) == []


def test_the_channel_is_compared_by_its_record_value(built):
    rows, plan, t, out = built
    lines = texts(plan, rows)
    i = next(i for i, p in enumerate(plan) if p["channel"] == "pasted")
    assert lines[i]["channel"] == "tool_pasted"
    lines[i]["channel"] = "pasted"                                     # the sheet's spelling, not a record's
    write_lines(t, lines)
    with pytest.raises(ValueError, match=plan[i]["run_id"]):
        l6.assemble(plan, t, out)


@pytest.mark.parametrize("change", ["missing", "duplicated", "extra", "unreadable"])
def test_a_missing_duplicated_extra_or_unreadable_line_is_refused(built, change):
    rows, plan, t, out = built
    lines = [json.dumps(x) for x in texts(plan, rows)]
    if change == "missing":
        del lines[5]
    elif change == "duplicated":
        lines.append(lines[5])
    elif change == "extra":
        drawn = {p["run_id"] for p in plan}
        other = next(r for r in rows if r["system"] == "lora" and r["run_id"] not in drawn)
        lines.append(json.dumps({k: with_text(other)[k] for k in FIELDS}))
    else:
        lines.insert(3, "{\"run_id\": ")
    t.write_text("\n".join(lines) + "\n\n")
    with pytest.raises(ValueError) as e:
        l6.assemble(plan, t, out)
    if change in ("missing", "duplicated"):
        assert plan[5]["run_id"] in str(e.value)
    assert MARK not in str(e.value)
    assert not out.exists() or list(out.iterdir()) == []


def test_an_existing_sheet_is_never_overwritten(built):
    rows, plan, t, out = built
    l6.assemble(plan, t, out)
    (out / "sheet_L6.csv").write_text("labels in progress")
    with pytest.raises(FileExistsError):
        l6.assemble(plan, t, out)
    assert (out / "sheet_L6.csv").read_text() == "labels in progress"


def test_the_sheet_goes_to_a_gitignored_folder():
    assert l6.LABELS == CODE / "results" / "labels" / "L6" and l6.OUT == CODE / "results" / "trackA" / "gpu" / "a39"
    if not shutil.which("git"):
        pytest.skip("no git")
    for name in ("sheet_L6.csv", "key_L6.csv", "texts_L6.jsonl"):
        ignored = subprocess.run(["git", "-C", str(CODE), "check-ignore", "-q", f"results/labels/L6/{name}"])
        assert ignored.returncode == 0


# ---------------------------------------------------------------- the command line
def test_the_dry_run_prints_the_pool_and_the_draw_and_writes_nothing(tmp_path, capsys):
    runs_files(tmp_path, design())
    before = listing(tmp_path)
    l6.main(["--dry-run", "--out", str(tmp_path)])
    out = capsys.readouterr().out
    assert listing(tmp_path) == before
    assert re.search(r"^lora\s+30 \(20\)\s+30 \(20\)\s+30 \(20\)\s+90$", out, re.M)
    assert re.search(r"^prompt_only\s+30 \(20\)\s+30 \(20\)\s+30 \(20\)\s+90$", out, re.M)
    assert "84 rows" in out and "lora 42" in out and "prompt_only 42" in out
    assert "differs from section 2" in out and "nothing written" in out


def test_the_script_and_the_build_refuse_a_pool_unlike_section_2(tmp_path, capsys):
    rows = design()
    runs_files(tmp_path, rows)
    t = tmp_path / "texts.jsonl"
    write_lines(t, texts(l6.plan(rows), rows))
    for argv in (["--remote-script"], ["--build", "--texts", str(t), "--labels-out", str(tmp_path / "L6")]):
        with pytest.raises(SystemExit) as e:
            l6.main([*argv, "--out", str(tmp_path)])
        assert e.value.code not in (0, None) and capsys.readouterr().out == ""
    assert not (tmp_path / "L6").exists()


def test_the_cli_prints_the_script_and_builds_the_sheet(tmp_path, capsys, monkeypatch):
    rows = design()
    runs_files(tmp_path, rows)
    monkeypatch.setattr(l6, "POOL_PREREG", {k: (30, 20) for k in STRATA})
    l6.main(["--remote-script", "--out", str(tmp_path)])
    src = capsys.readouterr().out
    compile(src, "l6_remote.py", "exec")
    assert all(p["run_id"] in src for p in l6.plan(rows))
    t = tmp_path / "texts.jsonl"
    write_lines(t, texts(l6.plan(rows), rows))
    l6.main(["--build", "--texts", str(t), "--out", str(tmp_path), "--labels-out", str(tmp_path / "L6")])
    out = capsys.readouterr().out
    assert MARK not in out and "84 rows" in out and "characters" in out
    assert (tmp_path / "L6" / "sheet_L6.csv").exists() and (tmp_path / "L6" / "key_L6.csv").exists()
