"""Standalone PEAQ halt monitor."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

from .runtime_head_source import RuntimeHeadSource
from .state_store import StateStore

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "config" / "runtime.json"


def load_config(config_file: Path | str = DEFAULT_CONFIG_FILE) -> dict[str, Any]:
    path = Path(config_file)
    with open(path, "r") as f:
        return json.load(f)


class PeaqRuntimeMonitor:
    def __init__(
        self,
        config_file: Optional[str] = None,
        poll_interval: int = 5,
        state_store: Optional[StateStore] = None,
        runtime_head_source: Optional[RuntimeHeadSource] = None,
    ):
        config = load_config(config_file) if config_file else load_config()
        self.poll_interval = poll_interval or int(
            config.get("poll_interval_seconds", 5)
        )
        self.target = config["target"]
        self.state_store = state_store or StateStore()
        self.runtime_head_source = runtime_head_source or RuntimeHeadSource(
            state_store=self.state_store
        )

    def close(self) -> None:
        self.runtime_head_source.close()

    def clear_state(self) -> None:
        self.state_store.clear()

    def poll_once(self) -> list[dict[str, Any]]:
        return self.runtime_head_source.collect(self.target)

    def run(
        self, on_events: Optional[Callable[[list[dict[str, Any]]], None]] = None
    ) -> None:
        logger.info("PEAQ halt monitor started interval=%ss", self.poll_interval)
        try:
            while True:
                events = self.poll_once()
                if events and on_events is not None:
                    on_events(events)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        finally:
            self.close()
