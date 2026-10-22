"""Tests never reach the network: the client's Voyager guards (catalog check and identity
canary) are switched off unless a test switches them back on with fakes."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def _no_voyager_guards(monkeypatch):
    import client
    monkeypatch.setattr(client, "GUARDS", False)
    monkeypatch.setattr(client, "_halted", None)
    monkeypatch.setattr(client, "_catalog_ok", set())
    monkeypatch.setattr(client, "_canary_at", {})
