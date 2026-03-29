"""Unit tests for the message formatter."""

import sys
import os
import unittest

# Ensure the src package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.formatter import format_message, PRIORITY_PREFIX


class TestFormatSignalDetected(unittest.TestCase):
    """Tests for signal_detected message formatting."""

    def setUp(self):
        self.signal = {
            "source": "02-GitHub Release (v4.0.0-athena)",
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
        }

    def test_contains_signal_tag(self):
        msg = format_message(self.signal)
        self.assertIn("[SIGNAL]", msg)

    def test_contains_orange_emoji_for_p1(self):
        msg = format_message(self.signal)
        self.assertTrue(msg.startswith(PRIORITY_PREFIX["P1"]))

    def test_contains_coin_info(self):
        msg = format_message(self.signal)
        self.assertIn("TT (ThunderCore)", msg)

    def test_contains_source(self):
        msg = format_message(self.signal)
        self.assertIn("02-GitHub Release (v4.0.0-athena)", msg)

    def test_contains_all_fields(self):
        msg = format_message(self.signal)
        for field in ["Target Grade", "Lead Time", "Direction", "Urgency",
                       "Estimated Size", "Detection Time", "Recommended Exchange"]:
            self.assertIn(field, msg)

    def test_no_p0_repeat_note(self):
        msg = format_message(self.signal)
        self.assertNotIn("P0 alert", msg)


class TestFormatCritical(unittest.TestCase):
    """Tests for P0 critical message formatting."""

    def setUp(self):
        self.signal = {
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
                ],
            },
        }

    def test_triple_red_emoji(self):
        msg = format_message(self.signal)
        triple_red = PRIORITY_PREFIX["P0_CRITICAL"]
        self.assertTrue(msg.startswith(triple_red))

    def test_contains_critical_tag(self):
        msg = format_message(self.signal)
        self.assertIn("[CRITICAL]", msg)

    def test_contains_exchange_and_chain(self):
        msg = format_message(self.signal)
        self.assertIn("Upbit", msg)
        self.assertIn("Solana", msg)

    def test_contains_actions(self):
        msg = format_message(self.signal)
        self.assertIn("No new long entries", msg)
        self.assertIn("Maintain existing position hold", msg)

    def test_contains_immediate_actions_header(self):
        msg = format_message(self.signal)
        self.assertIn("Immediate Actions", msg)

    def test_p0_repeat_alert_note(self):
        msg = format_message(self.signal)
        self.assertIn("P0 alert", msg)
        self.assertIn("Repeat alerts", msg)


class TestFormatPremiumUpdate(unittest.TestCase):
    """Tests for premium_update message formatting."""

    def setUp(self):
        self.signal = {
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
        }

    def test_yellow_emoji_for_p2(self):
        msg = format_message(self.signal)
        self.assertTrue(msg.startswith(PRIORITY_PREFIX["P2"]))

    def test_contains_premium_tag(self):
        msg = format_message(self.signal)
        self.assertIn("[PREMIUM]", msg)

    def test_contains_exchange_premiums(self):
        msg = format_message(self.signal)
        self.assertIn("Upbit: +34.2%", msg)
        self.assertIn("Bithumb: +89.5%", msg)

    def test_contains_peak_and_status(self):
        msg = format_message(self.signal)
        self.assertIn("Bithumb +95.0%", msg)
        self.assertIn("Rising", msg)


class TestFormatPositionOpen(unittest.TestCase):
    """Tests for position_open message formatting."""

    def test_position_open_format(self):
        signal = {
            "source": "09-position-manager",
            "priority": "P1",
            "type": "position_open",
            "data": {
                "coin": "TT",
                "domestic": "Bithumb spot long 10,000 @ 150 KRW",
                "overseas": "Binance futures short 10,000 @ $0.115",
                "quantity_match": "\u2705 100%",
                "liq_buffer": "200%+ \u2705",
                "total_deployed": "1,500,000 KRW + $345 margin",
            },
        }
        msg = format_message(signal)
        self.assertIn("[POSITION OPEN]", msg)
        self.assertIn("Delta Neutral", msg)
        self.assertIn("Bithumb spot long", msg)
        self.assertIn("Binance futures short", msg)


class TestFormatExitComplete(unittest.TestCase):
    """Tests for exit_complete message formatting."""

    def test_exit_complete_format(self):
        signal = {
            "source": "13-liquidation-engine",
            "priority": "P1",
            "type": "exit_complete",
            "data": {
                "coin": "TT",
                "exit_premium": "+107.0%",
                "domestic_sell": "Bithumb 10,000 @ 330 KRW",
                "overseas_close": "Binance @ $0.118",
                "net_profit": "1,759,500 KRW (+117.3%)",
                "execution_lag": "333ms \u2705",
                "funding_cost": "-$12.50",
                "trading_fees": "\u20a915,000",
                "final_net_profit": "1,727,750 KRW",
            },
        }
        msg = format_message(signal)
        self.assertIn("[EXIT]", msg)
        self.assertIn("Simultaneous Liquidation Complete", msg)
        self.assertIn("+107.0%", msg)
        self.assertIn("1,727,750 KRW", msg)


class TestFormatShortLiquidationRisk(unittest.TestCase):
    """Tests for short_liquidation_risk message formatting."""

    def test_liquidation_risk_format(self):
        signal = {
            "source": "15-risk-monitor",
            "priority": "P0",
            "type": "short_liquidation_risk",
            "data": {
                "coin": "TT",
                "exchange": "Binance",
                "current_price": "$0.280",
                "liquidation_price": "$0.345",
                "distance": "23.2% \u26a0\ufe0f",
                "margin_needed": "$500",
            },
        }
        msg = format_message(signal)
        self.assertIn("[RISK]", msg)
        self.assertIn("Approaching Short Liquidation Price", msg)
        self.assertIn("$0.280", msg)
        self.assertIn("$0.345", msg)
        self.assertIn("P0 alert", msg)


class TestFormatDailyReport(unittest.TestCase):
    """Tests for daily_report message formatting."""

    def test_daily_report_format(self):
        signal = {
            "source": "system",
            "priority": "P3",
            "type": "daily_report",
            "data": {
                "date": "2024-05-08",
                "active_positions": 3,
                "premium_status": "TT: +89.5%",
                "funding_fees": "-$45.20",
                "monitored_signals": 5,
                "signals_today": 2,
            },
        }
        msg = format_message(signal)
        self.assertIn("[DAILY REPORT]", msg)
        self.assertTrue(msg.startswith(PRIORITY_PREFIX["P3"]))
        self.assertIn("2024-05-08", msg)
        self.assertIn("3", msg)


class TestFormatGeneric(unittest.TestCase):
    """Tests for unknown event types (generic formatter)."""

    def test_generic_format(self):
        signal = {
            "source": "some-system",
            "priority": "P3",
            "type": "unknown_event",
            "data": {"foo": "bar", "count": 42},
        }
        msg = format_message(signal)
        self.assertIn("[UNKNOWN_EVENT]", msg)
        self.assertIn("foo: bar", msg)
        self.assertIn("count: 42", msg)


if __name__ == "__main__":
    unittest.main()
