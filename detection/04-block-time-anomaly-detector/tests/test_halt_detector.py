"""
Unit tests for the HaltDetector — uses mock data only, no live RPC calls.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.halt_detector import HaltDetector
from src.signal_emitter import SignalEmitter
from src.state_store import StateStore
import main as block_main
from src.chain_monitor import AnomalyLevel, BlockInfo, ChainStatus


class TestHaltDetector:
    """Test halt detection logic with mock observations."""

    def test_no_halt_when_height_advances(self):
        """Height increases each poll — no halt should be detected."""
        detector = HaltDetector(consecutive_threshold=3)
        for h in range(100, 110):
            rec = detector.observe("test_chain", h)
        assert not rec.halt_confirmed
        assert rec.consecutive_stalls == 1

    def test_halt_confirmed_after_threshold(self):
        """Same height for 3 consecutive polls should confirm a halt."""
        detector = HaltDetector(consecutive_threshold=3)
        # First observation sets the baseline
        detector.observe("test_chain", 500)
        # Second observation — same height
        detector.observe("test_chain", 500)
        # Third observation — same height, should confirm halt
        rec = detector.observe("test_chain", 500)
        assert rec.halt_confirmed
        assert rec.stalled_height == 500
        assert rec.halt_type in ("expected", "unexpected")

    def test_no_halt_below_threshold(self):
        """Same height for fewer than threshold polls should NOT confirm."""
        detector = HaltDetector(consecutive_threshold=3)
        detector.observe("test_chain", 500)
        rec = detector.observe("test_chain", 500)
        assert not rec.halt_confirmed
        assert rec.consecutive_stalls == 2

    def test_stall_resets_on_new_height(self):
        """A new height observation should reset the stall counter."""
        detector = HaltDetector(consecutive_threshold=3)
        detector.observe("test_chain", 500)
        detector.observe("test_chain", 500)
        # Height changes — reset
        rec = detector.observe("test_chain", 501)
        assert not rec.halt_confirmed
        assert rec.consecutive_stalls == 1

    def test_resume_after_halt(self):
        """After halt is confirmed, a new height means the chain resumed."""
        detector = HaltDetector(consecutive_threshold=3)
        detector.observe("test_chain", 500)
        detector.observe("test_chain", 500)
        detector.observe("test_chain", 500)

        # Confirm halted
        assert detector.is_halted("test_chain")

        # Now height advances — resume
        rec = detector.observe("test_chain", 501)
        assert rec.resumed
        assert not rec.halt_confirmed
        assert rec.resumed_at is not None

    def test_none_height_skipped(self):
        """None height (RPC failure) should not affect stall count."""
        detector = HaltDetector(consecutive_threshold=3)
        detector.observe("test_chain", 500)
        rec = detector.observe("test_chain", None)
        assert rec.consecutive_stalls == 1  # unchanged from first observe

    def test_multiple_chains_independent(self):
        """Each chain has independent halt tracking."""
        detector = HaltDetector(consecutive_threshold=3)
        for _ in range(3):
            detector.observe("chain_a", 100)
        for h in range(200, 205):
            detector.observe("chain_b", h)

        assert detector.is_halted("chain_a")
        assert not detector.is_halted("chain_b")

    def test_custom_threshold(self):
        """Custom threshold value should be respected."""
        detector = HaltDetector(consecutive_threshold=5)
        for _ in range(4):
            detector.observe("test_chain", 500)
        assert not detector.is_halted("test_chain")

        detector.observe("test_chain", 500)
        assert detector.is_halted("test_chain")

    def test_reset(self):
        """Reset should clear tracking for a chain."""
        detector = HaltDetector(consecutive_threshold=3)
        for _ in range(3):
            detector.observe("test_chain", 500)
        assert detector.is_halted("test_chain")

        detector.reset("test_chain")
        assert not detector.is_halted("test_chain")
        assert detector.get_record("test_chain") is None

    def test_is_halted_unknown_chain(self):
        """is_halted should return False for unknown chains."""
        detector = HaltDetector()
        assert not detector.is_halted("nonexistent")


class _StaticHeightMonitor:
    chain_id = "test_chain"
    name = "Test Chain"
    ticker = "TST"
    rpc_type = "mock"
    avg_block_time = 1.0
    tickers_affected = ["TST"]

    def __init__(self, height: int):
        self.height = height

    def poll(self):
        block = BlockInfo(
            height=self.height,
            timestamp=1_700_000_000.0,
            chain_id=self.chain_id,
        )
        return ChainStatus(
            chain_id=self.chain_id,
            chain_name=self.name,
            ticker=self.ticker,
            rpc_type=self.rpc_type,
            latest_block=block,
            avg_block_time=self.avg_block_time,
            anomaly_level=AnomalyLevel.CRITICAL,
            seconds_since_last_block=120.0,
        )


def test_halt_state_survives_short_lived_subprocess_style_polls(tmp_path):
    state_store = StateStore(state_file=tmp_path / "chain_state.json")
    signals_dir = tmp_path / "signals"

    for attempt in range(3):
        detector = HaltDetector(consecutive_threshold=3)
        emitter = SignalEmitter(signals_dir=signals_dir)
        block_main.poll_all(
            [_StaticHeightMonitor(500)],
            detector,
            emitter,
            state_store,
        )
        emitted = emitter.get_emitted()
        if attempt < 2:
            assert emitted == []
        else:
            assert len(emitted) == 1
            assert emitted[0]["signal_type"] == "block_halt"
            assert emitted[0]["chain"] == "test_chain"

    # A fourth short-lived poll at the same height should not duplicate the halt.
    detector = HaltDetector(consecutive_threshold=3)
    emitter = SignalEmitter(signals_dir=signals_dir)
    block_main.poll_all(
        [_StaticHeightMonitor(500)],
        detector,
        emitter,
        state_store,
    )
    assert emitter.get_emitted() == []


def test_persisted_halt_resumes_from_new_height(tmp_path):
    state_store = StateStore(state_file=tmp_path / "chain_state.json")
    signals_dir = tmp_path / "signals"

    for _ in range(3):
        block_main.poll_all(
            [_StaticHeightMonitor(500)],
            HaltDetector(consecutive_threshold=3),
            SignalEmitter(signals_dir=signals_dir),
            state_store,
        )

    emitter = SignalEmitter(signals_dir=signals_dir)
    block_main.poll_all(
        [_StaticHeightMonitor(501)],
        HaltDetector(consecutive_threshold=3),
        emitter,
        state_store,
    )

    emitted = emitter.get_emitted()
    assert len(emitted) == 1
    assert emitted[0]["signal_type"] == "chain_resumed"
    assert emitted[0]["chain"] == "test_chain"


def run_tests():
    """Run all tests and report results."""
    test = TestHaltDetector()
    methods = [m for m in dir(test) if m.startswith("test_")]
    passed = 0
    failed = 0

    for method_name in methods:
        try:
            getattr(test, method_name)()
            print(f"  PASS  {method_name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {method_name}: {e}")
            failed += 1

    print(f"\nHalt Detector Tests: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
