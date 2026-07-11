#!/usr/bin/env python3
"""Run a long-lived PEAQ quantitative soak."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from peaq_watch.monitor import PeaqRuntimeMonitor  # noqa: E402
from peaq_watch.state_store import StateStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a long PEAQ quantitative soak.")
    parser.add_argument(
        "--interval", type=int, default=5, help="Polling interval seconds"
    )
    parser.add_argument(
        "--rounds", type=int, default=0, help="Explicit number of rounds"
    )
    parser.add_argument(
        "--duration-seconds", type=int, default=0, help="Run length in seconds"
    )
    parser.add_argument(
        "--reset", action="store_true", help="Clear soak state before running"
    )
    parser.add_argument("--state-file", help="Dedicated state file for the soak")
    parser.add_argument(
        "--output-jsonl", required=True, help="Path to append per-round JSONL output"
    )
    parser.add_argument("--summary-json", help="Optional summary JSON path")
    parser.add_argument(
        "--stop-on-alert",
        action="store_true",
        help="Stop once warning/critical/recovery is emitted",
    )
    args = parser.parse_args()

    rounds = args.rounds
    if rounds <= 0:
        if args.duration_seconds <= 0:
            raise SystemExit("Either --rounds or --duration-seconds must be provided")
        rounds = max(1, math.ceil(args.duration_seconds / args.interval))

    output_path = Path(args.output_jsonl)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    state_store = (
        StateStore(state_file=args.state_file) if args.state_file else StateStore()
    )
    monitor = PeaqRuntimeMonitor(poll_interval=args.interval, state_store=state_store)
    if args.reset:
        monitor.clear_state()

    alert_count = 0
    highest_level = "healthy"
    level_rank = {"healthy": 0, "observe": 1, "warning": 2, "critical": 3}

    try:
        with output_path.open("a") as out:
            for index in range(1, rounds + 1):
                started = time.time()
                events = monitor.poll_once()
                state = monitor.state_store.get_namespace("runtime_head:peaq")
                snapshot = state.get("last_snapshot", {})
                current_level = state.get("current_level", "healthy")
                if level_rank.get(current_level, 0) > level_rank.get(highest_level, 0):
                    highest_level = current_level
                alert_count += len(events)

                row = {
                    "round": index,
                    "timestamp_utc": snapshot.get("timestamp_utc"),
                    "level": current_level,
                    "head": snapshot.get("quorum_head_number"),
                    "head_age": snapshot.get("quorum_head_age_sec"),
                    "finalized_age": snapshot.get("quorum_finalized_age_sec"),
                    "gap": snapshot.get("quorum_finality_gap_blocks"),
                    "spread": snapshot.get("endpoint_spread"),
                    "http_errors": snapshot.get("http_error_count"),
                    "events": [event.get("stage") for event in events],
                    "trigger_reasons": snapshot.get("trigger_reasons", []),
                }
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
                out.flush()
                print(json.dumps(row, ensure_ascii=False), flush=True)

                if args.stop_on_alert and events:
                    break

                if index < rounds:
                    elapsed = time.time() - started
                    time.sleep(max(0.0, args.interval - elapsed))
    finally:
        monitor.close()

    summary = {
        "rounds_completed": index,
        "highest_level": highest_level,
        "alert_count": alert_count,
        "output_jsonl": str(output_path.resolve()),
    }
    if args.summary_json:
        summary_path = Path(args.summary_json)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
