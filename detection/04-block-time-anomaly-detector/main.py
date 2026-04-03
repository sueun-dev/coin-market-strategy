#!/usr/bin/env python3
from __future__ import annotations

"""
04. Block Time Anomaly Detector — main entry point.

Usage:
  python main.py                  # single poll of all chains, report status
  python main.py --loop           # continuous monitoring at 10-second intervals
  python main.py --chain cosmos   # monitor a specific chain (substring match)
  python main.py --verbose        # debug logging
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx

from src.chain_monitor import AnomalyLevel, ChainMonitor, ChainStatus
from src.halt_detector import HaltDetector
from src.signal_emitter import SignalEmitter
from src.state_store import StateStore

CONFIG_FILE = Path(__file__).parent / "config" / "chains.json"
DEFAULT_POLL_INTERVAL = 10  # seconds


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def load_chains(chain_filter: str | None = None) -> list[dict]:
    """Load chain configs from JSON, optionally filtering by substring."""
    with open(CONFIG_FILE, "r") as f:
        data = json.load(f)

    chains = data["chains"]
    if chain_filter:
        needle = chain_filter.lower()
        chains = [
            c for c in chains
            if needle in c["chain_id"].lower()
            or needle in c["name"].lower()
            or needle in c["ticker"].lower()
        ]
    return chains


def print_status_table(statuses: list[ChainStatus]):
    """Print a formatted status table to console."""
    print("\n" + "=" * 90)
    print(f"{'Chain':<18} {'Ticker':<7} {'Height':>14} {'Elapsed':>10} "
          f"{'Avg':>6} {'Level':<10} {'Status'}")
    print("-" * 90)

    for s in statuses:
        if s.error:
            print(f"{s.chain_name:<18} {s.ticker:<7} {'ERROR':>14} "
                  f"{'':>10} {'':>6} {'':>10} {s.error}")
            continue

        height = s.latest_block.height if s.latest_block else 0
        elapsed = f"{s.seconds_since_last_block:.1f}s"
        avg = f"{s.avg_block_time:.1f}s"

        level_str = s.anomaly_level.value.upper()
        if s.anomaly_level == AnomalyLevel.CRITICAL:
            status = "!! CRITICAL !!"
        elif s.anomaly_level == AnomalyLevel.ALERT:
            status = "! ALERT !"
        elif s.anomaly_level == AnomalyLevel.WARNING:
            status = "WARNING"
        else:
            status = "OK"

        print(f"{s.chain_name:<18} {s.ticker:<7} {height:>14,} "
              f"{elapsed:>10} {avg:>6} {level_str:<10} {status}")

    print("=" * 90)


def poll_all(
    monitors: list[ChainMonitor],
    halt_detector: HaltDetector,
    signal_emitter: SignalEmitter,
    state_store: StateStore,
) -> list[ChainStatus]:
    """Poll all monitors once, run halt detection, emit signals."""
    statuses: list[ChainStatus] = []

    for mon in monitors:
        status = mon.poll()
        statuses.append(status)

        if status.error:
            state_store.mark_error(status.chain_id, status.error)
            continue

        block = status.latest_block
        if block is None:
            continue

        # Feed halt detector
        halt_rec = halt_detector.observe(status.chain_id, block.height)

        # Update persistent state
        state_store.update_chain(
            chain_id=status.chain_id,
            height=block.height,
            block_time=block.timestamp,
            anomaly_level=status.anomaly_level.value,
            is_halted=halt_rec.halt_confirmed,
        )

        # Emit halt signal if newly confirmed
        if halt_rec.halt_confirmed and halt_rec.consecutive_stalls == halt_detector.threshold:
            signal_emitter.emit_halt(
                chain_id=status.chain_id,
                ticker=status.ticker,
                tickers_affected=mon.tickers_affected,
                last_block_height=block.height,
                last_block_time=block.timestamp,
                seconds_since_last_block=status.seconds_since_last_block,
                avg_block_time=status.avg_block_time,
                halt_type=halt_rec.halt_type,
            )

        # Emit resume signal if chain just resumed
        if halt_rec.resumed and halt_rec.resumed_at:
            duration = halt_rec.resumed_at - (halt_rec.halt_confirmed_at or halt_rec.resumed_at)
            signal_emitter.emit_resume(
                chain_id=status.chain_id,
                ticker=status.ticker,
                resumed_height=block.height,
                halt_duration_seconds=duration,
            )
            # Reset the resumed flag after emitting
            halt_rec.resumed = False

    return statuses


def main():
    parser = argparse.ArgumentParser(
        description="Block Time Anomaly Detector — detect chain halts before exchange announcements"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Continuous monitoring mode (default: single poll)"
    )
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_POLL_INTERVAL,
        help=f"Polling interval in seconds (default: {DEFAULT_POLL_INTERVAL})"
    )
    parser.add_argument(
        "--chain", type=str, default=None,
        help="Filter chains by name/id/ticker substring (e.g. 'cosmos', 'SOL')"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Clear persisted state before running"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Load chain configs
    chains = load_chains(args.chain)
    if not chains:
        print(f"No chains match filter: {args.chain}")
        sys.exit(1)

    logger.info("Monitoring %d chain(s)", len(chains))

    # Initialize components
    client = httpx.Client()
    monitors = [ChainMonitor(c, client=client) for c in chains]
    halt_detector = HaltDetector()
    signal_emitter = SignalEmitter()
    state_store = StateStore()

    if args.reset:
        state_store.clear()
        logger.info("State cleared")

    try:
        if args.loop:
            logger.info(
                "Starting continuous monitoring (interval=%ds, Ctrl+C to stop)",
                args.interval,
            )
            while True:
                statuses = poll_all(monitors, halt_detector, signal_emitter, state_store)
                print_status_table(statuses)
                time.sleep(args.interval)
        else:
            # Single poll
            statuses = poll_all(monitors, halt_detector, signal_emitter, state_store)
            print_status_table(statuses)

            # Summary
            errors = [s for s in statuses if s.error]
            anomalies = [s for s in statuses if s.anomaly_level != AnomalyLevel.NONE and not s.error]
            print(f"\nPolled {len(statuses)} chains: "
                  f"{len(statuses) - len(errors)} OK, "
                  f"{len(errors)} errors, "
                  f"{len(anomalies)} anomalies")
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    finally:
        client.close()


if __name__ == "__main__":
    main()
