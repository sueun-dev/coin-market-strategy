"""Main Notifier: ties together formatting, dedup, and Telegram sending.

Usage:
    from infra.notification_system.src.notifier import Notifier

    notifier = Notifier()
    notifier.send(signal_dict)
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from .formatter import format_message
from .dedup import DedupFilter
from .telegram_bot import TelegramBot

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "settings.json"


class Notifier:
    """Main entry point for the notification system.

    Accepts a signal dict, formats it, checks dedup, and sends via Telegram.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        bot: Optional[TelegramBot] = None,
        dedup: Optional[DedupFilter] = None,
    ):
        """Initialize the notifier.

        Args:
            config_path: Path to settings.json. Defaults to config/settings.json.
            bot: Optional pre-configured TelegramBot instance.
            dedup: Optional pre-configured DedupFilter instance.
        """
        config = self._load_config(config_path or str(DEFAULT_CONFIG_PATH))

        telegram_config = config.get("telegram", {})
        settings = config.get("settings", {})

        # Resolve bot token from env if specified as "env:VAR_NAME"
        bot_token = telegram_config.get("bot_token", "")
        if bot_token.startswith("env:"):
            env_var = bot_token.split(":", 1)[1]
            bot_token = os.environ.get(env_var, "")

        channels = telegram_config.get("channels", {})

        self.bot = bot or TelegramBot(bot_token=bot_token, channels=channels)
        self.dedup = dedup or DedupFilter(
            window_seconds=settings.get("dedup_window_min", 60) * 60,
            premium_step_pct=settings.get("premium_alert_step_pct", 10.0),
        )

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from a JSON file."""
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Config file not found at %s, using defaults.", config_path)
            return {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON in config file %s", config_path)
            return {}

    def send(self, signal: dict[str, Any]) -> list[dict]:
        """Process and send a notification for the given signal.

        Pipeline: validate -> dedup check -> format -> send

        Args:
            signal: Event dict with keys: source, priority, type, data.

        Returns:
            List of Telegram API responses, or empty list if suppressed/failed.
        """
        # Validate minimum fields
        if not signal.get("type"):
            logger.warning("Signal missing 'type' field, skipping: %s", signal)
            return []

        priority = signal.get("priority", "P3")
        event_type = signal.get("type", "")

        # Dedup check
        if not self.dedup.should_send(signal):
            logger.info(
                "Signal suppressed by dedup filter: ticker=%s type=%s",
                signal.get("data", {}).get("ticker", "?"),
                event_type,
            )
            return []

        # Format message
        text = format_message(signal)

        # Send via Telegram
        results = self.bot.send_message(
            text=text,
            priority=priority,
            event_type=event_type,
        )

        logger.info(
            "Sent %d message(s) for %s/%s",
            len(results),
            priority,
            event_type,
        )
        return results
