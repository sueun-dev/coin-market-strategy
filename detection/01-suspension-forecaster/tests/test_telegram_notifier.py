"""Telegram formatting tests."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.telegram_notifier import TelegramNotifier, format_signal


def test_notifier_explicit_config():
    notifier = TelegramNotifier(bot_token="token", chat_id="123")
    assert notifier.is_configured() is True


def test_format_signal_includes_forecast_fields():
    text = format_signal(
        {
            "chain_name": "Injective",
            "ticker": "INJ",
            "cause_type": "network_upgrade",
            "source_type": "governance",
            "source_stage": "governance_voting",
            "affected_tickers": ["INJ"],
            "listed_on": ["upbit", "bithumb"],
            "event_title": "Real-Time USDC Mainnet Upgrade",
            "network_event_time": "2026-04-07T15:00:00+00:00",
            "forecast_actions": [
                {
                    "exchange": "upbit",
                    "likelihood": "high",
                    "expected_pause_start": "2026-04-06T15:00:00+00:00",
                }
            ],
            "evidence_links": [
                "https://injective-rest.publicnode.com/cosmos/gov/v1/proposals/628"
            ],
            "confidence": "high",
        }
    )
    assert "[입출금 정지 선행 예측]" in text
    assert "Injective (INJ)" in text
    assert "업비트" in text
    assert "https://injective-rest.publicnode.com/cosmos/gov/v1/proposals/628" in text
