"""telegram_notifier 유닛 테스트."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.telegram_notifier import (
    GovernanceTelegramNotifier,
    format_governance_signal,
)


def test_explicit_notifier_configuration():
    notifier = GovernanceTelegramNotifier(
        bot_token="token",
        chat_id="12345",
    )

    assert notifier.is_configured() is True
    assert notifier.bot_token == "token"
    assert notifier.chat_id == "12345"


def test_format_governance_signal_includes_scope():
    text = format_governance_signal({
        "chain": "injective",
        "ticker": "INJ",
        "affected_tickers": ["INJ"],
        "exchanges_affected": ["upbit", "bithumb"],
        "proposal_id": "628",
        "proposal_title": "Real-Time USDC Mainnet Upgrade",
        "proposal_status": "PROPOSAL_STATUS_VOTING_PERIOD",
        "upgrade_name": "v1.18.3",
        "upgrade_height": 161472000,
        "remaining_blocks": 523064,
        "lead_time_hours": 89.4,
        "vote_yes_pct": 0.0,
        "confidence": "medium",
        "detected_at": "2026-04-03T19:27:13.279941+00:00",
    })

    assert "[01 GOVERNANCE]" in text
    assert "Affected: <b>INJ</b>" in text
    assert "Exchanges: upbit, bithumb" in text
    assert "Proposal: #628" in text


def test_send_signals_counts_successes():
    notifier = GovernanceTelegramNotifier(
        bot_token="token",
        chat_id="12345",
    )

    sent_texts = []

    def fake_send_message(text: str) -> bool:
        sent_texts.append(text)
        return True

    notifier.send_message = fake_send_message  # type: ignore[method-assign]

    count = notifier.send_signals([
        {
            "chain": "injective",
            "ticker": "INJ",
            "affected_tickers": ["INJ"],
            "exchanges_affected": ["upbit", "bithumb"],
            "proposal_id": "628",
            "proposal_title": "Real-Time USDC Mainnet Upgrade",
            "proposal_status": "PROPOSAL_STATUS_VOTING_PERIOD",
            "upgrade_name": "v1.18.3",
            "confidence": "medium",
            "detected_at": "2026-04-03T19:27:13.279941+00:00",
        }
    ])

    assert count == 1
    assert len(sent_texts) == 1
    assert "INJ" in sent_texts[0]


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n결과: {passed} 통과, {failed} 실패")
