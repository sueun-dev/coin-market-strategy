#!/usr/bin/env python3
"""
02. GitHub Release Monitor - Main entry point.

Usage:
  python3 main.py                        # Single poll all repos
  python3 main.py --loop                 # 30-minute interval polling
  python3 main.py --repo cosmos/gaia     # Specific repo only
  python3 main.py --reset                # Clear state and re-detect
  python3 main.py --verbose              # Debug logging
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.poller import ReleasePoller


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Release Monitor - Detect blockchain upgrade releases before exchange announcements"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Continuous polling mode (default: single run)"
    )
    parser.add_argument(
        "--interval", type=int, default=1800,
        help="Polling interval in seconds (default: 1800 = 30 min)"
    )
    parser.add_argument(
        "--repo", type=str, default=None,
        help="Poll a specific repo only (e.g. cosmos/gaia)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable debug logging"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Clear detection state before running"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    poller = ReleasePoller(poll_interval=args.interval)

    if args.reset:
        logger.info("Clearing detection state")
        poller.state_store.clear()

    if args.repo:
        logger.info("Polling single repo: %s", args.repo)
        signals = poller.poll_single(args.repo)
        if not signals:
            print(f"\n[{args.repo}] No new upgrade signals detected")
        else:
            print(f"\n[{args.repo}] {len(signals)} signal(s) detected")
    elif args.loop:
        poller.run()
        return
    else:
        logger.info("Single poll of all repos")
        signals = poller.poll_all()
        if not signals:
            print("\nNo new upgrade signals detected")
        else:
            print(f"\n{len(signals)} signal(s) detected")

    poller.close()


if __name__ == "__main__":
    main()
