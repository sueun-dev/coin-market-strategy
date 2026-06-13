"""State-store dedup behavior for realtime Telegram delivery."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_store import MAX_SEEN_MESSAGE_IDS, StateStore


def test_mark_seen_accepts_lower_unseen_message_after_newer_runtime_message(tmp_path):
    store = StateStore(tmp_path / "state.json")

    assert store.mark_seen("bithumb", 103)
    assert store.mark_seen("bithumb", 102)
    assert not store.mark_seen("bithumb", 102)
    assert store.get_last_seen("bithumb") == 103


def test_loaded_last_seen_is_replay_floor_for_old_messages(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps({"bithumb": {"last_seen_message_id": 103}}),
        encoding="utf-8",
    )
    store = StateStore(state_file)

    assert not store.mark_seen("bithumb", 102)
    assert not store.mark_seen("bithumb", 103)
    assert store.mark_seen("bithumb", 104)


def test_seen_message_window_is_bounded(tmp_path):
    store = StateStore(tmp_path / "state.json")

    for message_id in range(1, MAX_SEEN_MESSAGE_IDS + 20):
        assert store.mark_seen("upbit", message_id)

    seen = store.snapshot_seen_message_ids()["upbit"]
    assert len(seen) == MAX_SEEN_MESSAGE_IDS
    assert 1 not in seen
    assert MAX_SEEN_MESSAGE_IDS + 19 in seen


def test_mark_seen_preserves_seen_listing_tickers(tmp_path):
    store = StateStore(tmp_path / "state.json")

    assert store.mark_listing_seen("bithumb", "SOMI", 11403)
    assert store.mark_seen("bithumb", 11404)

    reloaded = StateStore(tmp_path / "state.json")
    assert reloaded.has_seen_listing("bithumb", "SOMI")


def test_hot_state_snapshot_persists_recent_seen_message_ids(tmp_path):
    state_file = tmp_path / "state.json"
    store = StateStore(state_file)

    store.replace_hot_state_snapshot(
        {"bithumb": 321989},
        {"bithumb": [321987, "321989", "bad"]},
    )

    reloaded = StateStore(state_file)
    assert reloaded.snapshot_last_seen() == {"bithumb": 321989}
    assert reloaded.snapshot_seen_message_ids() == {"bithumb": [321987, 321989]}


def test_legacy_last_seen_state_still_loads(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"bithumb": 321989}), encoding="utf-8")

    store = StateStore(state_file)

    assert store.get_last_seen("bithumb") == 321989
    assert store.snapshot_last_seen() == {"bithumb": 321989}
    assert store.snapshot_seen_message_ids() == {"bithumb": []}
    assert not store.mark_seen("bithumb", 321989)
    assert store.mark_seen("bithumb", 321990)


def test_malformed_seen_message_ids_do_not_break_dedup(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {
                "bithumb": {
                    "last_seen_message_id": "321989",
                    "seen_message_ids": ["321988", "bad", 321989],
                },
                "upbit": {
                    "last_seen_message_id": "bad",
                    "seen_message_ids": "bad",
                },
            }
        ),
        encoding="utf-8",
    )

    store = StateStore(state_file)

    assert store.snapshot_last_seen() == {"bithumb": 321989, "upbit": 0}
    assert store.snapshot_seen_message_ids() == {
        "bithumb": [321988, 321989],
        "upbit": [],
    }
    assert not store.can_mark_seen("bithumb", 321989)
    assert store.can_mark_seen("bithumb", 321990)


def test_non_object_state_file_loads_as_empty_state(tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("[1, 2, 3]", encoding="utf-8")

    store = StateStore(state_file)

    assert store.snapshot_last_seen() == {}
    assert store.mark_seen("bithumb", 1)
