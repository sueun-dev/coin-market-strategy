"""State file for standalone PEAQ runtime watcher."""

from __future__ import annotations

import json
import logging
import os
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
            logger.warning("Failed to load runtime state, resetting: %s", exc)
            return {}

    def _save(self) -> None:
        tmp = self.state_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    def get_namespace(self, namespace: str) -> dict[str, Any]:
        payload = self._state.get(namespace, {})
        return dict(payload) if isinstance(payload, dict) else {}

    def set_namespace(self, namespace: str, payload: dict[str, Any]) -> None:
        self._state[namespace] = payload
        self._save()

    def clear(self) -> None:
        self._state = {}
        self._save()
