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
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

import httpx

# Load .env
load_dotenv(Path(__file__).parent / ".env")

# ── Paths ──────────────────────────────────────────────────
ROOT = Path(__file__).parent
GOV_DIR = ROOT / "detection" / "01-governance-monitor"
GITHUB_DIR = ROOT / "detection" / "02-github-release-monitor"
BLOCK_DIR = ROOT / "detection" / "04-block-time-anomaly-detector"
MULTI_CHAIN_STATE_FILE = GOV_DIR / "data" / "detected_multi_chain_proposals.json"

sys.path.insert(0, str(GOV_DIR))
sys.path.insert(0, str(BLOCK_DIR))

logger = logging.getLogger("chainpulse")

# ── Telegram Sender ────────────────────────────────────────

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
EXCHANGE_NAME_MAP = {
    "upbit": "업비트",
    "bithumb": "빗썸",
}
MULTI_CHAIN_ACTIONABLE_STATUSES = {
    "UPGRADE_PENDING",
    "TEZOS_PROPOSAL",
    "TEZOS_EXPLORATION",
    "TEZOS_PROMOTION",
    "TEZOS_TESTING",
    "TEZOS_ADOPTION",
}


def is_multi_chain_actionable(signal: dict) -> bool:
    status = str(signal.get("status", ""))
    return status in MULTI_CHAIN_ACTIONABLE_STATUSES or "VOTING" in status.upper()


def _load_json_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        logger.warning("State file unreadable, reinitializing: %s", path)
        return {}


def _save_json_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def _multi_chain_signal_key(signal: dict) -> str:
    plan = signal.get("plan") or {}
    chain_id = signal.get("chain_id") or signal.get("chain_name") or signal.get("ticker") or "unknown"
    proposal_id = signal.get("proposal_id") or plan.get("name") or signal.get("title") or "unknown"
    status = signal.get("status") or "unknown"
    height = plan.get("height")
    return f"{chain_id}:{proposal_id}:{status}:{height}"


def filter_new_multi_chain_signals(
    signals: list[dict],
    state_file: Path = MULTI_CHAIN_STATE_FILE,
) -> list[dict]:
    """Return only newly seen actionable multi-chain governance signals."""
    state = _load_json_state(state_file)
    fresh: list[dict] = []
    changed = False

    for signal in signals:
        if not is_multi_chain_actionable(signal):
            continue
        key = _multi_chain_signal_key(signal)
        if key in state:
            continue
        state[key] = {
            "chain_id": signal.get("chain_id"),
            "ticker": signal.get("ticker"),
            "proposal_id": signal.get("proposal_id"),
            "status": signal.get("status"),
            "title": signal.get("title"),
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
        fresh.append(signal)
        changed = True

    if changed:
        _save_json_state(state_file, state)
    return fresh


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
    affected_tickers = signal.get("affected_tickers", [])
    exchanges_affected = signal.get("exchanges_affected", [])
    affected_label = ", ".join(affected_tickers)
    exchange_label = ", ".join(EXCHANGE_NAME_MAP.get(exchange, exchange) for exchange in exchanges_affected)

    status_map = {
        "PROPOSAL_STATUS_VOTING_PERIOD": "투표 중",
        "PROPOSAL_STATUS_PASSED": "통과",
    }
    status = status_map.get(signal.get("proposal_status", ""), signal.get("proposal_status", ""))

    lines = [
        "🟠 <b>[예상 입출금 정지]</b>",
        "",
        f"<b>{exchange_label}</b> 에서 <b>{affected_label}</b> 입출금 정지 가능성이 높습니다."
        if exchange_label and affected_label else "",
        f"체인: <b>{signal.get('chain', '')} ({signal.get('ticker', '')})</b>",
        f"영향 코인: <b>{affected_label}</b>" if affected_tickers else "",
        f"예상 거래소: {exchange_label}" if exchanges_affected else "",
        f"근거 프로포절: #{signal.get('proposal_id', '')} — {signal.get('proposal_title', '')}",
        f"현재 상태: {status}",
        f"업그레이드: {signal.get('upgrade_name', '')}",
        f"예상 타겟 블록: {signal.get('upgrade_height', 'N/A'):,}" if signal.get('upgrade_height') else "예상 타겟 블록: N/A",
        f"남은 블록: {signal.get('remaining_blocks', 0):,}" if signal.get('remaining_blocks') else "",
        f"예상 리드타임: <b>{lead:.1f}시간 ({lead_days:.1f}일)</b>" if lead else "",
        f"찬성률: {signal.get('vote_yes_pct', 0)}%",
        f"신뢰도: {signal.get('confidence', '')}",
        f"감지 시각: {signal.get('detected_at', '')[:19]}",
        "",
        "이 알림은 거래소 공지 전 사전 예측입니다.",
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


def format_multi_chain_signal(signal: dict) -> str:
    """Format non-Cosmos multi-chain governance signal for Telegram."""
    chain_type = signal.get("chain_type", "unknown").upper()
    ticker = signal.get("ticker", "")
    chain_name = signal.get("chain_name", chain_type)
    affected_tickers = signal.get("affected_tickers", [])
    exchanges_affected = signal.get("exchanges_affected", [])
    status = signal.get("status", "")
    plan = signal.get("plan", {})
    plan_name = plan.get("name", "N/A") if plan else "N/A"
    plan_height = plan.get("height") if plan else None
    yes_pct = signal.get("yes_pct", 0.0)

    # Classify by status to decide urgency
    actionable_statuses = {
        "UPGRADE_PENDING", "TEZOS_PROPOSAL", "TEZOS_EXPLORATION",
        "TEZOS_PROMOTION", "TEZOS_TESTING", "TEZOS_ADOPTION",
    }
    is_actionable = status in actionable_statuses or "VOTING" in status.upper()
    emoji = "\U0001f7e0" if is_actionable else "\U0001f535"  # orange vs blue

    lines = [
        f"{emoji} <b>[MULTI-CHAIN GOV] {chain_name} ({ticker})</b>",
        "",
        f"Type: {chain_type}",
        f"Affected: <b>{', '.join(affected_tickers)}</b>" if affected_tickers else "",
        f"Exchanges: {', '.join(exchanges_affected)}" if exchanges_affected else "",
        f"Proposal: #{signal.get('proposal_id', 'N/A')}",
        f"Title: {signal.get('title', 'N/A')}",
        f"Status: <b>{status}</b>",
        f"Plan: {plan_name}",
    ]
    if plan_height:
        lines.append(f"Target Height: {plan_height:,}")
    if yes_pct and yes_pct > 0:
        lines.append(f"Approval: {yes_pct:.1f}%")
    if signal.get("submit_time"):
        lines.append(f"Submitted: {str(signal.get('submit_time', ''))[:19]}")
    if signal.get("voting_end_time"):
        lines.append(f"Voting End: {str(signal.get('voting_end_time', ''))[:19]}")

    lines.append(f"Detected: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')}")

    if is_actionable:
        lines.extend(["", "\u26a0\ufe0f <b>Action may be required — governance activity detected.</b>"])

    return "\n".join(lines)


def format_github_release_signal(signal: dict) -> str:
    """Format GitHub release signal for Telegram."""
    level = signal.get("signal_level", "alert")
    emoji = "🟡" if level == "pre-warning" else "🟠"
    mandatory = "YES" if signal.get("is_mandatory") else "no"
    pre = "yes" if signal.get("is_prerelease") else "no"

    lines = [
        f"{emoji} <b>[GITHUB] Release Detected</b>",
        "",
        f"Chain: <b>{signal.get('chain', '')} ({signal.get('ticker', '')})</b>",
        f"Repo: {signal.get('repo', '')}",
        f"Tag: <b>{signal.get('release_tag', '')}</b>",
        f"Title: {signal.get('release_title', '')}",
    ]
    if signal.get("keywords_matched"):
        lines.append(f"Keywords: {', '.join(signal['keywords_matched'])}")
    version_jump = signal.get("version_jump")
    if version_jump:
        if isinstance(version_jump, dict):
            version_text = version_jump.get("description") or version_jump.get("type", "")
        else:
            version_text = str(version_jump)
        if version_text:
            lines.append(f"Version: {version_text}")
    lines.extend([
        f"Mandatory: {mandatory}",
        f"Pre-release: {pre}",
        f"Confidence: {signal.get('confidence', '')}",
        f"Published: {str(signal.get('published_at', ''))[:19]}",
    ])
    if signal.get("release_url"):
        lines.append(f"URL: {signal['release_url']}")

    if mandatory == "YES":
        lines.extend(["", "⚠️ <b>Mandatory upgrade — exchange deposit/withdrawal suspension expected.</b>"])

    return "\n".join(lines)


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
    # Import the governance poller and its dependencies from the module's src/ dir.
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


# ── Multi-Chain Governance Monitor ─────────────────────────

def run_github_release_poll() -> list[dict]:
    """Poll GitHub releases via subprocess."""
    import subprocess
    script = """
import json, sys, os, io
sys.path.insert(0, ".")
os.environ.setdefault("GITHUB_TOKEN", sys.argv[2] if len(sys.argv) > 2 else "")
import logging
logging.disable(logging.CRITICAL)
_real_stdout = sys.stdout
sys.stdout = io.StringIO()
from src.poller import ReleasePoller
poller = ReleasePoller()
signals = poller.poll_all()
poller.close()
sys.stdout = _real_stdout
print(json.dumps(signals))
"""
    github_token = os.getenv("GITHUB_TOKEN", "")
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, str(GITHUB_DIR / "config" / "repos.json"), github_token],
            capture_output=True, text=True, timeout=120,
            cwd=str(GITHUB_DIR),
        )
        if result.returncode != 0:
            logger.error("GitHub poll stderr: %s", result.stderr.strip()[:200])
            return []

        output = result.stdout.strip()
        if not output:
            return []
        signals = json.loads(output)
        return signals if isinstance(signals, list) else []
    except subprocess.TimeoutExpired:
        logger.error("GitHub release poll timed out")
        return []
    except Exception as e:
        logger.error("GitHub release poll failed: %s", e)
        return []


def run_multi_chain_governance_poll() -> list[dict]:
    """Poll all 8 non-Cosmos chains via subprocess to avoid src/ namespace collision."""
    import subprocess

    # Inline script that imports multi_chain_client from the governance monitor's src/
    script = """
import json, sys
sys.path.insert(0, ".")
from src.impact_scope import build_impact_scope
from src.multi_chain_client import MultiChainGovernanceClient

config_path = sys.argv[1]
with open(config_path) as f:
    config = json.load(f)

results = []
for chain_cfg in config.get("chains", []):
    client = MultiChainGovernanceClient(chain_cfg)
    impact_scope = build_impact_scope(chain_cfg)
    try:
        proposals = client.fetch_upgrade_proposals()
        for p in proposals:
            p["chain_id"] = chain_cfg["chain_id"]
            p["ticker"] = chain_cfg["ticker"]
            p["chain_name"] = chain_cfg["name"]
            p["affected_tickers"] = impact_scope["affected_tickers"]
            p["exchanges_affected"] = impact_scope["exchanges_affected"]
        results.extend(proposals)
    finally:
        client.close()

print(json.dumps(results))
"""
    config_file = str(GOV_DIR / "config" / "multi_chains.json")
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, config_file],
            capture_output=True, text=True, timeout=120,
            cwd=str(GOV_DIR),
        )
        if result.returncode != 0:
            logger.error("Multi-chain poll stderr: %s", result.stderr.strip())
            return []

        output = result.stdout.strip()
        if not output:
            return []
        proposals = json.loads(output)
        return proposals if isinstance(proposals, list) else []
    except subprocess.TimeoutExpired:
        logger.error("Multi-chain governance poll timed out")
        return []
    except Exception as e:
        logger.error("Multi-chain governance poll failed: %s", e)
        return []


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

        logger.info("[%s] GitHub release poll starting...", now)
        try:
            gh_signals = run_github_release_poll()
            for signal in gh_signals:
                msg = format_github_release_signal(signal)
                level = signal.get("signal_level", "alert")
                if level == "pre-warning":
                    send_telegram(msg, "P2")
                else:
                    send_telegram(msg, "P1")
                logger.info("GitHub: %s %s [%s]", signal.get("ticker"), signal.get("release_tag"), level)
        except Exception as e:
            logger.error("GitHub release poll failed: %s", e)

        logger.info("[%s] Multi-chain governance poll starting...", now)
        try:
            mc_signals = filter_new_multi_chain_signals(
                run_multi_chain_governance_poll()
            )
            for signal in mc_signals:
                msg = format_multi_chain_signal(signal)
                send_telegram(msg, "P1")
                status = signal.get("status", "")
                logger.info("Multi-chain: %s %s [%s]", signal.get("ticker"), signal.get("title", "")[:60], status)
        except Exception as e:
            logger.error("Multi-chain governance poll failed: %s", e)

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
        f"• Governance (Cosmos): 13 chains, every {gov_interval}s\n"
        f"• Governance (Multi-chain): 8 chains, every {gov_interval}s\n"
        f"• GitHub releases: 34 repos, every {gov_interval}s\n"
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

            # Governance poll at interval (Cosmos + Multi-chain)
            if now - last_gov_poll >= gov_interval:
                try:
                    gov_signals = run_governance_poll()
                    for signal in gov_signals:
                        send_telegram(format_governance_signal(signal), "P1")
                except Exception as e:
                    logger.error("Gov poll error: %s", e)

                try:
                    mc_signals = filter_new_multi_chain_signals(
                        run_multi_chain_governance_poll()
                    )
                    for signal in mc_signals:
                        send_telegram(format_multi_chain_signal(signal), "P1")
                except Exception as e:
                    logger.error("Multi-chain gov poll error: %s", e)

                try:
                    gh_signals = run_github_release_poll()
                    for signal in gh_signals:
                        level = signal.get("signal_level", "alert")
                        msg = format_github_release_signal(signal)
                        send_telegram(msg, "P2" if level == "pre-warning" else "P1")
                except Exception as e:
                    logger.error("GitHub release poll error: %s", e)

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
