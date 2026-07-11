"""Quantitative PEAQ halt detector."""

from __future__ import annotations

import json
import logging
import math
import time
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .state_store import StateStore

logger = logging.getLogger(__name__)

ALERT_STAGES = {"warning", "critical", "recovery"}


class RuntimeHeadSource:
    def __init__(
        self,
        state_store: Optional[StateStore] = None,
        snapshot_provider: Optional[
            Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
        ] = None,
    ):
        self.state_store = state_store or StateStore()
        self.snapshot_provider = snapshot_provider

    def close(self) -> None:
        return None

    def collect(self, target: dict[str, Any]) -> list[dict[str, Any]]:
        runtime_cfg = target.get("sources", {}).get("runtime_head")
        if not runtime_cfg:
            return []

        snapshot = (
            self.snapshot_provider(target, runtime_cfg)
            if self.snapshot_provider is not None
            else self._build_live_snapshot(runtime_cfg)
        )
        namespace = f"runtime_head:{target['chain_id']}"
        state = self.state_store.get_namespace(namespace)
        events, next_state = self._advance_state(target, runtime_cfg, snapshot, state)
        self.state_store.set_namespace(namespace, next_state)
        return events

    def _build_live_snapshot(self, cfg: dict[str, Any]) -> dict[str, Any]:
        now = time.time()
        samples = []
        timeout = float(cfg.get("http_timeout_seconds", 8.0))
        for endpoint in cfg.get("http_endpoints", []):
            sample = {
                "url": endpoint,
                "latest_head_number": None,
                "finalized_head_number": None,
                "latest_block_timestamp": None,
                "finalized_block_timestamp": None,
                "head_age_sec": None,
                "finalized_age_sec": None,
                "latest_lag_sec": None,
                "finalized_lag_sec": None,
                "finality_gap_blocks": None,
                "error": None,
            }
            try:
                latest_block, latest_ts = self._fetch_block(endpoint, "latest", timeout)
                finalized_block, finalized_ts = self._fetch_block(
                    endpoint, "finalized", timeout
                )
                sample.update(
                    {
                        "latest_head_number": latest_block,
                        "finalized_head_number": finalized_block,
                        "latest_block_timestamp": latest_ts,
                        "finalized_block_timestamp": finalized_ts,
                        "head_age_sec": round(max(0.0, now - latest_ts), 2),
                        "finalized_age_sec": round(max(0.0, now - finalized_ts), 2),
                        "latest_lag_sec": round(max(0.0, now - latest_ts), 2),
                        "finalized_lag_sec": round(max(0.0, now - finalized_ts), 2),
                        "finality_gap_blocks": max(0, latest_block - finalized_block),
                    }
                )
            except Exception as exc:
                sample["error"] = str(exc)
            samples.append(sample)

        valid_samples = [
            sample for sample in samples if sample.get("latest_head_number") is not None
        ]
        majority = math.floor(len(valid_samples) / 2) + 1 if valid_samples else 0
        head_numbers = [sample["latest_head_number"] for sample in valid_samples]
        latest_ages = [
            sample["head_age_sec"]
            for sample in valid_samples
            if sample.get("head_age_sec") is not None
        ]
        finalized_ages = [
            sample["finalized_age_sec"]
            for sample in valid_samples
            if sample.get("finalized_age_sec") is not None
        ]
        finality_gaps = [
            sample["finality_gap_blocks"]
            for sample in valid_samples
            if sample.get("finality_gap_blocks") is not None
        ]

        endpoint_spread = None
        if head_numbers:
            endpoint_spread = max(head_numbers) - min(head_numbers)

        return {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "primary_mode": "http",
            "majority_threshold": majority,
            "primary_samples": valid_samples,
            "http_samples": samples,
            "quorum_head_number": self._median(head_numbers, cast_int=True),
            "quorum_head_age_sec": self._median(latest_ages),
            "quorum_finalized_age_sec": self._median(finalized_ages),
            "quorum_finality_gap_blocks": self._median(finality_gaps, cast_int=True),
            "endpoint_spread": endpoint_spread,
            "http_error_count": sum(1 for sample in samples if sample.get("error")),
        }

    def _advance_state(
        self,
        target: dict[str, Any],
        cfg: dict[str, Any],
        snapshot: dict[str, Any],
        state: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        observe_rounds = int(cfg.get("observe_stall_rounds", 2))
        warning_rounds = int(cfg.get("warning_stall_rounds", 3))
        critical_rounds = int(cfg.get("critical_stall_rounds", 5))
        recovery_rounds = int(cfg.get("recovery_healthy_rounds", 3))
        observe_head_age = float(cfg.get("observe_head_age_seconds", 12.0))
        warning_head_age = float(cfg.get("warning_head_age_seconds", 24.0))
        critical_head_age = float(cfg.get("critical_head_age_seconds", 45.0))
        observe_finalized_age = float(cfg.get("observe_finalized_age_seconds", 18.0))
        critical_finalized_age = float(cfg.get("critical_finalized_age_seconds", 30.0))
        divergence_blocks = int(cfg.get("divergence_blocks", 2))

        previous_endpoint_state = state.get("endpoint_state", {})
        endpoint_state: dict[str, Any] = {}
        primary_samples = []
        for sample in snapshot.get("primary_samples", []):
            latest_head = sample.get("latest_head_number")
            finalized_head = sample.get("finalized_head_number")
            if latest_head is None:
                continue

            previous = previous_endpoint_state.get(sample["url"], {})
            same_latest = previous.get("latest_head_number") == latest_head
            same_finalized = previous.get("finalized_head_number") == finalized_head
            head_age = float(sample.get("head_age_sec") or 0.0)
            finalized_age = float(sample.get("finalized_age_sec") or 0.0)

            latest_stall_rounds = (
                int(previous.get("latest_stall_rounds", 0)) + 1
                if same_latest and head_age >= observe_head_age
                else 0
            )
            finalized_stall_rounds = (
                int(previous.get("finalized_stall_rounds", 0)) + 1
                if same_finalized and finalized_age >= observe_finalized_age
                else 0
            )

            enriched = dict(sample)
            enriched["latest_stall_rounds"] = latest_stall_rounds
            enriched["finalized_stall_rounds"] = finalized_stall_rounds
            primary_samples.append(enriched)
            endpoint_state[sample["url"]] = {
                "latest_head_number": latest_head,
                "finalized_head_number": finalized_head,
                "latest_stall_rounds": latest_stall_rounds,
                "finalized_stall_rounds": finalized_stall_rounds,
            }

        majority = math.floor(len(primary_samples) / 2) + 1 if primary_samples else 0
        observe_latest_count = sum(
            sample["latest_stall_rounds"] >= observe_rounds
            and float(sample.get("head_age_sec") or 0.0) >= observe_head_age
            for sample in primary_samples
        )
        warning_latest_count = sum(
            sample["latest_stall_rounds"] >= warning_rounds
            and float(sample.get("head_age_sec") or 0.0) >= warning_head_age
            for sample in primary_samples
        )
        critical_latest_count = sum(
            sample["latest_stall_rounds"] >= critical_rounds
            and float(sample.get("head_age_sec") or 0.0) >= critical_head_age
            for sample in primary_samples
        )
        critical_finalized_count = sum(
            sample["finalized_stall_rounds"] >= warning_rounds
            and float(sample.get("finalized_age_sec") or 0.0) >= critical_finalized_age
            for sample in primary_samples
        )
        spread = snapshot.get("endpoint_spread")

        next_level = "healthy"
        trigger_reasons: list[str] = []
        if (
            majority
            and critical_latest_count >= majority
            and critical_finalized_count >= majority
        ):
            next_level = "critical"
            trigger_reasons = ["latest_quorum_stall", "finalized_quorum_stall"]
        elif majority and warning_latest_count >= majority:
            next_level = "warning"
            trigger_reasons = ["latest_quorum_stall"]
        elif (majority and observe_latest_count >= majority) or (
            spread is not None and int(spread) > divergence_blocks
        ):
            next_level = "observe"
            trigger_reasons = (
                ["latest_quorum_stall"]
                if observe_latest_count >= majority
                else ["endpoint_divergence"]
            )

        incident_seq = int(state.get("incident_seq", 0))
        incident_id = state.get("incident_id")
        stage_emitted = dict(state.get("stage_emitted", {}))
        previous_level = state.get("current_level", "healthy")
        healthy_rounds = int(state.get("healthy_rounds", 0))
        has_alert_history = any(
            stage in stage_emitted for stage in ("warning", "critical")
        )
        events: list[dict[str, Any]] = []

        if next_level == "healthy":
            if incident_id and not has_alert_history:
                return events, {
                    "current_level": "healthy",
                    "incident_seq": incident_seq,
                    "incident_id": None,
                    "stage_emitted": {},
                    "healthy_rounds": 0,
                    "endpoint_state": endpoint_state,
                    "last_snapshot": self._compact_snapshot(
                        snapshot,
                        primary_samples,
                        observe_latest_count,
                        warning_latest_count,
                        critical_latest_count,
                        critical_finalized_count,
                        [],
                    ),
                }

            if incident_id and previous_level != "healthy":
                healthy_rounds += 1
            elif incident_id and healthy_rounds > 0:
                healthy_rounds += 1
            else:
                healthy_rounds = 0

            compact_snapshot = self._compact_snapshot(
                snapshot,
                primary_samples,
                observe_latest_count,
                warning_latest_count,
                critical_latest_count,
                critical_finalized_count,
                [],
            )
            if (
                incident_id
                and has_alert_history
                and healthy_rounds >= recovery_rounds
                and "recovery" not in stage_emitted
            ):
                events.append(
                    self._build_event(
                        target,
                        snapshot,
                        incident_id,
                        "recovery",
                        primary_samples,
                        observe_latest_count,
                        warning_latest_count,
                        critical_latest_count,
                        critical_finalized_count,
                        ["healthy_recovery"],
                    )
                )
                stage_emitted["recovery"] = snapshot["timestamp_utc"]

            if incident_id and healthy_rounds >= recovery_rounds:
                return events, {
                    "current_level": "healthy",
                    "incident_seq": incident_seq,
                    "incident_id": None,
                    "stage_emitted": {},
                    "healthy_rounds": 0,
                    "endpoint_state": endpoint_state,
                    "last_snapshot": compact_snapshot,
                }

            return events, {
                "current_level": "healthy",
                "incident_seq": incident_seq,
                "incident_id": incident_id,
                "stage_emitted": stage_emitted,
                "healthy_rounds": healthy_rounds,
                "endpoint_state": endpoint_state,
                "last_snapshot": compact_snapshot,
            }

        healthy_rounds = 0
        if previous_level == "healthy" or not incident_id:
            incident_seq += 1
            incident_id = f"{target['chain_id']}-incident-{incident_seq}"
            stage_emitted = {}

        if next_level in ALERT_STAGES and next_level not in stage_emitted:
            events.append(
                self._build_event(
                    target,
                    snapshot,
                    incident_id,
                    next_level,
                    primary_samples,
                    observe_latest_count,
                    warning_latest_count,
                    critical_latest_count,
                    critical_finalized_count,
                    trigger_reasons,
                )
            )
            stage_emitted[next_level] = snapshot["timestamp_utc"]

        return events, {
            "current_level": next_level,
            "incident_seq": incident_seq,
            "incident_id": incident_id,
            "stage_emitted": stage_emitted,
            "healthy_rounds": healthy_rounds,
            "endpoint_state": endpoint_state,
            "last_snapshot": self._compact_snapshot(
                snapshot,
                primary_samples,
                observe_latest_count,
                warning_latest_count,
                critical_latest_count,
                critical_finalized_count,
                trigger_reasons,
            ),
        }

    def _build_event(
        self,
        target: dict[str, Any],
        snapshot: dict[str, Any],
        incident_id: str,
        stage: str,
        primary_samples: list[dict[str, Any]],
        observe_latest_count: int,
        warning_latest_count: int,
        critical_latest_count: int,
        critical_finalized_count: int,
        trigger_reasons: list[str],
    ) -> dict[str, Any]:
        titles = {
            "warning": "PEAQ halt warning: quorum latest head stalled",
            "critical": "PEAQ halt critical: latest and finalized heads stalled",
            "recovery": "PEAQ halt recovery: quorum heads resumed",
        }
        return {
            "event_key": f"{incident_id}:{stage}",
            "event_reference": incident_id,
            "source_type": "runtime_head",
            "stage": stage,
            "cause_type": "recovery" if stage == "recovery" else "network_issue",
            "title": titles[stage],
            "summary": (
                f"head_age={snapshot.get('quorum_head_age_sec')} "
                f"finalized_age={snapshot.get('quorum_finalized_age_sec')} "
                f"spread={snapshot.get('endpoint_spread')}"
            ),
            "confidence_hint": "high",
            "network_event_time": snapshot.get("timestamp_utc"),
            "network_event_height": snapshot.get("quorum_head_number"),
            "evidence_links": [],
            "metadata": {
                "quorum_head_number": snapshot.get("quorum_head_number"),
                "quorum_head_age_sec": snapshot.get("quorum_head_age_sec"),
                "quorum_finalized_age_sec": snapshot.get("quorum_finalized_age_sec"),
                "quorum_finality_gap_blocks": snapshot.get(
                    "quorum_finality_gap_blocks"
                ),
                "endpoint_spread": snapshot.get("endpoint_spread"),
                "http_error_count": snapshot.get("http_error_count"),
                "observe_latest_count": observe_latest_count,
                "warning_latest_count": warning_latest_count,
                "critical_latest_count": critical_latest_count,
                "critical_finalized_count": critical_finalized_count,
                "trigger_reasons": trigger_reasons,
                "primary_samples": primary_samples,
                "likelihood_hint": "high" if stage != "critical" else "very_high",
            },
        }

    @staticmethod
    def _compact_snapshot(
        snapshot: dict[str, Any],
        primary_samples: list[dict[str, Any]],
        observe_latest_count: int,
        warning_latest_count: int,
        critical_latest_count: int,
        critical_finalized_count: int,
        trigger_reasons: list[str],
    ) -> dict[str, Any]:
        return {
            "timestamp_utc": snapshot.get("timestamp_utc"),
            "primary_mode": snapshot.get("primary_mode"),
            "quorum_head_number": snapshot.get("quorum_head_number"),
            "quorum_head_age_sec": snapshot.get("quorum_head_age_sec"),
            "quorum_finalized_age_sec": snapshot.get("quorum_finalized_age_sec"),
            "quorum_finality_gap_blocks": snapshot.get("quorum_finality_gap_blocks"),
            "endpoint_spread": snapshot.get("endpoint_spread"),
            "http_error_count": snapshot.get("http_error_count"),
            "observe_latest_count": observe_latest_count,
            "warning_latest_count": warning_latest_count,
            "critical_latest_count": critical_latest_count,
            "critical_finalized_count": critical_finalized_count,
            "trigger_reasons": trigger_reasons,
            "primary_samples": primary_samples,
        }

    @staticmethod
    def _median(
        values: list[float | int], cast_int: bool = False
    ) -> Optional[float | int]:
        if not values:
            return None
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2:
            result = ordered[mid]
        else:
            result = (ordered[mid - 1] + ordered[mid]) / 2
        return int(result) if cast_int else round(float(result), 2)

    @classmethod
    def _fetch_block(cls, url: str, tag: str, timeout: float) -> tuple[int, int]:
        payload = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_getBlockByNumber",
                "params": [tag, False],
            }
        ).encode()
        request = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "coin-market-strategy/peaq-runtime-watch",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode())
        if "error" in body:
            raise RuntimeError(json.dumps(body["error"], ensure_ascii=False))
        result = body.get("result")
        if not result:
            raise RuntimeError(f"missing block payload for tag={tag}")
        return int(result["number"], 16), int(result["timestamp"], 16)
