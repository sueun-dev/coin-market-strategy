#!/usr/bin/env python3
"""Standalone PEAQ quantitative halt watcher."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from peaq_watch.monitor import PeaqRuntimeMonitor
from peaq_watch.telegram_notifier import TelegramNotifier


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standalone PEAQ quantitative halt watcher."
    )
    parser.add_argument("--loop", action="store_true", help="Run continuously")
    parser.add_argument(
        "--interval", type=int, default=5, help="Polling interval in seconds"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--reset", action="store_true", help="Clear stored runtime state before running"
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

    monitor = PeaqRuntimeMonitor(poll_interval=args.interval)
    if args.reset:
        monitor.clear_state()

    if args.loop:

        def handle_events(events):
            print(json.dumps(events, ensure_ascii=False, indent=2))
            if notifier:
                notifier.send_events(events)

        monitor.run(on_events=handle_events)
        return

    try:
        events = monitor.poll_once()
        if not events:
            print("No new PEAQ halt alerts")
        else:
            print(json.dumps(events, ensure_ascii=False, indent=2))
            if notifier:
                notifier.send_events(events)
    finally:
        monitor.close()


if __name__ == "__main__":
    main()
