"""Standalone Telegram sender for the governance monitor."""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from pathlib import Path

logger = logging.getLogger(__name__)

MODULE_DIR = Path(__file__).parent.parent
REPO_ROOT = MODULE_DIR.parent.parent
ENV_FILES = [
    REPO_ROOT / ".env",
    MODULE_DIR / ".env",
]
ENV_KEY_PAIRS = [
    ("GOVERNANCE_TELEGRAM_BOT_TOKEN", "GOVERNANCE_TELEGRAM_CHAT_ID"),
    ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
]
EXCHANGE_NAME_MAP = {
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


def _load_env_settings() -> dict[str, str]:
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


def _format_exchange_names(exchanges: list[str]) -> str:
    labels = [EXCHANGE_NAME_MAP.get(exchange, exchange) for exchange in exchanges]
    return ", ".join(labels)


def format_governance_signal(signal: dict) -> str:
    """Format a governance signal for Telegram."""
    lead = signal.get("lead_time_hours", 0)
    lead_days = lead / 24 if lead else 0
    affected_tickers = signal.get("affected_tickers", [])
    exchanges_affected = signal.get("exchanges_affected", [])
    affected_label = ", ".join(affected_tickers)
    exchange_label = _format_exchange_names(exchanges_affected)

    status_map = {
        "PROPOSAL_STATUS_VOTING_PERIOD": "투표 중",
        "PROPOSAL_STATUS_PASSED": "통과",
    }
    status = status_map.get(signal.get("proposal_status", ""), signal.get("proposal_status", ""))

    lines = [
        "🟠 <b>[예상 입출금 정지]</b>",
        "",
        f"<b>{exchange_label}</b> 에서 <b>{affected_label}</b> 입출금 정지 가능성이 높습니다."
        if exchange_label and affected_label else "",
        f"체인: <b>{signal.get('chain', '')} ({signal.get('ticker', '')})</b>",
        f"영향 코인: <b>{affected_label}</b>" if affected_label else "",
        f"예상 거래소: {exchange_label}" if exchange_label else "",
        f"근거 프로포절: #{signal.get('proposal_id', '')} — {signal.get('proposal_title', '')}",
        f"현재 상태: {status}",
        f"업그레이드: {signal.get('upgrade_name', '')}",
        f"예상 타겟 블록: {signal.get('upgrade_height', 'N/A'):,}" if signal.get("upgrade_height") else "예상 타겟 블록: N/A",
        f"남은 블록: {signal.get('remaining_blocks', 0):,}" if signal.get("remaining_blocks") else "",
        f"예상 리드타임: <b>{lead:.1f}시간 ({lead_days:.1f}일)</b>" if lead else "",
        f"찬성률: {signal.get('vote_yes_pct', 0)}%",
        f"신뢰도: {signal.get('confidence', '')}",
        f"감지 시각: {str(signal.get('detected_at', ''))[:19]}",
        "",
        "이 알림은 거래소 공지 전 사전 예측입니다.",
    ]
    return "\n".join(line for line in lines if line or line == "")


class GovernanceTelegramNotifier:
    """Send governance monitor alerts to a dedicated Telegram chat."""

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
    ):
        settings = _load_env_settings()
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
            logger.warning(
                "Governance Telegram not configured (need bot token and chat id)."
            )
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }).encode("utf-8")
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
                logger.info("Governance Telegram sent")
            else:
                logger.error("Governance Telegram send failed: %s", body)
            return ok
        except Exception as exc:
            logger.error("Governance Telegram send failed: %s", exc)
            return False

    def send_signals(self, signals: list[dict]) -> int:
        sent = 0
        for signal in signals:
            if self.send_message(format_governance_signal(signal)):
                sent += 1
        return sent

    def send_test_message(self) -> bool:
        return self.send_message(
            "🧪 <b>[01 거버넌스] 텔레그램 테스트</b>\n\n"
            "이 메시지가 보이면 01 전용 텔레그램 알림이 정상 동작 중입니다."
        )
