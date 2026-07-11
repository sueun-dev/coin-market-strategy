"""Config helpers for the suspension forecaster."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "config" / "targets.json"


def load_monitor_config(
    config_file: Path | str = DEFAULT_CONFIG_FILE,
) -> dict[str, Any]:
    path = Path(config_file)
    with open(path, "r") as f:
        return json.load(f)


def match_target(target: dict[str, Any], query: str) -> bool:
    needle = query.lower()
    aliases = {
        str(target.get("chain_id", "")).lower(),
        str(target.get("chain_name", "")).lower(),
        str(target.get("primary_ticker", "")).lower(),
    }
    github = target.get("sources", {}).get("github_release", {}).get("repo")
    if github:
        aliases.add(str(github).lower())
    return needle in aliases
