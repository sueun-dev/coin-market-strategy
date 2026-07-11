#!/usr/bin/env python3
"""01. Deposit/withdrawal suspension forecaster."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.monitor import SuspensionMonitor
from src.telegram_notifier import TelegramNotifier


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def _enabled_sources(source_arg: str) -> set[str]:
    if source_arg == "github":
        return {"github_release"}
    if source_arg == "governance":
        return {"governance"}
    return {"github_release", "governance"}


def main():
    parser = argparse.ArgumentParser(
        description="Forecast exchange deposit/withdrawal suspensions from upstream signals."
    )
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval", type=int, default=600, help="Polling interval in seconds"
    )
    parser.add_argument(
        "--target", type=str, default=None, help="Poll a single chain/ticker/repo"
    )
    parser.add_argument(
        "--source",
        choices=["all", "github", "governance"],
        default="all",
        help="Limit polling to a specific source family",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--reset", action="store_true", help="Clear stored state before running"
    )
    parser.add_argument(
        "--test-telegram", action="store_true", help="Send a Telegram test message"
    )
    parser.add_argument(
        "--no-telegram", action="store_true", help="Do not send Telegram alerts"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    notifier = None if args.no_telegram else TelegramNotifier()

    if args.test_telegram:
        ok = notifier.send_test_message() if notifier else False
        print("Test message sent!" if ok else "Failed to send test message.")
        return

    monitor = SuspensionMonitor(
        poll_interval=args.interval,
        enabled_sources=_enabled_sources(args.source),
    )

    if args.reset:
        monitor.clear_state()

    if args.loop:
        monitor.run(
            on_signals=(
                lambda signals: notifier.send_signals(signals) if notifier else None
            )
        )
        return

    try:
        if args.target:
            signals = monitor.poll_target(args.target)
        else:
            signals = monitor.poll_all()

        if notifier and signals:
            notifier.send_signals(signals)

        if monitor.poll_errors:
            print(f"{len(monitor.poll_errors)} source errors during suspension poll")
            for error in monitor.poll_errors[:10]:
                print(f"- {error['chain_id']} {error['source_type']}: {error['error']}")
            if signals:
                print(f"{len(signals)} new suspension forecasts")
            raise SystemExit(2)

        if not signals:
            print("No new suspension forecasts")
        else:
            print(f"{len(signals)} new suspension forecasts")
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
