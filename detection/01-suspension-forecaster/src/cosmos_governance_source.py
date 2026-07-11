"""Cosmos governance source for suspension forecasting."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0
PROPOSAL_STATUS_VOTING = "PROPOSAL_STATUS_VOTING_PERIOD"
PROPOSAL_STATUS_PASSED = "PROPOSAL_STATUS_PASSED"
V1BETA1_STATUS_MAP = {
    PROPOSAL_STATUS_VOTING: "2",
    PROPOSAL_STATUS_PASSED: "3",
}
UPGRADE_MSG_TYPES = {
    "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade",
    "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal",
}


def _parse_cosmos_time(raw: str) -> datetime:
    raw = raw.rstrip("Z")
    if "." in raw:
        base, frac = raw.split(".")
        raw = f"{base}.{frac[:6]}"
    return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)


class CosmosGovernanceSource:
    def __init__(self):
        self._client = httpx.Client(timeout=REQUEST_TIMEOUT)

    def close(self):
        self._client.close()

    def collect(self, target: dict[str, Any]) -> list[dict[str, Any]]:
        gov_cfg = target.get("sources", {}).get("governance")
        if not gov_cfg or gov_cfg.get("kind") != "cosmos":
            return []

        endpoints = gov_cfg.get("rpc_endpoints", [])
        gov_version = gov_cfg.get("gov_api_version", "v1")
        avg_block_time = float(gov_cfg.get("avg_block_time_seconds", 6.0))
        proposals = self._fetch_proposals(
            endpoints, gov_version, PROPOSAL_STATUS_VOTING
        )
        proposals.extend(
            self._fetch_proposals(
                endpoints, gov_version, PROPOSAL_STATUS_PASSED, limit=5
            )
        )
        current_height = self._get_latest_block_height(endpoints)
        dynamic_block_time = self._get_avg_block_time(endpoints, sample_count=50)
        if dynamic_block_time is not None:
            avg_block_time = dynamic_block_time

        events = []
        for proposal in proposals:
            event = self._proposal_to_event(
                target, proposal, endpoints, current_height, avg_block_time
            )
            if event:
                events.append(event)
        return events

    def _get(
        self, endpoints: list[str], path: str, params: Optional[dict[str, str]] = None
    ) -> dict[str, Any]:
        last_error: Optional[Exception] = None
        for endpoint in endpoints:
            url = f"{endpoint.rstrip('/')}{path}"
            try:
                response = self._client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                continue
        raise ConnectionError(last_error)

    def _fetch_proposals(
        self,
        endpoints: list[str],
        gov_version: str,
        status: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if gov_version == "v1":
            try:
                data = self._get(
                    endpoints,
                    "/cosmos/gov/v1/proposals",
                    params={
                        "proposal_status": status,
                        "pagination.limit": str(limit),
                        "pagination.reverse": "true",
                    },
                )
                return data.get("proposals", [])
            except ConnectionError:
                pass

        try:
            data = self._get(
                endpoints,
                "/cosmos/gov/v1beta1/proposals",
                params={
                    "proposal_status": V1BETA1_STATUS_MAP.get(status, status),
                    "pagination.limit": str(limit),
                    "pagination.reverse": "true",
                },
            )
            return [self._normalize_v1beta1(item) for item in data.get("proposals", [])]
        except ConnectionError:
            return []

    def _normalize_v1beta1(self, proposal: dict[str, Any]) -> dict[str, Any]:
        content = proposal.get("content", {})
        tally = proposal.get("final_tally_result", {})
        msg = {"@type": content.get("@type", "")}
        if "plan" in content:
            msg["plan"] = content["plan"]
        return {
            "id": proposal.get("proposal_id", ""),
            "title": content.get("title", proposal.get("title", "")),
            "summary": content.get("description", proposal.get("summary", "")),
            "status": proposal.get("status", ""),
            "messages": [msg],
            "final_tally_result": {
                "yes_count": tally.get("yes", tally.get("yes_count", "0")),
                "no_count": tally.get("no", tally.get("no_count", "0")),
                "abstain_count": tally.get("abstain", tally.get("abstain_count", "0")),
                "no_with_veto_count": tally.get(
                    "no_with_veto", tally.get("no_with_veto_count", "0")
                ),
            },
            "submit_time": proposal.get("submit_time", ""),
            "voting_end_time": proposal.get("voting_end_time", ""),
            "expedited": proposal.get("expedited", False),
        }

    def _get_latest_block_height(self, endpoints: list[str]) -> Optional[int]:
        try:
            data = self._get(endpoints, "/cosmos/base/tendermint/v1beta1/blocks/latest")
            return int(data["block"]["header"]["height"])
        except Exception:
            return None

    def _get_avg_block_time(
        self, endpoints: list[str], sample_count: int
    ) -> Optional[float]:
        try:
            latest = self._get(
                endpoints, "/cosmos/base/tendermint/v1beta1/blocks/latest"
            )
            latest_height = int(latest["block"]["header"]["height"])
            latest_time = latest["block"]["header"]["time"]
            older = self._get(
                endpoints,
                f"/cosmos/base/tendermint/v1beta1/blocks/{latest_height - sample_count}",
            )
            older_time = older["block"]["header"]["time"]
            delta = (
                _parse_cosmos_time(latest_time) - _parse_cosmos_time(older_time)
            ).total_seconds()
            return delta / sample_count
        except Exception:
            return None

    def _proposal_to_event(
        self,
        target: dict[str, Any],
        proposal: dict[str, Any],
        endpoints: list[str],
        current_height: Optional[int],
        avg_block_time: float,
    ) -> Optional[dict[str, Any]]:
        plan = self._extract_upgrade_plan(proposal)
        if not plan:
            return None

        target_height = plan.get("height")
        if target_height is None:
            return None

        network_event_time = None
        remaining_blocks = None
        if current_height is not None:
            remaining_blocks = max(0, target_height - current_height)
            if target_height <= current_height:
                return None
            if remaining_blocks > 0:
                network_event_time = (
                    datetime.now(timezone.utc)
                    + timedelta(seconds=remaining_blocks * avg_block_time)
                ).isoformat()

        status = proposal.get("status", "")
        stage = (
            "governance_voting"
            if status == PROPOSAL_STATUS_VOTING
            else "governance_passed"
        )
        confidence = "high" if stage == "governance_passed" else "medium"
        proposal_id = str(proposal.get("id", ""))

        return {
            "event_key": f"{target['chain_id']}:gov:{proposal_id}",
            "event_reference": proposal_id,
            "source_type": "governance",
            "stage": stage,
            "cause_type": "network_upgrade",
            "title": proposal.get("title", ""),
            "summary": proposal.get("summary", ""),
            "confidence_hint": confidence,
            "network_event_time": network_event_time,
            "network_event_height": target_height,
            "evidence_links": [
                f"{endpoints[0].rstrip('/')}/cosmos/gov/v1/proposals/{proposal_id}"
            ]
            if endpoints
            else [],
            "metadata": {
                "proposal_id": proposal_id,
                "status": status,
                "proposal_status": status,
                "vote_yes_pct": self._calculate_yes_percentage(proposal),
                "voting_end_time": proposal.get("voting_end_time"),
                "remaining_blocks": remaining_blocks,
                "upgrade_name": plan.get("name", ""),
            },
        }

    def _extract_upgrade_plan(
        self, proposal: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        for message in proposal.get("messages", []):
            if message.get("@type") in UPGRADE_MSG_TYPES:
                plan = message.get("plan", {})
                if plan and plan.get("height") is not None:
                    try:
                        height = int(plan.get("height"))
                    except (TypeError, ValueError):
                        return None
                    return {
                        "name": plan.get("name", ""),
                        "height": height,
                    }
        return None

    def _calculate_yes_percentage(self, proposal: dict[str, Any]) -> float:
        tally = proposal.get("final_tally_result", {})
        try:
            yes = int(tally.get("yes_count", "0"))
            no = int(tally.get("no_count", "0"))
            abstain = int(tally.get("abstain_count", "0"))
            veto = int(tally.get("no_with_veto_count", "0"))
        except (TypeError, ValueError):
            return 0.0
        total = yes + no + abstain + veto
        if total == 0:
            return 0.0
        return round((yes / total) * 100, 2)
