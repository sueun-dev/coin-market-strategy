"""Main polling coordinator for the suspension forecaster."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, Optional

from .config_loader import load_monitor_config, match_target
from .cosmos_governance_source import CosmosGovernanceSource
from .forecaster import SuspensionForecaster
from .github_release_source import GitHubReleaseSource
from .signal_store import SignalStore
from .state_store import StateStore

logger = logging.getLogger(__name__)


class SuspensionMonitor:
    def __init__(
        self,
        config_file: Optional[str] = None,
        poll_interval: int = 600,
        enabled_sources: Optional[set[str]] = None,
        state_store: Optional[StateStore] = None,
        signal_store: Optional[SignalStore] = None,
        github_source: Optional[GitHubReleaseSource] = None,
        governance_source: Optional[CosmosGovernanceSource] = None,
    ):
        config = (
            load_monitor_config(config_file) if config_file else load_monitor_config()
        )
        self.poll_interval = poll_interval
        self.enabled_sources = enabled_sources or {"github_release", "governance"}
        self.exchange_profiles = config.get("exchange_profiles", {})
        self.default_recent_release_hours = int(
            config.get("defaults", {}).get("recent_release_hours", 168)
        )
        self.targets = config.get("targets", [])
        self.state_store = state_store or StateStore()
        self.signal_store = signal_store or SignalStore()
        self.github_source = github_source or GitHubReleaseSource()
        self.governance_source = governance_source or CosmosGovernanceSource()
        self.forecaster = SuspensionForecaster(self.exchange_profiles)
        self.poll_errors: list[dict[str, str]] = []

    def close(self):
        self.github_source.close()
        self.governance_source.close()

    def clear_state(self):
        self.state_store.clear()

    def poll_target(self, query: str) -> list[dict[str, Any]]:
        self.poll_errors = []
        signals: list[dict[str, Any]] = []
        for target in self.targets:
            if match_target(target, query):
                signals.extend(self._poll_single_target(target))
        return signals

    def poll_all(self) -> list[dict[str, Any]]:
        self.poll_errors = []
        signals: list[dict[str, Any]] = []
        for target in self.targets:
            try:
                signals.extend(self._poll_single_target(target))
            except Exception as exc:
                self._record_poll_error(target, "poll", exc)
                logger.error(
                    "[%s] polling failed: %s",
                    target.get("chain_id"),
                    exc,
                    exc_info=True,
                )
        return signals

    def _record_poll_error(
        self, target: dict[str, Any], source_type: str, exc: Exception
    ):
        self.poll_errors.append(
            {
                "chain_id": str(target.get("chain_id", "unknown")),
                "source_type": source_type,
                "error": str(exc),
            }
        )

    def _poll_single_target(self, target: dict[str, Any]) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if "github_release" in self.enabled_sources:
            try:
                events.extend(
                    self.github_source.collect(
                        target, self.default_recent_release_hours
                    )
                )
            except Exception as exc:
                self._record_poll_error(target, "github_release", exc)
                logger.error(
                    "[%s] github_release source failed: %s",
                    target.get("chain_id"),
                    exc,
                    exc_info=True,
                )
        if "governance" in self.enabled_sources:
            try:
                events.extend(self.governance_source.collect(target))
            except Exception as exc:
                self._record_poll_error(target, "governance", exc)
                logger.error(
                    "[%s] governance source failed: %s",
                    target.get("chain_id"),
                    exc,
                    exc_info=True,
                )

        signals: list[dict[str, Any]] = []
        for event in events:
            if not self.state_store.is_new_event(
                event["source_type"], event["event_key"], event["stage"]
            ):
                continue
            signal = self.forecaster.build_signal(target, event)
            if not signal.get("forecast_actions"):
                logger.info(
                    "[%s] skipping alert without exchange forecast: %s / %s",
                    target.get("chain_id"),
                    event["source_type"],
                    event["event_reference"],
                )
                self.state_store.mark_seen(
                    event["source_type"],
                    event["event_key"],
                    event["stage"],
                    {"skipped": "no_exchange_forecast"},
                )
                continue
            saved = self.signal_store.save(signal)
            self.state_store.mark_seen(
                event["source_type"], event["event_key"], event["stage"], saved
            )
            signals.append(saved)
        return signals

    def run(self, on_signals: Optional[Callable[[list[dict[str, Any]]], None]] = None):
        logger.info(
            "Suspension monitor started - sources=%s targets=%d interval=%ds",
            ",".join(sorted(self.enabled_sources)),
            len(self.targets),
            self.poll_interval,
        )
        try:
            while True:
                logger.info("━" * 40 + " suspension poll start " + "━" * 40)
                signals = self.poll_all()
                if signals:
                    logger.info(
                        "Poll complete: %d new suspension forecasts", len(signals)
                    )
                    if on_signals is not None:
                        on_signals(signals)
                elif self.poll_errors:
                    logger.error(
                        "Poll complete with %d source errors", len(self.poll_errors)
                    )
                else:
                    logger.info("Poll complete: no new forecasts")
                logger.info("Sleeping %ds until next poll...", self.poll_interval)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("Stopped by user")
        finally:
            self.close()
