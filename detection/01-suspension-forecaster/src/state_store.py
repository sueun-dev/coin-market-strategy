"""State file for deduplicating suspension forecasts."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path(__file__).parent.parent / "data" / "state.json"


class StateStore:
    def __init__(self, state_file: Path | str = DEFAULT_STATE_FILE):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed to load state file, resetting: %s", exc)
            return {}

    def _save(self):
        tmp = self.state_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    @staticmethod
    def _key(source_type: str, event_key: str, stage: str) -> str:
        return f"{source_type}:{event_key}:{stage}"

    def is_new_event(self, source_type: str, event_key: str, stage: str) -> bool:
        return self._key(source_type, event_key, stage) not in self._state

    def mark_seen(
        self,
        source_type: str,
        event_key: str,
        stage: str,
        signal: dict[str, Any],
    ):
        key = self._key(source_type, event_key, stage)
        now = datetime.now(timezone.utc).isoformat()
        self._state[key] = {
            "source_type": source_type,
            "event_key": event_key,
            "stage": stage,
            "first_seen_at": self._state.get(key, {}).get("first_seen_at", now),
            "last_seen_at": now,
            "signal": signal,
        }
        self._save()

    def get_all(self) -> dict[str, Any]:
        return dict(self._state)

    def clear(self):
        self._state = {}
        self._save()
