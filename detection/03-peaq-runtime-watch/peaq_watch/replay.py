"""Replay helpers for quantitative PEAQ halt validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_snapshots(path: Path | str) -> list[dict[str, Any]]:
    filepath = Path(path)
    raw = filepath.read_text().strip()
    if not raw:
        return []
    if raw.startswith("["):
        payload = json.loads(raw)
        if not isinstance(payload, list):
            raise ValueError("snapshot file must contain a JSON array")
        return [dict(item) for item in payload]

    snapshots: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        snapshots.append(dict(json.loads(line)))
    return snapshots


def build_snapshot_provider(snapshots: list[dict[str, Any]]):
    iterator = iter(snapshots)

    def provider(target: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
        return next(iterator)

    return provider
