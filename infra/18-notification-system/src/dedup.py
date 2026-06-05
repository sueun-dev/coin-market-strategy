"""Duplicate alert prevention.

Rules from STRATEGY.md:
  - Same ticker + same signal_type: no re-send within 1 hour
  - P0 is an exception (always send)
  - Premium alerts: only send on 10% unit changes
"""

import math
import time
from typing import Any, Optional


class DedupFilter:
    """In-memory deduplication filter for notification events."""

    def __init__(
        self,
        window_seconds: int = 3600,
        premium_step_pct: float = 10.0,
    ):
        """Initialize the dedup filter.

        Args:
            window_seconds: Dedup window in seconds (default 3600 = 1 hour).
            premium_step_pct: Minimum premium change (%) to trigger a new alert.
        """
        self.window_seconds = window_seconds
        self.premium_step_pct = premium_step_pct
        # {dedup_key: timestamp} for general events
        self._seen: dict[str, float] = {}
        # {ticker: last_alerted_premium_value} for premium step tracking
        self._premium_levels: dict[str, float] = {}

    def should_send(self, signal: dict[str, Any]) -> bool:
        """Determine whether this signal should be sent or suppressed.

        Args:
            signal: Event dict with keys: priority, type, data (with ticker).

        Returns:
            True if the message should be sent, False to suppress.
        """
        priority = signal.get("priority", "P3")
        event_type = signal.get("type", "")
        data = signal.get("data", {})
        ticker = data.get("ticker", data.get("coin", ""))

        # P0 always sends
        if priority == "P0":
            return True

        # Premium alerts: use step-based dedup
        if event_type == "premium_update":
            return self._check_premium_step(ticker, data)

        # General dedup: same ticker + event_type within window
        return self._check_time_window(ticker, event_type)

    def _check_time_window(self, ticker: str, event_type: str) -> bool:
        """Check if this ticker+event_type was sent within the dedup window."""
        if not ticker or not event_type:
            # If we can't identify it, let it through
            return True

        key = f"{ticker}:{event_type}"
        now = time.time()

        last_sent = self._seen.get(key)
        if last_sent is not None and (now - last_sent) < self.window_seconds:
            return False

        self._seen[key] = now
        return True

    def _check_premium_step(self, ticker: str, data: dict[str, Any]) -> bool:
        """Check if the premium has changed by at least premium_step_pct since last alert."""
        if not ticker:
            return True

        # Get the current highest premium value
        current_premium = self._extract_max_premium(data)
        if current_premium is None:
            return True

        last_level = self._premium_levels.get(ticker)
        if last_level is None:
            # First premium alert for this ticker
            self._premium_levels[ticker] = current_premium
            return True

        # Check if premium crossed a step boundary.
        # We track in steps of premium_step_pct (e.g., 10%). Use floor (not int(),
        # which truncates toward zero) so that buckets are monotonic across zero:
        # otherwise +5% and -5% both fall in bucket 0 and a premium reversal
        # (e.g. +5% -> -5%) would be silently suppressed.
        last_step = math.floor(last_level / self.premium_step_pct)
        current_step = math.floor(current_premium / self.premium_step_pct)

        if current_step != last_step:
            self._premium_levels[ticker] = current_premium
            return True

        return False

    def _extract_max_premium(self, data: dict[str, Any]) -> Optional[float]:
        """Extract the maximum premium value from the data dict."""
        premiums = data.get("premiums", {})
        if not premiums:
            # Try a direct 'premium' field
            val = data.get("premium")
            if val is not None:
                return float(str(val).replace("%", "").replace("+", ""))
            return None

        max_val = None
        for _, val in premiums.items():
            try:
                numeric = float(str(val).replace("%", "").replace("+", ""))
                if max_val is None or numeric > max_val:
                    max_val = numeric
            except (ValueError, TypeError):
                continue
        return max_val

    def clear(self) -> None:
        """Clear all dedup state."""
        self._seen.clear()
        self._premium_levels.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries from the seen cache.

        Returns:
            Number of entries removed.
        """
        now = time.time()
        expired_keys = [
            k for k, ts in self._seen.items()
            if (now - ts) >= self.window_seconds
        ]
        for k in expired_keys:
            del self._seen[k]
        return len(expired_keys)
