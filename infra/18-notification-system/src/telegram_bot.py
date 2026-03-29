"""Telegram Bot API client for sending messages via httpx."""

import os
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Priority level to emoji mapping
PRIORITY_EMOJI = {
    "P0": "\U0001f534",  # red circle
    "P1": "\U0001f7e0",  # orange circle
    "P2": "\U0001f7e1",  # yellow circle
    "P3": "\U0001f7e2",  # green circle
}

# Map event types to channel keys
EVENT_TYPE_TO_CHANNEL = {
    "signal_detected": "signal",
    "position_open": "position",
    "position_close": "position",
    "exit_complete": "position",
    "premium_update": "premium",
    "risk_warning": "risk",
    "short_liquidation_risk": "risk",
    "critical": "critical",
    "hack_detected": "critical",
    "fill_failure": "critical",
    "daily_report": "signal",
}


class TelegramBot:
    """Send messages to Telegram channels via the Bot API using httpx."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(
        self,
        bot_token: Optional[str] = None,
        channels: Optional[dict[str, str]] = None,
    ):
        self.bot_token = bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN is not set. Sending will fail.")
        self.channels = channels or {}
        self._base_url = self.BASE_URL.format(token=self.bot_token)

    def _resolve_channel(self, priority: str, event_type: str) -> list[str]:
        """Determine which channel(s) to send to based on priority and event type.

        P0 sends to ALL channels plus the critical channel.
        P1 sends to the relevant channel.
        P2 sends to the relevant channel only.
        P3 sends to the signal (log) channel only.
        """
        if priority == "P0":
            # P0: all channels + critical
            targets = list(set(self.channels.values()))
            critical_id = self.channels.get("critical")
            if critical_id and critical_id not in targets:
                targets.append(critical_id)
            return targets if targets else []

        if priority == "P3":
            ch = self.channels.get("signal")
            return [ch] if ch else []

        # P1, P2: route to the relevant channel
        channel_key = EVENT_TYPE_TO_CHANNEL.get(event_type, "signal")
        ch = self.channels.get(channel_key)
        return [ch] if ch else []

    def send_message(
        self,
        text: str,
        priority: str,
        event_type: str,
        chat_id: Optional[str] = None,
    ) -> list[dict]:
        """Send a formatted message to the appropriate Telegram channel(s).

        Args:
            text: The formatted message text.
            priority: Priority level (P0, P1, P2, P3).
            event_type: The event type string for channel routing.
            chat_id: Override chat_id (sends to this one only).

        Returns:
            List of Telegram API response dicts.
        """
        if chat_id:
            targets = [chat_id]
        else:
            targets = self._resolve_channel(priority, event_type)

        if not targets:
            logger.warning(
                "No target channels resolved for priority=%s event_type=%s",
                priority,
                event_type,
            )
            return []

        results = []
        for target_id in targets:
            try:
                resp = self._send_to_chat(target_id, text)
                results.append(resp)
            except Exception:
                logger.exception("Failed to send to chat_id=%s", target_id)
        return results

    def _send_to_chat(self, chat_id: str, text: str) -> dict:
        """Low-level send to a single chat_id."""
        url = f"{self._base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    def send_test_message(self, chat_id: str) -> dict:
        """Send a test message to verify bot connectivity."""
        text = (
            "\U0001f7e2 [TEST] Notification System Online\n\n"
            "The notification system is connected and working.\n"
            "All priority levels (P0-P3) are operational."
        )
        return self._send_to_chat(chat_id, text)
