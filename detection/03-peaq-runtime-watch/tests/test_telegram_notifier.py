from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from peaq_watch.telegram_notifier import TelegramNotifier, format_event


def _event():
    return {
        "event_reference": "peaq-incident-1",
        "stage": "warning",
        "title": "PEAQ halt warning: quorum latest head stalled",
        "network_event_time": "2026-04-08T00:00:15+00:00",
        "metadata": {
            "quorum_head_number": 100,
            "quorum_head_age_sec": 33.0,
            "quorum_finalized_age_sec": 35.0,
            "quorum_finality_gap_blocks": 5,
            "endpoint_spread": 0,
            "http_error_count": 0,
            "trigger_reasons": ["latest_quorum_stall"],
            "primary_samples": [
                {
                    "url": "https://quicknode1.peaq.xyz",
                    "latest_head_number": 100,
                    "finalized_head_number": 95,
                    "head_age_sec": 33.0,
                }
            ],
        },
    }


def test_format_event_contains_quantitative_alert_fields():
    text = format_event(_event())

    assert "PEAQ runtime warning" in text
    assert "peaq-incident-1" in text
    assert "Head age: 33.0s" in text
    assert "latest_quorum_stall" in text


def test_send_events_uses_one_message_per_event(monkeypatch):
    notifier = TelegramNotifier(bot_token="token", chat_id="chat")
    sent = []

    monkeypatch.setattr(
        notifier, "send_message", lambda text: sent.append(text) or True
    )

    assert notifier.send_events([_event()]) == 1
    assert len(sent) == 1
