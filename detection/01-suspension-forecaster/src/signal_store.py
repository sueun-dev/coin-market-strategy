"""Persist and print suspension forecast signals."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_SIGNALS_DIR = Path(__file__).parent.parent / "data" / "signals"


class SignalStore:
    def __init__(self, signals_dir: Path | str = DEFAULT_SIGNALS_DIR):
        self.signals_dir = Path(signals_dir)
        self.signals_dir.mkdir(parents=True, exist_ok=True)

    def save(self, signal: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        signal = dict(signal)
        signal.setdefault("signal_id", uuid.uuid4().hex[:12])
        signal.setdefault("detected_at", now.isoformat())
        item_id = signal.get("event_reference") or signal["signal_id"]
        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{signal.get('chain_id', 'unknown')}_{item_id}.json"
        filename = filename.replace("/", "_")
        filepath = self.signals_dir / filename
        tmp = filepath.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(signal, f, indent=2, ensure_ascii=False)
        os.replace(tmp, filepath)
        logger.info(
            "Forecast signal saved: %s [%s] -> %s",
            signal.get("chain_id"),
            signal.get("source_stage"),
            filepath.name,
        )
        self._print(signal)
        return signal

    def _print(self, signal: dict[str, Any]):
        print("\n" + "=" * 60)
        print("🔔 [SIGNAL] 입출금 정지 선행 예측")
        print("=" * 60)
        print(f"  체인:        {signal.get('chain_name')} ({signal.get('ticker')})")
        print(f"  원인 유형:   {signal.get('cause_type')}")
        print(
            f"  소스 단계:   {signal.get('source_type')} / {signal.get('source_stage')}"
        )
        print(f"  이벤트:      {signal.get('event_title')}")
        if signal.get("network_event_time"):
            print(f"  네트워크 시점:{signal.get('network_event_time')}")
        if signal.get("network_event_height") is not None:
            print(f"  타겟 블록:   {signal.get('network_event_height')}")
        print(f"  영향 코인:   {', '.join(signal.get('affected_tickers', []))}")
        actions = signal.get("forecast_actions", [])
        if actions:
            for action in actions:
                print(
                    f"  {action['exchange']}: {action['likelihood']} / "
                    f"{action.get('expected_pause_start', 'time_unknown')}"
                )
        else:
            print("  거래소 예측: 검증된 상장 정보 없음")
        print(f"  신뢰도:      {signal.get('confidence')}")
        print("=" * 60)
