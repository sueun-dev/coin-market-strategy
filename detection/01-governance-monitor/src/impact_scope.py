"""Helpers for describing which exchange assets are impacted by a chain event."""

from __future__ import annotations


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def get_affected_tickers(chain_config: dict) -> list[str]:
    """Return all listed tickers expected to pause when this chain has an issue."""
    configured = chain_config.get("affected_tickers") or chain_config.get("tickers_affected")
    if configured:
        return _dedupe_keep_order([str(t).upper() for t in configured])

    ticker = chain_config.get("ticker")
    return [str(ticker).upper()] if ticker else []


def get_exchanges_affected(chain_config: dict) -> list[str]:
    """Return domestic exchanges expected to be affected for the configured chain."""
    listed = chain_config.get("listed", {})
    exchanges = [name for name, is_listed in listed.items() if is_listed]
    return _dedupe_keep_order(exchanges)


def build_impact_scope(chain_config: dict) -> dict:
    """Build the reusable impact scope payload for a chain-level event."""
    return {
        "affected_tickers": get_affected_tickers(chain_config),
        "exchanges_affected": get_exchanges_affected(chain_config),
    }
