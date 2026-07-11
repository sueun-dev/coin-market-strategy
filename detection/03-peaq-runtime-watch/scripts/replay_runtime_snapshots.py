#!/usr/bin/env python3
"""Replay saved PEAQ runtime snapshots through the detector."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from peaq_watch.monitor import load_config  # noqa: E402
from peaq_watch.replay import build_snapshot_provider, load_snapshots  # noqa: E402
from peaq_watch.runtime_head_source import RuntimeHeadSource  # noqa: E402
from peaq_watch.state_store import StateStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay saved PEAQ runtime snapshots.")
    parser.add_argument("snapshot_file", help="JSON or JSONL snapshot fixture")
    parser.add_argument(
        "--output-json", help="Optional path to save replay summary JSON"
    )
    parser.add_argument(
        "--expect-stages",
        nargs="*",
        default=[],
        help="Fail if the emitted stage sequence does not match exactly",
    )
    args = parser.parse_args()

    config = load_config()
    target = config["target"]
    snapshots = load_snapshots(args.snapshot_file)
    provider = build_snapshot_provider(snapshots)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(state_file=Path(tmpdir) / "state.json")
        source = RuntimeHeadSource(state_store=store, snapshot_provider=provider)
        rounds = []
        emitted_stages = []
        try:
            for index, _snapshot in enumerate(snapshots, start=1):
                events = source.collect(target)
                state = store.get_namespace(f"runtime_head:{target['chain_id']}")
                snap = state.get("last_snapshot", {})
                stages = [event.get("stage") for event in events]
                emitted_stages.extend(stages)
                rounds.append(
                    {
                        "round": index,
                        "level": state.get("current_level"),
                        "head": snap.get("quorum_head_number"),
                        "head_age": snap.get("quorum_head_age_sec"),
                        "finalized_age": snap.get("quorum_finalized_age_sec"),
                        "gap": snap.get("quorum_finality_gap_blocks"),
                        "spread": snap.get("endpoint_spread"),
                        "events": stages,
                    }
                )
        finally:
            source.close()

    summary = {
        "fixture": str(Path(args.snapshot_file).resolve()),
        "rounds": rounds,
        "emitted_stages": emitted_stages,
    }
    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.expect_stages and emitted_stages != args.expect_stages:
        raise SystemExit(f"expected stages {args.expect_stages}, got {emitted_stages}")


if __name__ == "__main__":
    main()
