"""Telegram notifier for quantitative PEAQ runtime events."""

from __future__ import annotations

import html
import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent.parent
REPO_ROOT = MODULE_DIR.parent.parent
ENV_FILES = [REPO_ROOT / ".env", MODULE_DIR / ".env"]
ENV_KEY_PAIRS = [
    ("PEAQ_TELEGRAM_BOT_TOKEN", "PEAQ_TELEGRAM_CHAT_ID"),
    ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
]


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _load_env() -> dict[str, str]:
    settings: dict[str, str] = {}
    for env_file in ENV_FILES:
        settings.update(_parse_env_file(env_file))
    for token_key, chat_key in ENV_KEY_PAIRS:
        for key in (token_key, chat_key):
            value = os.getenv(key)
            if value:
                settings[key] = value
    return settings


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    return html.escape(str(value))


def format_event(event: dict[str, Any]) -> str:
    metadata = event.get("metadata", {})
    samples = metadata.get("primary_samples", [])
    sample_lines = []
    for sample in samples[:3]:
        sample_lines.append(
            "- "
            + _fmt(sample.get("url"))
            + " latest="
            + _fmt(sample.get("latest_head_number"))
            + " finalized="
            + _fmt(sample.get("finalized_head_number"))
            + " head_age="
            + _fmt(sample.get("head_age_sec"))
            + "s"
        )

    lines = [
        f"<b>[PEAQ runtime {html.escape(str(event.get('stage', 'alert')))}]</b>",
        "",
        f"Incident: <b>{_fmt(event.get('event_reference'))}</b>",
        f"Title: {_fmt(event.get('title'))}",
        f"Time: {_fmt(event.get('network_event_time'))}",
        f"Head: {_fmt(metadata.get('quorum_head_number'))}",
        f"Head age: {_fmt(metadata.get('quorum_head_age_sec'))}s",
        f"Finalized age: {_fmt(metadata.get('quorum_finalized_age_sec'))}s",
        f"Finality gap: {_fmt(metadata.get('quorum_finality_gap_blocks'))} blocks",
        f"Endpoint spread: {_fmt(metadata.get('endpoint_spread'))}",
        f"HTTP errors: {_fmt(metadata.get('http_error_count'))}",
        f"Triggers: {_fmt(', '.join(metadata.get('trigger_reasons', [])))}",
    ]
    if sample_lines:
        lines.extend(["", "Samples:", *sample_lines])
    return "\n".join(lines)


class TelegramNotifier:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        settings = _load_env()
        selected_token = bot_token or ""
        selected_chat_id = chat_id or ""
        if not selected_token or not selected_chat_id:
            for token_key, chat_key in ENV_KEY_PAIRS:
                token = selected_token or settings.get(token_key, "")
                resolved_chat_id = selected_chat_id or settings.get(chat_key, "")
                if token and resolved_chat_id:
                    selected_token = token
                    selected_chat_id = resolved_chat_id
                    break
        self.bot_token = selected_token
        self.chat_id = selected_chat_id

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str) -> bool:
        if not self.is_configured():
            logger.warning("PEAQ Telegram not configured")
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                body = json.load(response)
            ok = bool(body.get("ok"))
            if ok:
                logger.info("PEAQ Telegram sent")
            else:
                logger.error("PEAQ Telegram failed: %s", body)
            return ok
        except Exception as exc:
            logger.error("PEAQ Telegram failed: %s", exc)
            return False

    def send_events(self, events: list[dict[str, Any]]) -> int:
        sent = 0
        for event in events:
            if self.send_message(format_event(event)):
                sent += 1
        return sent

    def send_test_message(self) -> bool:
        return self.send_message(
            "<b>[PEAQ runtime watch] Telegram test</b>\n\n"
            "If this message appears, PEAQ runtime alerts can be delivered."
        )
