"""Tests never reach the network or wait on a real run:
- any real HTTP request fails (a test that needs one installs its own fake urlopen)
- each test gets its own request-slot lock files, so a live run holding the 4 real slots
  can't block a test
- the client's Voyager guards (catalog check, identity canary) are off unless a test turns
  them back on with fakes"""
import sys
from pathlib import Path

import pytest

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(CODE / "progress"))


@pytest.fixture(autouse=True)
def _offline_and_isolated(monkeypatch, tmp_path):
    import urllib.request

    import client
    import common

    def no_network(*a, **k):
        raise AssertionError("a test tried to reach the network")
    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    slots = tmp_path / "slots"
    slots.mkdir()
    monkeypatch.setattr(common, "_SLOTS", slots)
    monkeypatch.setattr(client, "GUARDS", False)
    monkeypatch.setattr(client, "_halted", None)
    monkeypatch.setattr(client, "_catalog_ok", set())
    monkeypatch.setattr(client, "_canary_at", {})
