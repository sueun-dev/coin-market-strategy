"""Telegram notifier for suspension forecasts."""

from __future__ import annotations

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
    ("GOVERNANCE_TELEGRAM_BOT_TOKEN", "GOVERNANCE_TELEGRAM_CHAT_ID"),
    ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
]
EXCHANGE_LABELS = {
    "upbit": "업비트",
    "bithumb": "빗썸",
}


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
    for key in {
        "GOVERNANCE_TELEGRAM_BOT_TOKEN",
        "GOVERNANCE_TELEGRAM_CHAT_ID",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    }:
        value = os.getenv(key)
        if value:
            settings[key] = value
    return settings


def _format_exchange(name: str) -> str:
    return EXCHANGE_LABELS.get(name, name)


def format_signal(signal: dict[str, Any]) -> str:
    listed = ", ".join(_format_exchange(name) for name in signal.get("listed_on", []))
    tickers = ", ".join(signal.get("affected_tickers", []))
    lines = [
        "🟠 <b>[입출금 정지 선행 예측]</b>",
        "",
        f"체인: <b>{signal.get('chain_name')} ({signal.get('ticker')})</b>",
        f"원인: <b>{signal.get('cause_type')}</b>",
        f"소스: {signal.get('source_type')} / {signal.get('source_stage')}",
        f"영향 코인: <b>{tickers}</b>" if tickers else "",
        f"예상 거래소: {listed}" if listed else "예상 거래소: 검증된 상장 정보 없음",
        f"네트워크 이벤트: {signal.get('event_title')}",
        f"예상 체인 시점: {signal.get('network_event_time')}"
        if signal.get("network_event_time")
        else "",
        "",
    ]
    for action in signal.get("forecast_actions", []):
        exchange = _format_exchange(action["exchange"])
        lines.append(
            f"{exchange}: {action['likelihood']} 가능성"
            + (
                f" / 예상 중지 {action['expected_pause_start']}"
                if action.get("expected_pause_start")
                else ""
            )
        )

    evidence_links = signal.get("evidence_links", [])
    if evidence_links:
        lines.extend(["", f"근거: {evidence_links[0]}"])

    lines.append(f"신뢰도: {signal.get('confidence')}")
    return "\n".join(line for line in lines if line or line == "")


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
            logger.warning("Telegram not configured")
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
                logger.info("Forecast Telegram sent")
            else:
                logger.error("Forecast Telegram failed: %s", body)
            return ok
        except Exception as exc:
            logger.error("Forecast Telegram failed: %s", exc)
            return False

    def send_signals(self, signals: list[dict[str, Any]]) -> int:
        sent = 0
        for signal in signals:
            if self.send_message(format_signal(signal)):
                sent += 1
        return sent

    def send_test_message(self) -> bool:
        return self.send_message(
            "🧪 <b>[01 입출금 정지 선행 예측] 텔레그램 테스트</b>\n\n"
            "이 메시지가 보이면 새 01 알림 채널이 정상 동작 중입니다."
        )
