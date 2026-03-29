"""Notification system entry point.

Can be imported by other systems:
    from infra.notification_system.src.notifier import Notifier

Or run standalone for testing:
    python main.py --test
    python main.py --test --chat-id YOUR_CHAT_ID
"""

import argparse
import logging
import sys

from src.notifier import Notifier
from src.telegram_bot import TelegramBot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def send_test_signal(notifier: Notifier) -> None:
    """Send a set of test signals covering all priority levels."""
    test_signals = [
        {
            "source": "02-github-monitor",
            "priority": "P1",
            "type": "signal_detected",
            "data": {
                "title": "Network Upgrade Detected",
                "coin": "TT (ThunderCore)",
                "ticker": "TT",
                "grade": "S (92 points)",
                "lead_time": "~6 days",
                "exchange": "Bithumb",
                "direction": "Long + Short",
                "urgency": "prepare (start split buying)",
                "size": "10M KRW (10% of capital)",
                "detection_time": "2024-05-08 01:00 KST",
            },
        },
        {
            "source": "12-premium-tracker",
            "priority": "P2",
            "type": "premium_update",
            "data": {
                "coin": "TT",
                "ticker": "TT",
                "premiums": {
                    "Upbit": "+34.2%",
                    "Bithumb": "+89.5%",
                },
                "peak": "Bithumb +95.0%",
                "status": "Rising",
                "recommendation": "Maintain hold",
            },
        },
        {
            "source": "16-hack-detector",
            "priority": "P0",
            "type": "hack_detected",
            "data": {
                "title": "Abnormal Hot Wallet Withdrawal Detected",
                "exchange": "Upbit",
                "chain": "Solana",
                "amount": "~44.5B KRW ($34M)",
                "receiving_address": "Unidentified (Gq3x...)",
                "detection_time": "04:42 KST",
                "actions": [
                    "No new long entries",
                    "Maintain existing position hold",
                    "Confirm overseas short maintained",
                    "Prepare for reverse premium additional buy",
                ],
            },
        },
        {
            "source": "system",
            "priority": "P3",
            "type": "daily_report",
            "data": {
                "date": "2024-05-08",
                "active_positions": 3,
                "premium_status": "TT: +89.5%, ETH: +2.1%",
                "funding_fees": "-$45.20",
                "monitored_signals": 5,
                "signals_today": 2,
            },
        },
    ]

    logger.info("Sending %d test signals...", len(test_signals))
    for signal in test_signals:
        try:
            results = notifier.send(signal)
            logger.info(
                "  %s/%s -> %d message(s) sent",
                signal["priority"],
                signal["type"],
                len(results),
            )
        except Exception:
            logger.exception(
                "  Failed to send %s/%s",
                signal["priority"],
                signal["type"],
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Notification System")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Send test messages to verify the system works.",
    )
    parser.add_argument(
        "--chat-id",
        type=str,
        default=None,
        help="Override chat ID for test messages.",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Send a single test message to verify bot connectivity.",
    )
    args = parser.parse_args()

    if args.test_connection:
        if not args.chat_id:
            logger.error("--chat-id is required for --test-connection")
            sys.exit(1)
        bot = TelegramBot()
        result = bot.send_test_message(args.chat_id)
        logger.info("Test connection result: %s", result)
        return

    if args.test:
        notifier = Notifier()
        send_test_signal(notifier)
        return

    logger.info(
        "Notification system initialized. Import and use Notifier in your pipeline."
    )
    logger.info("Run with --test to send test signals, or --test-connection --chat-id <id>.")


if __name__ == "__main__":
    main()
