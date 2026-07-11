"""Quantitative halt detector tests."""

import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from peaq_watch.runtime_head_source import RuntimeHeadSource
from peaq_watch.state_store import StateStore


def _target():
    return {
        "chain_id": "peaq",
        "chain_name": "peaq",
        "primary_ticker": "PEAQ",
        "affected_tickers": ["PEAQ"],
        "listed_on": ["bithumb"],
        "sources": {
            "runtime_head": {
                "observe_stall_rounds": 2,
                "warning_stall_rounds": 3,
                "critical_stall_rounds": 5,
                "recovery_healthy_rounds": 3,
                "observe_head_age_seconds": 12.0,
                "warning_head_age_seconds": 24.0,
                "critical_head_age_seconds": 45.0,
                "observe_finalized_age_seconds": 18.0,
                "critical_finalized_age_seconds": 30.0,
                "divergence_blocks": 2,
                "http_endpoints": ["https://quicknode1.peaq.xyz"],
            }
        },
    }


def _snapshot(
    ts: str,
    latest_head: int,
    finalized_head: int,
    head_age: float,
    finalized_age: float,
    spread: int = 0,
):
    primary = [
        {
            "url": "https://quicknode1.peaq.xyz",
            "latest_head_number": latest_head,
            "finalized_head_number": finalized_head,
            "latest_block_timestamp": 1000,
            "finalized_block_timestamp": 990,
            "head_age_sec": head_age,
            "finalized_age_sec": finalized_age,
            "latest_lag_sec": head_age,
            "finalized_lag_sec": finalized_age,
            "finality_gap_blocks": max(0, latest_head - finalized_head),
            "error": None,
        },
        {
            "url": "https://quicknode2.peaq.xyz",
            "latest_head_number": latest_head,
            "finalized_head_number": finalized_head,
            "latest_block_timestamp": 1000,
            "finalized_block_timestamp": 990,
            "head_age_sec": head_age,
            "finalized_age_sec": finalized_age,
            "latest_lag_sec": head_age,
            "finalized_lag_sec": finalized_age,
            "finality_gap_blocks": max(0, latest_head - finalized_head),
            "error": None,
        },
        {
            "url": "https://quicknode3.peaq.xyz",
            "latest_head_number": latest_head,
            "finalized_head_number": finalized_head,
            "latest_block_timestamp": 1000,
            "finalized_block_timestamp": 990,
            "head_age_sec": head_age,
            "finalized_age_sec": finalized_age,
            "latest_lag_sec": head_age,
            "finalized_lag_sec": finalized_age,
            "finality_gap_blocks": max(0, latest_head - finalized_head),
            "error": None,
        },
    ]
    return {
        "timestamp_utc": ts,
        "primary_mode": "http",
        "majority_threshold": 2,
        "primary_samples": primary,
        "http_samples": primary,
        "quorum_head_number": latest_head,
        "quorum_head_age_sec": head_age,
        "quorum_finalized_age_sec": finalized_age,
        "quorum_finality_gap_blocks": max(0, latest_head - finalized_head),
        "endpoint_spread": spread,
        "http_error_count": 0,
    }


def test_warning_critical_and_recovery_progression():
    snapshots = iter(
        [
            _snapshot("2026-04-08T00:00:00+00:00", 100, 95, 5.0, 5.0),
            _snapshot("2026-04-08T00:00:05+00:00", 100, 95, 14.0, 20.0),
            _snapshot("2026-04-08T00:00:10+00:00", 100, 95, 26.0, 28.0),
            _snapshot("2026-04-08T00:00:15+00:00", 100, 95, 33.0, 35.0),
            _snapshot("2026-04-08T00:00:20+00:00", 100, 95, 50.0, 40.0),
            _snapshot("2026-04-08T00:00:25+00:00", 100, 95, 58.0, 48.0),
            _snapshot("2026-04-08T00:00:30+00:00", 101, 96, 2.0, 2.0),
            _snapshot("2026-04-08T00:00:35+00:00", 102, 97, 2.0, 2.0),
            _snapshot("2026-04-08T00:00:40+00:00", 103, 98, 2.0, 2.0),
        ]
    )

    def provider(target, cfg):
        return next(snapshots)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(state_file=Path(tmpdir) / "state.json")
        source = RuntimeHeadSource(state_store=store, snapshot_provider=provider)
        target = _target()

        assert source.collect(target) == []
        assert source.collect(target) == []
        assert source.collect(target) == []

        warning = source.collect(target)
        assert len(warning) == 1
        assert warning[0]["stage"] == "warning"

        assert source.collect(target) == []

        critical = source.collect(target)
        assert len(critical) == 1
        assert critical[0]["stage"] == "critical"

        assert source.collect(target) == []
        assert source.collect(target) == []

        recovery = source.collect(target)
        assert len(recovery) == 1
        assert recovery[0]["stage"] == "recovery"

        source.close()


def test_divergence_only_sets_observe_without_alert():
    snapshots = iter(
        [
            _snapshot("2026-04-08T00:00:00+00:00", 100, 95, 3.0, 3.0, spread=0),
            _snapshot("2026-04-08T00:00:05+00:00", 101, 96, 3.0, 3.0, spread=5),
        ]
    )

    def provider(target, cfg):
        return next(snapshots)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(state_file=Path(tmpdir) / "state.json")
        source = RuntimeHeadSource(state_store=store, snapshot_provider=provider)
        target = _target()

        assert source.collect(target) == []
        assert source.collect(target) == []
        state = store.get_namespace("runtime_head:peaq")
        assert state["current_level"] == "observe"

        source.close()


def test_observe_only_recovery_does_not_emit_recovery_event():
    snapshots = iter(
        [
            _snapshot("2026-04-08T00:00:00+00:00", 100, 95, 3.0, 3.0, spread=0),
            _snapshot("2026-04-08T00:00:05+00:00", 100, 95, 24.0, 24.0, spread=0),
            _snapshot("2026-04-08T00:00:10+00:00", 101, 96, 1.0, 20.0, spread=0),
            _snapshot("2026-04-08T00:00:15+00:00", 102, 97, 1.0, 20.0, spread=0),
            _snapshot("2026-04-08T00:00:20+00:00", 103, 98, 1.0, 20.0, spread=0),
        ]
    )

    def provider(target, cfg):
        return next(snapshots)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(state_file=Path(tmpdir) / "state.json")
        source = RuntimeHeadSource(state_store=store, snapshot_provider=provider)
        target = _target()

        assert source.collect(target) == []
        assert source.collect(target) == []
        assert source.collect(target) == []
        assert source.collect(target) == []
        assert source.collect(target) == []

        state = store.get_namespace("runtime_head:peaq")
        assert state["current_level"] == "healthy"
        assert state["incident_id"] is None

        source.close()
