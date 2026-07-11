"""Suspension forecaster tests."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.forecaster import SuspensionForecaster


def test_forecaster_builds_exchange_actions():
    forecaster = SuspensionForecaster(
        {
            "upbit": {
                "network_upgrade": {
                    "min_lead_hours": 1,
                    "default_lead_hours": 24,
                    "max_lead_hours": 168,
                }
            },
            "bithumb": {
                "network_upgrade": {
                    "min_lead_hours": 2,
                    "default_lead_hours": 24,
                    "max_lead_hours": 168,
                }
            },
        }
    )
    target = {
        "chain_id": "injective",
        "chain_name": "Injective",
        "primary_ticker": "INJ",
        "affected_tickers": ["INJ"],
        "listed_on": ["upbit", "bithumb"],
    }
    event = {
        "event_key": "injective:gov:628",
        "event_reference": "628",
        "source_type": "governance",
        "stage": "governance_voting",
        "cause_type": "network_upgrade",
        "title": "Real-Time USDC Mainnet Upgrade",
        "summary": "Upgrade proposal",
        "confidence_hint": "high",
        "network_event_time": "2026-04-07T15:00:00+00:00",
        "network_event_height": 161472000,
        "evidence_links": [
            "https://injective-rest.publicnode.com/cosmos/gov/v1/proposals/628"
        ],
        "metadata": {},
    }
    signal = forecaster.build_signal(target, event)
    assert signal["signal_type"] == "suspension_forecast"
    assert len(signal["forecast_actions"]) == 2
    assert signal["forecast_actions"][0]["exchange"] == "upbit"
    assert signal["forecast_actions"][0]["expected_pause_start"] is not None


def test_forecaster_handles_unverified_listing():
    forecaster = SuspensionForecaster({})
    target = {
        "chain_id": "solana",
        "chain_name": "Solana",
        "primary_ticker": "SOL",
        "affected_tickers": ["SOL"],
        "listed_on": [],
    }
    event = {
        "event_key": "solana:repo:v4.0.0",
        "event_reference": "v4.0.0",
        "source_type": "github_release",
        "stage": "early",
        "cause_type": "network_upgrade",
        "title": "Release v4.0.0",
        "summary": "",
        "confidence_hint": "medium",
        "network_event_time": None,
        "network_event_height": None,
        "evidence_links": ["https://github.com/anza-xyz/agave/releases/tag/v4.0.0"],
        "metadata": {},
    }
    signal = forecaster.build_signal(target, event)
    assert signal["forecast_actions"] == []
