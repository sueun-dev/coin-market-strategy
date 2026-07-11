"""Monitor orchestration tests."""

import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitor import SuspensionMonitor
from src.signal_store import SignalStore
from src.state_store import StateStore


class FakeGitHubSource:
    def collect(self, target, default_recent_release_hours):
        if target["chain_id"] != "injective":
            return []
        return [
            {
                "event_key": "injective:repo:v1.18.3",
                "event_reference": "v1.18.3",
                "source_type": "github_release",
                "stage": "early",
                "cause_type": "network_upgrade",
                "title": "v1.18.3",
                "summary": "Mainnet upgrade",
                "confidence_hint": "medium",
                "network_event_time": None,
                "network_event_height": None,
                "evidence_links": ["https://github.com/example"],
                "metadata": {"repo": "InjectiveFoundation/injective-core"},
            }
        ]

    def close(self):
        return None


class FakeGovernanceSource:
    def collect(self, target):
        return []

    def close(self):
        return None


def test_monitor_emits_and_dedupes():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "targets.json"
        config_path.write_text(
            json.dumps(
                {
                    "defaults": {"recent_release_hours": 168},
                    "exchange_profiles": {
                        "upbit": {
                            "network_upgrade": {
                                "min_lead_hours": 1,
                                "default_lead_hours": 24,
                                "max_lead_hours": 168,
                            }
                        }
                    },
                    "targets": [
                        {
                            "chain_id": "injective",
                            "chain_name": "Injective",
                            "primary_ticker": "INJ",
                            "affected_tickers": ["INJ"],
                            "listed_on": ["upbit"],
                            "sources": {
                                "github_release": {
                                    "repo": "InjectiveFoundation/injective-core"
                                }
                            },
                        }
                    ],
                }
            )
        )
        state_store = StateStore(state_file=Path(tmpdir) / "state.json")
        signal_store = SignalStore(signals_dir=Path(tmpdir) / "signals")
        monitor = SuspensionMonitor(
            config_file=str(config_path),
            state_store=state_store,
            signal_store=signal_store,
            github_source=FakeGitHubSource(),
            governance_source=FakeGovernanceSource(),
        )
        signals_first = monitor.poll_all()
        signals_second = monitor.poll_all()
        monitor.close()
        assert len(signals_first) == 1
        assert len(signals_second) == 0


def test_monitor_skips_targets_without_exchange_forecast():
    class NoExchangeGitHubSource:
        def collect(self, target, default_recent_release_hours):
            return [
                {
                    "event_key": "solana:repo:v3.1.12",
                    "event_reference": "v3.1.12",
                    "source_type": "github_release",
                    "stage": "early",
                    "cause_type": "network_upgrade",
                    "title": "Release v3.1.12",
                    "summary": "Mainnet upgrade",
                    "confidence_hint": "medium",
                    "network_event_time": None,
                    "network_event_height": None,
                    "evidence_links": ["https://github.com/example"],
                    "metadata": {"repo": "anza-xyz/agave"},
                }
            ]

        def close(self):
            return None

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "targets.json"
        config_path.write_text(
            json.dumps(
                {
                    "defaults": {"recent_release_hours": 168},
                    "exchange_profiles": {},
                    "targets": [
                        {
                            "chain_id": "solana",
                            "chain_name": "Solana",
                            "primary_ticker": "SOL",
                            "affected_tickers": ["SOL"],
                            "listed_on": [],
                            "sources": {"github_release": {"repo": "anza-xyz/agave"}},
                        }
                    ],
                }
            )
        )
        state_store = StateStore(state_file=Path(tmpdir) / "state.json")
        signal_store = SignalStore(signals_dir=Path(tmpdir) / "signals")
        monitor = SuspensionMonitor(
            config_file=str(config_path),
            state_store=state_store,
            signal_store=signal_store,
            github_source=NoExchangeGitHubSource(),
            governance_source=FakeGovernanceSource(),
        )
        signals_first = monitor.poll_all()
        signals_second = monitor.poll_all()
        state = state_store.get_all()
        monitor.close()
        assert signals_first == []
        assert signals_second == []
        assert len(state) == 1


def test_monitor_records_source_errors_instead_of_hiding_them():
    class FailingGitHubSource:
        def collect(self, target, default_recent_release_hours):
            raise RuntimeError("GitHub releases unavailable: HTTP 401")

        def close(self):
            return None

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "targets.json"
        config_path.write_text(
            json.dumps(
                {
                    "defaults": {"recent_release_hours": 168},
                    "exchange_profiles": {},
                    "targets": [
                        {
                            "chain_id": "cosmoshub",
                            "chain_name": "Cosmos Hub",
                            "primary_ticker": "ATOM",
                            "affected_tickers": ["ATOM"],
                            "listed_on": ["upbit"],
                            "sources": {"github_release": {"repo": "cosmos/gaia"}},
                        }
                    ],
                }
            )
        )
        monitor = SuspensionMonitor(
            config_file=str(config_path),
            state_store=StateStore(state_file=Path(tmpdir) / "state.json"),
            signal_store=SignalStore(signals_dir=Path(tmpdir) / "signals"),
            github_source=FailingGitHubSource(),
            governance_source=FakeGovernanceSource(),
            enabled_sources={"github_release"},
        )

        signals = monitor.poll_all()
        monitor.close()

        assert signals == []
        assert monitor.poll_errors == [
            {
                "chain_id": "cosmoshub",
                "source_type": "github_release",
                "error": "GitHub releases unavailable: HTTP 401",
            }
        ]
