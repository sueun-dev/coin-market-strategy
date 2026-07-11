"""StateStore tests for the rebuilt 01."""

import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_store import StateStore


def _make_store():
    return StateStore(state_file=Path(tempfile.mktemp(suffix=".json")))


def test_new_event_is_new():
    store = _make_store()
    assert (
        store.is_new_event("github_release", "injective:repo:v1.18.3", "early") is True
    )


def test_seen_event_is_not_new():
    store = _make_store()
    signal = {"signal_id": "abc"}
    store.mark_seen("github_release", "injective:repo:v1.18.3", "early", signal)
    assert (
        store.is_new_event("github_release", "injective:repo:v1.18.3", "early") is False
    )


def test_stage_keeps_separate_entries():
    store = _make_store()
    signal = {"signal_id": "abc"}
    store.mark_seen("governance", "injective:gov:628", "governance_voting", signal)
    assert (
        store.is_new_event("governance", "injective:gov:628", "governance_passed")
        is True
    )
