"""Turn upstream events into exchange suspension forecasts."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


class SuspensionForecaster:
    def __init__(self, exchange_profiles: dict[str, Any]):
        self.exchange_profiles = exchange_profiles

    def build_signal(
        self, target: dict[str, Any], event: dict[str, Any]
    ) -> dict[str, Any]:
        listed_on = list(target.get("listed_on", []))
        forecast_actions = self._build_actions(listed_on, event)
        confidence = self._resolve_confidence(event, forecast_actions)
        metadata = event.get("metadata", {})

        return {
            "signal_id": uuid.uuid4().hex[:12],
            "signal_type": "suspension_forecast",
            "event_reference": event.get("event_reference"),
            "chain_id": target["chain_id"],
            "chain_name": target["chain_name"],
            "ticker": target["primary_ticker"],
            "affected_tickers": target.get(
                "affected_tickers", [target["primary_ticker"]]
            ),
            "listed_on": listed_on,
            "source_type": event["source_type"],
            "source_stage": event["stage"],
            "cause_type": event["cause_type"],
            "event_key": event["event_key"],
            "event_title": event["title"],
            "event_summary": event.get("summary", ""),
            "network_event_time": event.get("network_event_time"),
            "network_event_height": event.get("network_event_height"),
            "confidence": confidence,
            "forecast_actions": forecast_actions,
            "evidence_links": event.get("evidence_links", []),
            "metadata": metadata,
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

    def _build_actions(
        self, listed_on: list[str], event: dict[str, Any]
    ) -> list[dict[str, Any]]:
        actions = []
        event_time = self._parse_time(event.get("network_event_time"))
        for exchange in listed_on:
            profile = self.exchange_profiles.get(exchange, {}).get(
                event["cause_type"], {}
            )
            if not profile:
                continue
            min_lead = int(profile.get("min_lead_hours", 1))
            default_lead = int(profile.get("default_lead_hours", 24))
            max_lead = int(profile.get("max_lead_hours", 168))
            action = {
                "exchange": exchange,
                "action": "deposit_withdrawal_suspend",
                "likelihood": self._likelihood_for_exchange(event),
                "rationale": event["cause_type"],
                "expected_pause_start": None,
                "expected_pause_window_start": None,
                "expected_pause_window_end": None,
            }
            if event_time is not None:
                action["expected_pause_start"] = (
                    event_time - timedelta(hours=default_lead)
                ).isoformat()
                action["expected_pause_window_start"] = (
                    event_time - timedelta(hours=max_lead)
                ).isoformat()
                action["expected_pause_window_end"] = (
                    event_time - timedelta(hours=min_lead)
                ).isoformat()
            actions.append(action)
        return actions

    def _resolve_confidence(
        self, event: dict[str, Any], actions: list[dict[str, Any]]
    ) -> str:
        hint = event.get("confidence_hint", "medium")
        if not actions and hint == "high":
            return "medium"
        return hint

    def _likelihood_for_exchange(self, event: dict[str, Any]) -> str:
        stage = event.get("stage")
        if stage == "governance_passed":
            return "high"
        if stage == "governance_voting":
            return "high" if event.get("network_event_time") else "medium"
        if stage == "early":
            return "medium"
        return "low"

    def _parse_time(self, raw: Optional[str]) -> Optional[datetime]:
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except ValueError:
            return None
