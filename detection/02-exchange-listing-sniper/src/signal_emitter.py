from __future__ import annotations

"""Emit and persist listing signals."""

import json
from datetime import datetime, timezone
from pathlib import Path

SIGNAL_DIR = Path(__file__).parent.parent / "data" / "signals"


class SignalEmitter:
    """Persist listing signals as JSON files."""

    def __init__(self, signal_dir: Path | str = SIGNAL_DIR):
        self.signal_dir = Path(signal_dir)
        self.signal_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _to_iso8601(value) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def build(
        self,
        *,
        post: dict,
        listing: dict,
        bybit: dict,
        trade: dict | None = None,
        latency: dict | None = None,
    ) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        post_url = post.get("post_url")
        if not post_url:
            post_url = (
                f"https://t.me/{post.get('channel_handle', '')}/{post.get('message_id', '')}"
            )
        text = post.get("text") or post.get("title", "")
        signal = {
            "exchange": listing["exchange"],
            "exchange_name": listing["display_name"],
            "signal_type": listing["signal_type"],
            "ticker": listing["ticker"],
            "asset_name": listing["asset_name"],
            "markets": listing["markets"],
            "channel_handle": post["channel_handle"],
            "message_id": post["message_id"],
            "title": post.get("title", text),
            "text": text,
            "post_url": post_url,
            "published_at": self._to_iso8601(post["published_at"]),
            "bybit_symbol": bybit["symbol"],
            "bybit_spot": bybit["spot"],
            "bybit_perp": bybit["perp"],
            "bybit_any": bybit["any"],
            "trade": trade or {},
            "detected_at": now,
        }
        if "cache_ready" in bybit:
            signal["bybit_cache_ready"] = bybit["cache_ready"]
        if "cache_age_ms" in bybit:
            signal["bybit_cache_age_ms"] = bybit["cache_age_ms"]
        if latency:
            signal["latency"] = latency
        return signal

    def persist(self, signal: dict) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = (
            f"{timestamp}_{signal['exchange']}_{signal['ticker']}_{signal['message_id']}.json"
        )
        out_path = self.signal_dir / filename
        with open(out_path, "w") as handle:
            json.dump(signal, handle, indent=2, ensure_ascii=False)
        return out_path

    def emit(
        self,
        *,
        post: dict,
        listing: dict,
        bybit: dict,
        trade: dict | None = None,
    ) -> dict:
        signal = self.build(
            post=post,
            listing=listing,
            bybit=bybit,
            trade=trade,
            latency=None,
        )
        self.persist(signal)
        return signal
