#!/usr/bin/env python3
"""
ChainPulse — Unified Monitor
=============================
Connects all detection systems to Telegram alerts.

Usage:
  python3 run_monitor.py              # Single poll, all systems
  python3 run_monitor.py --loop       # Continuous monitoring
  python3 run_monitor.py --gov-only   # Governance monitor only
  python3 run_monitor.py --block-only # Block time monitor only
"""

import argparse
import json
import logging
import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

import httpx

# Load .env
load_dotenv(Path(__file__).parent / ".env")

# ── Paths ──────────────────────────────────────────────────
ROOT = Path(__file__).parent
GOV_DIR = ROOT / "detection" / "01-governance-monitor"
BLOCK_DIR = ROOT / "detection" / "04-block-time-anomaly-detector"

sys.path.insert(0, str(GOV_DIR))
sys.path.insert(0, str(BLOCK_DIR))

logger = logging.getLogger("chainpulse")

# ── Telegram Sender ────────────────────────────────────────

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


def send_telegram(text: str, priority: str = "P1"):
    """Send a message to Telegram."""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram not configured (missing token or chat_id)")
        return False

    try:
        client = httpx.Client(timeout=10)
        resp = client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )
        client.close()
        if resp.status_code == 200:
            logger.info("Telegram sent [%s]", priority)
            return True
        else:
            logger.error("Telegram error: %s", resp.text)
            return False
    except Exception as e:
        logger.error("Telegram send failed: %s", e)
        return False


# ── Signal Formatters ──────────────────────────────────────

def format_governance_signal(signal: dict) -> str:
    """Format governance upgrade signal for Telegram."""
    lead = signal.get("lead_time_hours", 0)
    lead_days = lead / 24 if lead else 0

    status_map = {
        "PROPOSAL_STATUS_VOTING_PERIOD": "VOTING",
        "PROPOSAL_STATUS_PASSED": "PASSED",
    }
    status = status_map.get(signal.get("proposal_status", ""), signal.get("proposal_status", ""))

    lines = [
        f"🟠 <b>[GOVERNANCE] Upgrade Detected</b>",
        "",
        f"Chain: <b>{signal.get('chain', '')} ({signal.get('ticker', '')})</b>",
        f"Proposal: #{signal.get('proposal_id', '')} — {signal.get('proposal_title', '')}",
        f"Status: {status}",
        f"Upgrade: {signal.get('upgrade_name', '')}",
        f"Target Block: {signal.get('upgrade_height', 'N/A'):,}" if signal.get('upgrade_height') else "Target Block: N/A",
        f"Remaining: {signal.get('remaining_blocks', 0):,} blocks" if signal.get('remaining_blocks') else "",
        f"Lead Time: <b>{lead:.1f}h ({lead_days:.1f} days)</b>" if lead else "",
        f"Approval: {signal.get('vote_yes_pct', 0)}%",
        f"Confidence: {signal.get('confidence', '')}",
        f"Detected: {signal.get('detected_at', '')[:19]}",
    ]
    return "\n".join(line for line in lines if line or line == "")


def format_block_halt_signal(signal: dict) -> str:
    """Format block halt signal for Telegram."""
    severity = signal.get("severity", "unknown")
    emoji = {"critical": "🔴🔴🔴", "alert": "🔴", "warning": "🟡"}.get(severity, "🟡")

    lines = [
        f"{emoji} <b>[CHAIN HALT] {signal.get('chain', '')} ({signal.get('ticker', '')})</b>",
        "",
        f"Last Block: {signal.get('last_block_height', 0):,}" if signal.get('last_block_height') else "",
        f"Time Since Last Block: <b>{signal.get('seconds_since_last_block', 0):.0f}s</b>",
        f"Normal Block Time: {signal.get('avg_block_time', 0):.1f}s",
        f"Halt Type: {signal.get('halt_type', 'unknown')}",
        f"Severity: <b>{severity.upper()}</b>",
        f"Affected: {', '.join(signal.get('tickers_affected', []))}",
        f"Detected: {signal.get('detected_at', '')[:19]}",
    ]
    if severity == "critical":
        lines.extend([
            "",
            "⚠️ <b>Chain appears halted. Exchange deposit/withdrawal suspension likely imminent.</b>",
        ])
    return "\n".join(line for line in lines if line or line == "")


def format_chain_resumed_signal(signal: dict) -> str:
    """Format chain resumed signal for Telegram."""
    lines = [
        f"🟢 <b>[CHAIN RESUMED] {signal.get('chain', '')} ({signal.get('ticker', '')})</b>",
        "",
        f"Block production resumed at height {signal.get('resumed_height', 'N/A')}",
        f"Downtime: {signal.get('downtime_seconds', 0):.0f}s",
    ]
    return "\n".join(lines)


# ── Governance Monitor ─────────────────────────────────────

def run_governance_poll() -> list[dict]:
    """Run a single governance poll and return new signals."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "gov_poller", GOV_DIR / "src" / "poller.py",
        submodule_search_locations=[str(GOV_DIR / "src")]
    )
    # We need to import all dependencies from the same src directory
    old_path = sys.path.copy()
    sys.path.insert(0, str(GOV_DIR))
    try:
        from src.poller import GovernancePoller
        poller = GovernancePoller(
            config_file=GOV_DIR / "config" / "chains.json",
        )
        signals = poller.poll_all()
        poller.close()
        return signals
    finally:
        sys.path = old_path


# ── Block Time Monitor ─────────────────────────────────────

def run_block_poll() -> list[dict]:
    """Run block time poll via subprocess to avoid import conflicts."""
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(BLOCK_DIR / "main.py"), "--json"],
            capture_output=True, text=True, timeout=60,
            cwd=str(BLOCK_DIR),
        )
        if result.returncode != 0:
            # No --json flag yet, run normal poll and check for signal files
            result = subprocess.run(
                [sys.executable, str(BLOCK_DIR / "main.py")],
                capture_output=True, text=True, timeout=60,
                cwd=str(BLOCK_DIR),
            )
            # Parse output for halt indicators
            signals = []
            for line in result.stdout.split("\n"):
                if "HALT" in line.upper():
                    logger.warning("Block monitor: %s", line.strip())
            return signals

        # Parse JSON output if available
        signals = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    signals.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return signals
    except subprocess.TimeoutExpired:
        logger.error("Block poll timed out")
        return []
    except Exception as e:
        logger.error("Block poll failed: %s", e)
        return []


# ── Main Loop ──────────────────────────────────────────────

def poll_once(run_gov: bool = True, run_block: bool = True):
    """Run all monitors once and send alerts."""
    now = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    if run_gov:
        logger.info("[%s] Governance poll starting...", now)
        try:
            gov_signals = run_governance_poll()
            for signal in gov_signals:
                msg = format_governance_signal(signal)
                send_telegram(msg, "P1")
                logger.info("Governance signal: %s %s", signal.get("ticker"), signal.get("upgrade_name"))
        except Exception as e:
            logger.error("Governance poll failed: %s", e)

    if run_block:
        logger.info("[%s] Block time poll starting...", now)
        try:
            block_signals = run_block_poll()
            for signal in block_signals:
                sig_type = signal.get("signal_type", "")
                if sig_type == "block_halt":
                    msg = format_block_halt_signal(signal)
                    send_telegram(msg, "P0")
                elif sig_type == "chain_resumed":
                    msg = format_chain_resumed_signal(signal)
                    send_telegram(msg, "P1")
                elif sig_type == "block_anomaly":
                    severity = signal.get("severity", "")
                    if severity in ("alert", "critical"):
                        msg = format_block_halt_signal(signal)
                        send_telegram(msg, "P2")
        except Exception as e:
            logger.error("Block poll failed: %s", e)


def run_loop(gov_interval: int = 600, block_interval: int = 10):
    """
    Continuous monitoring loop.
    - Governance: every gov_interval seconds (default 10 min)
    - Block time: every block_interval seconds (default 10 sec)
    """
    send_telegram(
        "🟢 <b>ChainPulse Monitor Started</b>\n\n"
        f"• Governance: 21 chains, every {gov_interval}s\n"
        f"• Block time: 21 chains, every {block_interval}s\n"
        f"• Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "P3",
    )

    last_gov_poll = 0
    poll_count = 0

    try:
        while True:
            now = time.time()
            poll_count += 1

            # Block time poll every cycle
            try:
                block_signals = run_block_poll()
                for signal in block_signals:
                    sig_type = signal.get("signal_type", "")
                    if sig_type == "block_halt":
                        send_telegram(format_block_halt_signal(signal), "P0")
                    elif sig_type == "chain_resumed":
                        send_telegram(format_chain_resumed_signal(signal), "P1")
                    elif sig_type == "block_anomaly" and signal.get("severity") in ("alert", "critical"):
                        send_telegram(format_block_halt_signal(signal), "P2")
            except Exception as e:
                logger.error("Block poll error: %s", e)

            # Governance poll at interval
            if now - last_gov_poll >= gov_interval:
                try:
                    gov_signals = run_governance_poll()
                    for signal in gov_signals:
                        send_telegram(format_governance_signal(signal), "P1")
                except Exception as e:
                    logger.error("Gov poll error: %s", e)
                last_gov_poll = now

            if poll_count % 360 == 0:  # ~every hour at 10s interval
                logger.info("Heartbeat: %d polls completed", poll_count)

            time.sleep(block_interval)

    except KeyboardInterrupt:
        send_telegram("🔴 <b>ChainPulse Monitor Stopped</b>", "P3")
        logger.info("Stopped by user.")


def main():
    parser = argparse.ArgumentParser(description="ChainPulse — Unified Monitor")
    parser.add_argument("--loop", action="store_true", help="Continuous monitoring")
    parser.add_argument("--gov-only", action="store_true", help="Governance only")
    parser.add_argument("--block-only", action="store_true", help="Block time only")
    parser.add_argument("--gov-interval", type=int, default=600, help="Governance poll interval in seconds (default: 600)")
    parser.add_argument("--block-interval", type=int, default=10, help="Block time poll interval in seconds (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--test", action="store_true", help="Send a test alert")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    if args.test:
        ok = send_telegram(
            "🧪 <b>ChainPulse Test Alert</b>\n\n"
            "If you see this, Telegram integration is working.\n"
            f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "P3",
        )
        print("Test message sent!" if ok else "Failed to send test message.")
        return

    run_gov = not args.block_only
    run_block = not args.gov_only

    if args.loop:
        logger.info("Starting continuous monitoring...")
        run_loop(
            gov_interval=args.gov_interval,
            block_interval=args.block_interval,
        )
    else:
        logger.info("Single poll...")
        poll_once(run_gov=run_gov, run_block=run_block)
        logger.info("Done.")


if __name__ == "__main__":
    main()
