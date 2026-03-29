"""Unit tests for the dedup filter."""

import sys
import os
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.dedup import DedupFilter


class TestDedupBasic(unittest.TestCase):
    """Test basic time-window deduplication."""

    def setUp(self):
        self.dedup = DedupFilter(window_seconds=3600)

    def test_first_signal_passes(self):
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        self.assertTrue(self.dedup.should_send(signal))

    def test_duplicate_within_window_blocked(self):
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        self.assertTrue(self.dedup.should_send(signal))
        self.assertFalse(self.dedup.should_send(signal))

    def test_different_ticker_passes(self):
        signal_tt = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        signal_eth = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "ETH"},
        }
        self.assertTrue(self.dedup.should_send(signal_tt))
        self.assertTrue(self.dedup.should_send(signal_eth))

    def test_different_event_type_passes(self):
        signal_a = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        signal_b = {
            "priority": "P1",
            "type": "position_open",
            "data": {"ticker": "TT"},
        }
        self.assertTrue(self.dedup.should_send(signal_a))
        self.assertTrue(self.dedup.should_send(signal_b))

    def test_expired_entry_passes_again(self):
        # Use a very short window
        dedup = DedupFilter(window_seconds=0)
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        self.assertTrue(dedup.should_send(signal))
        # With 0-second window, the next call should also pass
        self.assertTrue(dedup.should_send(signal))


class TestDedupP0Exception(unittest.TestCase):
    """Test that P0 signals always pass dedup."""

    def setUp(self):
        self.dedup = DedupFilter(window_seconds=3600)

    def test_p0_always_passes(self):
        signal = {
            "priority": "P0",
            "type": "hack_detected",
            "data": {"ticker": "EXCHANGE"},
        }
        self.assertTrue(self.dedup.should_send(signal))
        self.assertTrue(self.dedup.should_send(signal))
        self.assertTrue(self.dedup.should_send(signal))

    def test_p0_critical_always_passes(self):
        signal = {
            "priority": "P0",
            "type": "short_liquidation_risk",
            "data": {"ticker": "TT"},
        }
        for _ in range(5):
            self.assertTrue(self.dedup.should_send(signal))


class TestDedupPremiumStep(unittest.TestCase):
    """Test premium step-based deduplication."""

    def setUp(self):
        self.dedup = DedupFilter(window_seconds=3600, premium_step_pct=10.0)

    def _make_premium_signal(self, ticker, premium_val):
        return {
            "priority": "P2",
            "type": "premium_update",
            "data": {
                "ticker": ticker,
                "premiums": {"Bithumb": f"+{premium_val}%"},
            },
        }

    def test_first_premium_passes(self):
        signal = self._make_premium_signal("TT", 35.0)
        self.assertTrue(self.dedup.should_send(signal))

    def test_same_step_blocked(self):
        # 35% and 37% are both in the 30-40% step (step index 3)
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 35.0)))
        self.assertFalse(self.dedup.should_send(self._make_premium_signal("TT", 37.0)))

    def test_next_step_passes(self):
        # 35% -> step 3, 45% -> step 4
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 35.0)))
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 45.0)))

    def test_crossing_multiple_steps(self):
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 15.0)))
        self.assertFalse(self.dedup.should_send(self._make_premium_signal("TT", 18.0)))
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 25.0)))
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 55.0)))

    def test_different_tickers_independent(self):
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("TT", 35.0)))
        self.assertTrue(self.dedup.should_send(self._make_premium_signal("ETH", 35.0)))

    def test_premium_with_percent_sign_parsing(self):
        signal = {
            "priority": "P2",
            "type": "premium_update",
            "data": {
                "ticker": "TT",
                "premiums": {"Upbit": "+34.2%", "Bithumb": "+89.5%"},
            },
        }
        self.assertTrue(self.dedup.should_send(signal))
        # Max is 89.5, step 8. Sending 92% (still step 9) should pass since 89->9, 92->9 is same
        # Actually 89.5/10 = 8, 92/10 = 9, different steps
        signal2 = {
            "priority": "P2",
            "type": "premium_update",
            "data": {
                "ticker": "TT",
                "premiums": {"Upbit": "+34.2%", "Bithumb": "+92.0%"},
            },
        }
        self.assertTrue(self.dedup.should_send(signal2))


class TestDedupCoinFieldFallback(unittest.TestCase):
    """Test that dedup works with 'coin' field when 'ticker' is absent."""

    def test_coin_field_used_as_fallback(self):
        dedup = DedupFilter(window_seconds=3600)
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"coin": "TT"},
        }
        self.assertTrue(dedup.should_send(signal))
        self.assertFalse(dedup.should_send(signal))


class TestDedupClear(unittest.TestCase):
    """Test clearing dedup state."""

    def test_clear_resets_state(self):
        dedup = DedupFilter(window_seconds=3600)
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        dedup.should_send(signal)
        self.assertFalse(dedup.should_send(signal))

        dedup.clear()
        self.assertTrue(dedup.should_send(signal))


class TestDedupCleanup(unittest.TestCase):
    """Test cleanup of expired entries."""

    def test_cleanup_removes_expired(self):
        dedup = DedupFilter(window_seconds=0)
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        dedup.should_send(signal)
        removed = dedup.cleanup_expired()
        self.assertEqual(removed, 1)

    def test_cleanup_keeps_fresh(self):
        dedup = DedupFilter(window_seconds=9999)
        signal = {
            "priority": "P1",
            "type": "signal_detected",
            "data": {"ticker": "TT"},
        }
        dedup.should_send(signal)
        removed = dedup.cleanup_expired()
        self.assertEqual(removed, 0)


if __name__ == "__main__":
    unittest.main()
