"""
Unit tests for the state store module.
Tests persistence, deduplication, and atomic write behavior.
"""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_store import StateStore


@pytest.fixture
def tmp_state_file(tmp_path):
    """Provide a temporary state file path."""
    return tmp_path / "test_state.json"


@pytest.fixture
def store(tmp_state_file):
    """Provide a fresh StateStore instance."""
    return StateStore(state_file=tmp_state_file)


class TestStateStoreBasic:
    def test_new_release_is_new(self, store):
        assert store.is_new("cosmos/gaia", "v25.0.0") is True

    def test_detected_release_not_new(self, store):
        store.mark_detected("cosmos/gaia", "v25.0.0")
        assert store.is_new("cosmos/gaia", "v25.0.0") is False

    def test_different_tag_is_new(self, store):
        store.mark_detected("cosmos/gaia", "v25.0.0")
        assert store.is_new("cosmos/gaia", "v26.0.0") is True

    def test_different_repo_is_new(self, store):
        store.mark_detected("cosmos/gaia", "v25.0.0")
        assert store.is_new("osmosis-labs/osmosis", "v25.0.0") is True

    def test_mark_with_signal_data(self, store):
        signal = {"ticker": "ATOM", "is_breaking": True}
        store.mark_detected("cosmos/gaia", "v25.0.0", signal_data=signal)
        entry = store.get("cosmos/gaia", "v25.0.0")
        assert entry is not None
        assert entry["signal_data"]["ticker"] == "ATOM"

    def test_get_nonexistent(self, store):
        assert store.get("nonexistent/repo", "v1.0.0") is None


class TestStateStorePersistence:
    def test_survives_reload(self, tmp_state_file):
        store1 = StateStore(state_file=tmp_state_file)
        store1.mark_detected("cosmos/gaia", "v25.0.0")

        # Create new instance from same file
        store2 = StateStore(state_file=tmp_state_file)
        assert store2.is_new("cosmos/gaia", "v25.0.0") is False

    def test_file_created(self, tmp_state_file, store):
        store.mark_detected("test/repo", "v1.0.0")
        assert tmp_state_file.exists()

    def test_file_is_valid_json(self, tmp_state_file, store):
        store.mark_detected("test/repo", "v1.0.0")
        with open(tmp_state_file) as f:
            data = json.load(f)
        assert "test/repo:v1.0.0" in data

    def test_atomic_write_no_tmp_leftover(self, tmp_state_file, store):
        store.mark_detected("test/repo", "v1.0.0")
        tmp = tmp_state_file.with_suffix(".tmp")
        assert not tmp.exists()


class TestStateStoreClear:
    def test_clear_removes_all(self, store):
        store.mark_detected("cosmos/gaia", "v25.0.0")
        store.mark_detected("osmosis-labs/osmosis", "v20.0.0")
        store.clear()
        assert store.is_new("cosmos/gaia", "v25.0.0") is True
        assert store.is_new("osmosis-labs/osmosis", "v20.0.0") is True

    def test_clear_persists(self, tmp_state_file):
        store1 = StateStore(state_file=tmp_state_file)
        store1.mark_detected("test/repo", "v1.0.0")
        store1.clear()

        store2 = StateStore(state_file=tmp_state_file)
        assert store2.is_new("test/repo", "v1.0.0") is True


class TestStateStoreGetAll:
    def test_get_all_returns_copy(self, store):
        store.mark_detected("test/repo", "v1.0.0")
        all_state = store.get_all()
        all_state.clear()
        # Original should not be affected
        assert store.is_new("test/repo", "v1.0.0") is False

    def test_get_all_multiple_entries(self, store):
        store.mark_detected("repo1/a", "v1.0.0")
        store.mark_detected("repo2/b", "v2.0.0")
        all_state = store.get_all()
        assert len(all_state) == 2


class TestStateStoreEdgeCases:
    def test_corrupted_state_file(self, tmp_state_file):
        # Write invalid JSON
        with open(tmp_state_file, "w") as f:
            f.write("not valid json{{{")
        store = StateStore(state_file=tmp_state_file)
        # Should reinitialize
        assert store.is_new("test/repo", "v1.0.0") is True

    def test_empty_state_file(self, tmp_state_file):
        tmp_state_file.touch()
        store = StateStore(state_file=tmp_state_file)
        assert store.is_new("test/repo", "v1.0.0") is True

    def test_detected_at_timestamp(self, store):
        store.mark_detected("test/repo", "v1.0.0")
        entry = store.get("test/repo", "v1.0.0")
        assert "detected_at" in entry
        # Should be ISO format
        assert "T" in entry["detected_at"]
