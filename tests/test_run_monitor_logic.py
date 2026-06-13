from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_monitor  # noqa: E402


def _multi_chain_signal(status: str = "TEZOS_PROMOTION") -> dict:
    return {
        "chain_id": "tezos",
        "chain_name": "Tezos",
        "ticker": "XTZ",
        "proposal_id": "42_proto",
        "title": "Tezos protocol promotion",
        "status": status,
        "plan": {"name": "proto_42", "height": 12345},
    }


def test_multi_chain_dedup_only_returns_new_actionable_signals(tmp_path):
    state_file = tmp_path / "multi_chain_state.json"
    signal = _multi_chain_signal()

    first = run_monitor.filter_new_multi_chain_signals([signal], state_file=state_file)
    second = run_monitor.filter_new_multi_chain_signals([signal], state_file=state_file)

    assert first == [signal]
    assert second == []


def test_multi_chain_dedup_allows_status_change(tmp_path):
    state_file = tmp_path / "multi_chain_state.json"
    first_signal = _multi_chain_signal("TEZOS_EXPLORATION")
    second_signal = _multi_chain_signal("TEZOS_PROMOTION")

    first = run_monitor.filter_new_multi_chain_signals(
        [first_signal],
        state_file=state_file,
    )
    second = run_monitor.filter_new_multi_chain_signals(
        [second_signal],
        state_file=state_file,
    )

    assert first == [first_signal]
    assert second == [second_signal]


def test_multi_chain_non_actionable_signal_is_not_persisted(tmp_path):
    state_file = tmp_path / "multi_chain_state.json"
    signal = _multi_chain_signal("CURRENT")

    assert run_monitor.filter_new_multi_chain_signals([signal], state_file=state_file) == []
    assert not state_file.exists()
