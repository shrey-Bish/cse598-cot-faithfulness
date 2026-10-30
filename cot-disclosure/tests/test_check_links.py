"""tools/check_links.py: broken internal markdown links and RUNBOOK script paths. CPU only, no network."""
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE / "tools"))

import check_links as cl  # noqa: E402


def test_broken_links_and_missing_runbook_scripts(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "cot-disclosure" / "tools").mkdir(parents=True)
    (tmp_path / "cot-disclosure" / "tools" / "real.py").write_text("")
    (tmp_path / "docs" / "A.md").write_text("[ok](B.md) [anchor](B.md#x) [web](https://x.org) [gone](missing.md) "
                                           "[dir](../cot-disclosure/tools/) [self](#top) ![img](fig.png)\n")
    (tmp_path / "docs" / "B.md").write_text("# B\n")
    (tmp_path / "docs" / "RUNBOOK.md").write_text("```bash\npython tools/real.py --x\n"
                                                  "../.venv/bin/python tools/gone.py\nbash cot-disclosure/tools/real.py\n```\n")
    broken = cl.broken_links(tmp_path, [tmp_path / "docs" / "A.md", tmp_path / "docs" / "B.md"])
    assert sorted(t for _, t in broken) == ["fig.png", "missing.md"]
    assert cl.missing_scripts(tmp_path, tmp_path / "docs" / "RUNBOOK.md") == ["tools/gone.py"]
