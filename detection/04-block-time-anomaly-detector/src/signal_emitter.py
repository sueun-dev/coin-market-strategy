from __future__ import annotations

"""
Block time anomaly detector — signal emitter.

Emits block_halt and chain_resumed signals as JSON files, following the
same pattern as 01-governance-monitor.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

SIGNALS_DIR = Path(__file__).parent.parent / "data" / "signals"


class SignalEmitter:
    """Emit block halt / resume signals as JSON files + console output."""

    def __init__(self, signals_dir: Path | str = SIGNALS_DIR):
        self.signals_dir = Path(signals_dir)
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self._emitted: list[dict] = []

    def emit_halt(
        self,
        chain_id: str,
        ticker: str,
        tickers_affected: list[str],
        last_block_height: int,
        last_block_time: float,
        seconds_since_last_block: float,
        avg_block_time: float,
        halt_type: str = "unexpected",
        severity: str = "critical",
        confidence: str = "high",
    ) -> dict:
        """Emit a block_halt signal."""
        now = datetime.now(timezone.utc)

        signal = {
            "signal_id": uuid.uuid4().hex[:12],
            "signal_type": "block_halt",
            "chain": chain_id,
            "ticker": ticker,
            "tickers_affected": tickers_affected,
            "last_block_height": last_block_height,
            "last_block_time": datetime.fromtimestamp(
                last_block_time, tz=timezone.utc
            ).isoformat(),
            "seconds_since_last_block": round(seconds_since_last_block, 1),
            "avg_block_time": avg_block_time,
            "halt_type": halt_type,
            "severity": severity,
            "confidence": confidence,
            "detected_at": now.isoformat(),
        }

        self._write_signal(signal, now, chain_id, "halt")
        self._emitted.append(signal)
        self._print_halt_signal(signal)

        logger.info(
            "Signal emitted: block_halt %s [%s] height=%d elapsed=%.1fs",
            ticker, halt_type, last_block_height, seconds_since_last_block,
        )
        return signal

    def emit_resume(
        self,
        chain_id: str,
        ticker: str,
        resumed_height: int,
        halt_duration_seconds: float,
    ) -> dict:
        """Emit a chain_resumed signal."""
        now = datetime.now(timezone.utc)

        signal = {
            "signal_id": uuid.uuid4().hex[:12],
            "signal_type": "chain_resumed",
            "chain": chain_id,
            "ticker": ticker,
            "resumed_height": resumed_height,
            "halt_duration_seconds": round(halt_duration_seconds, 1),
            "detected_at": now.isoformat(),
        }

        self._write_signal(signal, now, chain_id, "resumed")
        self._emitted.append(signal)
        self._print_resume_signal(signal)

        logger.info(
            "Signal emitted: chain_resumed %s at height %d (halted %.0fs)",
            ticker, resumed_height, halt_duration_seconds,
        )
        return signal

    def _write_signal(self, signal: dict, now: datetime, chain_id: str, label: str):
        """Write signal to JSON file atomically."""
        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{chain_id}_{label}.json"
        filepath = self.signals_dir / filename
        tmp = filepath.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(signal, f, indent=2, ensure_ascii=False)
        os.replace(tmp, filepath)

    def _print_halt_signal(self, signal: dict):
        """Print halt signal to console."""
        print("\n" + "=" * 60)
        print(f"[SIGNAL] Block Halt Detected")
        print("=" * 60)
        print(f"  Chain:        {signal['chain']} ({signal['ticker']})")
        print(f"  Affected:     {', '.join(signal['tickers_affected'])}")
        print(f"  Last Height:  {signal['last_block_height']:,}")
        print(f"  Last Block:   {signal['last_block_time']}")
        print(f"  Elapsed:      {signal['seconds_since_last_block']}s")
        print(f"  Avg Block:    {signal['avg_block_time']}s")
        print(f"  Halt Type:    {signal['halt_type']}")
        print(f"  Severity:     {signal['severity']}")
        print(f"  Confidence:   {signal['confidence']}")
        print(f"  Detected At:  {signal['detected_at']}")
        print("=" * 60)

    def _print_resume_signal(self, signal: dict):
        """Print resume signal to console."""
        print("\n" + "=" * 60)
        print(f"[SIGNAL] Chain Resumed")
        print("=" * 60)
        print(f"  Chain:        {signal['chain']} ({signal['ticker']})")
        print(f"  Height:       {signal['resumed_height']:,}")
        print(f"  Halt Duration:{signal['halt_duration_seconds']}s")
        print(f"  Detected At:  {signal['detected_at']}")
        print("=" * 60)

    def get_emitted(self) -> list[dict]:
        return self._emitted.copy()
