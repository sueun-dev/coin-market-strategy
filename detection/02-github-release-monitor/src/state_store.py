"""
State store for tracking already-detected releases.
Prevents duplicate signal emission. Uses JSON file with atomic writes.
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = Path(__file__).parent.parent / "data" / "detected_releases.json"


class StateStore:
    """Tracks detected releases to prevent duplicate signals."""

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
        """Atomic write: write to temp file then os.replace."""
        tmp = self.state_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self._state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.state_file)

    @staticmethod
    def _key(repo: str, tag: str) -> str:
        """Generate unique key from repo + tag."""
        return f"{repo}:{tag}"

    def is_new(self, repo: str, tag: str) -> bool:
        """Check if a release has NOT been detected before."""
        return self._key(repo, tag) not in self._state

    def mark_detected(self, repo: str, tag: str, signal_data: dict | None = None):
        """Record a release as detected."""
        key = self._key(repo, tag)
        now = datetime.now(timezone.utc).isoformat()

        self._state[key] = {
            "repo": repo,
            "tag": tag,
            "detected_at": now,
            "signal_data": signal_data,
        }
        self._save()
        logger.info("State recorded: %s @ %s", repo, tag)

    def get(self, repo: str, tag: str) -> dict | None:
        """Get stored data for a specific release."""
        return self._state.get(self._key(repo, tag))

    def get_all(self) -> dict:
        """Return all stored state."""
        return self._state.copy()

    def clear(self):
        """Clear all state (for reset)."""
        self._state = {}
        self._save()
        logger.info("State store cleared")
