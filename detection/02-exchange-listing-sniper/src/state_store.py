from __future__ import annotations

"""State file for latest seen Telegram post ids."""

import json
import os
import tempfile
import threading
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "data" / "detected_listing_posts.json"


class StateStore:
    """Track the latest processed Telegram message id per channel."""

    def __init__(self, state_file: Path | str = STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._state = self._load()

    def _load(self) -> dict:
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r") as handle:
                return json.load(handle)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save(self):
        with tempfile.NamedTemporaryFile(
            "w",
            dir=self.state_file.parent,
            prefix=f"{self.state_file.stem}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(self._state, handle, indent=2, ensure_ascii=False)
            tmp_path = Path(handle.name)
        os.replace(tmp_path, self.state_file)

    def get_last_seen(self, channel_id: str) -> int:
        with self._lock:
            return int(self._state.get(channel_id, {}).get("last_seen_message_id", 0))

    def snapshot_last_seen(self) -> dict[str, int]:
        with self._lock:
            return {
                channel_id: int(payload.get("last_seen_message_id", 0))
                for channel_id, payload in self._state.items()
            }

    def mark_seen(self, channel_id: str, message_id: int, persist: bool = True) -> bool:
        # NOTE (known limitation): dedup is a single monotonic high-water mark per
        # channel. A message whose id is <= the highest id already seen is treated
        # as a duplicate and skipped. Telegram channel message ids are assigned in
        # increasing order, so out-of-order delivery of a *lower* id (e.g. a brief
        # API reordering) would cause that listing to be dropped. This is a
        # deliberate trade-off: a set/window of recently-seen ids would catch that
        # case but widens the state model and is not the primary double-buy guard
        # (idempotency ultimately relies on Bybit's orderLinkId dedup). Revisit
        # only if lower-id reordering is observed in practice.
        with self._lock:
            existing = self._state.get(channel_id, {})
            if message_id <= int(existing.get("last_seen_message_id", 0)):
                return False
            self._state[channel_id] = {
                "last_seen_message_id": int(message_id),
            }
            if persist:
                self._save()
            return True

    def replace_last_seen_snapshot(
        self,
        snapshot: dict[str, int],
        persist: bool = True,
    ):
        with self._lock:
            self._state = {
                channel_id: {"last_seen_message_id": int(message_id)}
                for channel_id, message_id in snapshot.items()
            }
            if persist:
                self._save()

    def flush(self):
        with self._lock:
            self._save()

    def clear(self):
        with self._lock:
            self._state = {}
            self._save()
