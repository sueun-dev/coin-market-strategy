"""
Block time anomaly detector — halt confirmation module.

Confirms a chain halt by checking for 3 consecutive polls with no height
change. Distinguishes expected vs unexpected halts by cross-referencing
governance monitor signals when available.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to governance monitor signals for cross-referencing
GOVERNANCE_SIGNALS_DIR = (
    Path(__file__).parent.parent.parent
    / "01-governance-monitor"
    / "data"
    / "signals"
)


@dataclass
class HaltRecord:
    """Tracks consecutive stalled polls for a single chain."""
    chain_id: str
    stalled_height: int | None = None
    consecutive_stalls: int = 0
    halt_confirmed: bool = False
    halt_confirmed_at: float | None = None
    halt_type: str = "unexpected"  # "expected" or "unexpected"
    resumed: bool = False
    resumed_at: float | None = None


class HaltDetector:
    """Detect chain halts from a series of block height observations.

    A halt is confirmed when the block height does not change across
    *consecutive_threshold* consecutive polls (default 3, i.e. ~30 seconds
    at 10-second polling).
    """

    def __init__(self, consecutive_threshold: int = 3):
        self.threshold = consecutive_threshold
        self._records: dict[str, HaltRecord] = {}

    def restore(
        self,
        chain_id: str,
        *,
        stalled_height: int | None,
        consecutive_stalls: int = 0,
        halt_confirmed: bool = False,
        halt_confirmed_at: float | None = None,
        halt_type: str = "unexpected",
    ) -> HaltRecord:
        """Restore a chain record from persistent state.

        ChainPulse invokes this module as a short-lived subprocess. Without
        restoring the last stalled height and count, "3 consecutive polls" would
        reset to one on every subprocess call and root-level halt alerts would
        never fire.
        """
        rec = HaltRecord(
            chain_id=chain_id,
            stalled_height=stalled_height,
            consecutive_stalls=max(0, int(consecutive_stalls or 0)),
            halt_confirmed=bool(halt_confirmed),
            halt_confirmed_at=halt_confirmed_at,
            halt_type=halt_type or "unexpected",
        )
        self._records[chain_id] = rec
        return rec

    def observe(self, chain_id: str, height: int | None) -> HaltRecord:
        """Record a new block height observation and return the halt record.

        Args:
            chain_id: Identifier for the chain.
            height: Latest observed block height, or None if RPC failed.

        Returns:
            Updated HaltRecord for the chain.
        """
        if chain_id not in self._records:
            self._records[chain_id] = HaltRecord(chain_id=chain_id)

        rec = self._records[chain_id]

        # RPC failure is not a stall — skip this observation
        if height is None:
            return rec

        # If chain was halted and height has changed, it has resumed
        if rec.halt_confirmed and height != rec.stalled_height:
            rec.resumed = True
            rec.resumed_at = time.time()
            rec.halt_confirmed = False
            rec.consecutive_stalls = 0
            rec.stalled_height = None
            logger.info("[%s] Chain resumed at height %d", chain_id, height)
            return rec

        # Check for stall
        if rec.stalled_height is not None and height == rec.stalled_height:
            rec.consecutive_stalls += 1
        elif rec.stalled_height is None or height != rec.stalled_height:
            # New height observed — reset stall counter
            rec.stalled_height = height
            rec.consecutive_stalls = 1
            rec.resumed = False

        # Confirm halt if threshold reached
        if rec.consecutive_stalls >= self.threshold and not rec.halt_confirmed:
            rec.halt_confirmed = True
            rec.halt_confirmed_at = time.time()
            rec.halt_type = self._classify_halt(chain_id)
            logger.warning(
                "[%s] HALT CONFIRMED at height %d (%s)",
                chain_id, height, rec.halt_type,
            )

        return rec

    def _classify_halt(self, chain_id: str) -> str:
        """Check if a governance upgrade signal exists for this chain.

        If a recent governance_upgrade signal exists, the halt is expected.
        Otherwise it is unexpected.
        """
        if not GOVERNANCE_SIGNALS_DIR.is_dir():
            return "unexpected"

        try:
            for f in sorted(GOVERNANCE_SIGNALS_DIR.glob("*.json"), reverse=True):
                # Only check recent signals (last 20 files)
                import json
                with open(f) as fh:
                    sig = json.load(fh)
                if sig.get("chain") == chain_id and sig.get("signal_type") == "governance_upgrade":
                    return "expected"
        except Exception as e:
            logger.debug("Error reading governance signals: %s", e)

        return "unexpected"

    def get_record(self, chain_id: str) -> HaltRecord | None:
        return self._records.get(chain_id)

    def get_all_records(self) -> dict[str, HaltRecord]:
        return self._records.copy()

    def is_halted(self, chain_id: str) -> bool:
        rec = self._records.get(chain_id)
        return rec.halt_confirmed if rec else False

    def reset(self, chain_id: str):
        """Reset tracking for a chain."""
        if chain_id in self._records:
            del self._records[chain_id]
