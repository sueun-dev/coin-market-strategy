#!/usr/bin/env python3
"""
Live RPC integration tests for ChainMonitor.

Tests each chain type by making actual RPC calls to verify endpoints
are working and block data can be parsed correctly.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

from src.chain_monitor import ChainMonitor

CONFIG_FILE = Path(__file__).parent.parent / "config" / "chains.json"


def load_chains() -> list[dict]:
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)["chains"]


def check_single_chain(chain_config: dict, client: httpx.Client) -> tuple[bool, str]:
    """Check a single chain's RPC endpoint.

    Returns (success, message). Named ``check_*`` (not ``test_*``) so pytest does
    not collect it as a test case requiring fixtures; it is a helper driven by
    ``run_all_tests`` for live RPC verification.
    """
    try:
        monitor = ChainMonitor(chain_config, client=client)
        status = monitor.poll()

        if status.error:
            return False, f"RPC error: {status.error}"

        block = status.latest_block
        if block is None:
            return False, "No block returned"

        # Validate block data
        if block.height <= 0:
            return False, f"Invalid height: {block.height}"

        # Timestamp should be within the last hour (sanity check)
        now = time.time()
        age = now - block.timestamp
        if age < -60:
            return False, f"Block timestamp is in the future by {abs(age):.0f}s"
        if age > 3600:
            return False, f"Block timestamp is {age:.0f}s old (>1 hour)"

        return True, (
            f"height={block.height:,} elapsed={status.seconds_since_last_block:.1f}s "
            f"level={status.anomaly_level.value}"
        )

    except Exception as e:
        return False, f"Exception: {type(e).__name__}: {e}"


def run_all_tests():
    """Test all chains from config and report results."""
    chains = load_chains()
    client = httpx.Client()

    print(f"Testing {len(chains)} chain RPC endpoints...\n")
    print(f"{'Chain':<18} {'Ticker':<7} {'Type':<12} {'Result':<6} Details")
    print("-" * 90)

    passed = 0
    failed = 0
    failed_chains: list[str] = []

    for chain in chains:
        success, msg = check_single_chain(chain, client)
        label = "PASS" if success else "FAIL"

        if success:
            passed += 1
        else:
            failed += 1
            failed_chains.append(chain["chain_id"])

        print(f"{chain['name']:<18} {chain['ticker']:<7} {chain['rpc_type']:<12} {label:<6} {msg}")

    client.close()

    print(f"\n{'=' * 90}")
    print(f"Results: {passed} passed, {failed} failed out of {len(chains)} chains")

    if failed_chains:
        print(f"Failed chains: {', '.join(failed_chains)}")

    return failed == 0, failed_chains


if __name__ == "__main__":
    success, _ = run_all_tests()
    sys.exit(0 if success else 1)
