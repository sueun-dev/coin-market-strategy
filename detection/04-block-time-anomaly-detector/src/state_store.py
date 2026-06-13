"""
Block time anomaly detector — persistent state store.

Tracks each monitored chain's last known block height, block time,
halt status, and polling history. Persists to JSON file.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path(__file__).parent.parent / "data" / "chain_state.json"


class StateStore:
    """Persist chain monitoring state to a JSON file."""

    def __init__(self, state_file: Path | str = DEFAULT_STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict = self._load()

    def _load(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load state file, reinitializing: %s", e)
        return {}

    def _save(self):
        tmp = self.state_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    def update_chain(
        self,
        chain_id: str,
        height: int,
        block_time: float,
        anomaly_level: str = "none",
        is_halted: bool = False,
        stalled_height: int | None = None,
        consecutive_stalls: int = 0,
        halt_confirmed_at: float | None = None,
        halt_type: str = "unexpected",
        resumed_at: float | None = None,
    ):
        """Update state for a chain after a poll."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self._state.get(chain_id, {})
        was_halted = bool(existing.get("is_halted"))

        self._state[chain_id] = {
            "chain_id": chain_id,
            "last_height": height,
            "last_block_time": block_time,
            "last_polled": now,
            "anomaly_level": anomaly_level,
            "is_halted": is_halted,
            "stalled_height": stalled_height,
            "consecutive_stalls": int(consecutive_stalls or 0),
            "halt_confirmed_at": halt_confirmed_at,
            "halt_type": halt_type,
            "resumed_at": resumed_at,
            "first_seen": existing.get("first_seen", now),
            "halt_count": existing.get("halt_count", 0) + (1 if is_halted and not was_halted else 0),
        }
        self._save()

    def mark_error(self, chain_id: str, error: str):
        """Record an RPC error for a chain."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self._state.get(chain_id, {})
        existing["last_error"] = error
        existing["last_error_time"] = now
        self._state[chain_id] = existing
        self._save()

    def get(self, chain_id: str) -> dict | None:
        return self._state.get(chain_id)

    def get_all(self) -> dict:
        return self._state.copy()

    def clear(self):
        """Clear all state (for testing)."""
        self._state = {}
        self._save()
