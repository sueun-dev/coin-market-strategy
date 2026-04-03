from __future__ import annotations

"""
Cosmos SDK 거버넌스 API 클라이언트.
각 체인의 REST 엔드포인트에서 프로포절을 조회한다.
"""

import httpx
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _parse_cosmos_time(t: str) -> datetime:
    """Cosmos 타임스탬프 파싱. 나노초를 마이크로초로 잘라서 처리."""
    t = t.rstrip("Z")
    if "." in t:
        base, frac = t.split(".")
        frac = frac[:6]
        t = f"{base}.{frac}"
    return datetime.fromisoformat(t).replace(tzinfo=timezone.utc)

PROPOSAL_STATUS_VOTING = "PROPOSAL_STATUS_VOTING_PERIOD"
PROPOSAL_STATUS_PASSED = "PROPOSAL_STATUS_PASSED"

# v1beta1 상태 코드 (숫자): 2=VOTING, 3=PASSED
V1BETA1_STATUS_MAP = {
    PROPOSAL_STATUS_VOTING: "2",
    PROPOSAL_STATUS_PASSED: "3",
}

REQUEST_TIMEOUT = 15.0


class CosmosClient:
    """Cosmos SDK REST API 클라이언트. RPC 장애 시 백업 엔드포인트 자동 전환."""

    def __init__(self, chain_config: dict):
        self.chain_id = chain_config["chain_id"]
        self.ticker = chain_config["ticker"]
        self.rpc_endpoints: list[str] = chain_config["rpc_endpoints"]
        self.gov_version = chain_config.get("gov_api_version", "v1")
        self.avg_block_time = chain_config["avg_block_time_seconds"]
        self._client = httpx.Client(timeout=REQUEST_TIMEOUT)
        self._cached_block_time: float | None = None

    def close(self):
        self._client.close()

    # ── API 호출 (자동 failover) ──────────────────────────────

    def _get(self, path: str, params: dict | None = None) -> dict:
        """RPC 엔드포인트 순회하며 GET 요청. 첫 성공 응답 반환."""
        last_error: Exception | None = None
        for endpoint in self.rpc_endpoints:
            url = f"{endpoint.rstrip('/')}{path}"
            try:
                resp = self._client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_error = e
                logger.warning(
                    "[%s] RPC 실패 %s: %s", self.chain_id, endpoint, e
                )
                continue
        raise ConnectionError(
            f"[{self.chain_id}] 모든 RPC 엔드포인트 실패: {last_error}"
        )

    # ── 프로포절 조회 ─────────────────────────────────────────

    def fetch_proposals(self, status: str, limit: int = 20) -> list[dict]:
        """특정 상태의 프로포절 목록 조회. v1 실패 시 v1beta1 자동 폴백."""
        # v1 시도
        if self.gov_version == "v1":
            try:
                path = "/cosmos/gov/v1/proposals"
                params = {
                    "proposal_status": status,
                    "pagination.limit": str(limit),
                    "pagination.reverse": "true",
                }
                data = self._get(path, params)
                return data.get("proposals", [])
            except ConnectionError:
                logger.info("[%s] v1 실패, v1beta1 폴백 시도", self.chain_id)

        # v1beta1 폴백
        try:
            path = "/cosmos/gov/v1beta1/proposals"
            beta_status = V1BETA1_STATUS_MAP.get(status, status)
            params = {
                "proposal_status": beta_status,
                "pagination.limit": str(limit),
                "pagination.reverse": "true",
            }
            data = self._get(path, params)
            proposals = data.get("proposals", [])
            # v1beta1 응답을 v1 형태로 정규화
            return [self._normalize_v1beta1(p) for p in proposals]
        except ConnectionError as e:
            logger.error(e)
            return []

    @staticmethod
    def _normalize_v1beta1(proposal: dict) -> dict:
        """v1beta1 프로포절을 v1 형식으로 변환."""
        content = proposal.get("content", {})
        msg_type = content.get("@type", "")

        # v1beta1의 content를 v1의 messages로 변환
        messages = []
        if msg_type:
            msg = {"@type": msg_type}
            # SoftwareUpgradeProposal인 경우 plan 포함
            if "plan" in content:
                msg["plan"] = content["plan"]
            messages.append(msg)

        tally = proposal.get("final_tally_result", {})

        return {
            "id": proposal.get("proposal_id", ""),
            "title": content.get("title", proposal.get("title", "")),
            "summary": content.get("description", proposal.get("summary", "")),
            "status": proposal.get("status", ""),
            "messages": messages,
            "content": content,  # 원본도 유지
            "final_tally_result": {
                "yes_count": tally.get("yes", tally.get("yes_count", "0")),
                "no_count": tally.get("no", tally.get("no_count", "0")),
                "abstain_count": tally.get("abstain", tally.get("abstain_count", "0")),
                "no_with_veto_count": tally.get("no_with_veto", tally.get("no_with_veto_count", "0")),
            },
            "submit_time": proposal.get("submit_time", ""),
            "voting_start_time": proposal.get("voting_start_time", ""),
            "voting_end_time": proposal.get("voting_end_time", ""),
            "expedited": proposal.get("expedited", False),
        }

    def fetch_voting_proposals(self) -> list[dict]:
        return self.fetch_proposals(PROPOSAL_STATUS_VOTING)

    def fetch_passed_proposals(self, limit: int = 10) -> list[dict]:
        return self.fetch_proposals(PROPOSAL_STATUS_PASSED, limit)

    # ── 현재 블록 높이 조회 ───────────────────────────────────

    def get_latest_block_height(self) -> int | None:
        """현재 블록 높이 조회."""
        try:
            data = self._get(
                "/cosmos/base/tendermint/v1beta1/blocks/latest"
            )
            height_str = data["block"]["header"]["height"]
            return int(height_str)
        except (ConnectionError, KeyError, ValueError, TypeError) as e:
            logger.error("[%s] 블록 높이 조회 실패: %s", self.chain_id, e)
            return None

    # ── 블록타임 동적 계산 ────────────────────────────────────

    def get_avg_block_time(self, sample_count: int = 100) -> float | None:
        """캐시된 블록타임 반환. 없으면 동적 계산."""
        if self._cached_block_time is not None:
            return self._cached_block_time
        result = self.calculate_avg_block_time(sample_count)
        if result is not None:
            self._cached_block_time = result
        return result

    def calculate_avg_block_time(self, sample_count: int = 100) -> float | None:
        """최근 N개 블록 기반 평균 블록타임 계산."""
        try:
            latest = self._get(
                "/cosmos/base/tendermint/v1beta1/blocks/latest"
            )
            latest_height = int(latest["block"]["header"]["height"])
            latest_time = latest["block"]["header"]["time"]

            old_height = latest_height - sample_count
            old_data = self._get(
                f"/cosmos/base/tendermint/v1beta1/blocks/{old_height}"
            )
            old_time = old_data["block"]["header"]["time"]

            dt = (_parse_cosmos_time(latest_time) - _parse_cosmos_time(old_time)).total_seconds()
            avg = dt / sample_count
            logger.info(
                "[%s] 블록타임 계산: %.2fs (%d블록 샘플)",
                self.chain_id, avg, sample_count,
            )
            return avg

        except Exception as e:
            logger.error("[%s] 블록타임 계산 실패: %s", self.chain_id, e)
            return None
