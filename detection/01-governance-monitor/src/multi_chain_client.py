from __future__ import annotations

"""
비-Cosmos 체인 거버넌스 클라이언트.
Polkadot, Tezos, Aptos, Sui, Algorand, Cardano, ICON, Celo 지원.
각 체인의 API 규격에 맞춰 업그레이드 프로포절/상태를 조회한다.
"""

import httpx
import logging
import re
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15.0


class MultiChainGovernanceClient:
    """비-Cosmos 체인 거버넌스 통합 클라이언트."""

    def __init__(self, chain_config: dict):
        self.chain_id = chain_config["chain_id"]
        self.ticker = chain_config["ticker"]
        self.chain_type = chain_config["chain_type"]
        self.endpoints = chain_config.get("rpc_endpoints", [])
        self.gov_config = chain_config.get("governance", {})
        self._client = httpx.Client(timeout=REQUEST_TIMEOUT)

    def close(self):
        self._client.close()

    def _get(self, url: str, params: dict | None = None, headers: dict | None = None) -> dict:
        try:
            resp = self._client.get(url, params=params, headers=headers or {})
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("[%s] GET 실패 %s: %s", self.chain_id, url, e)
            raise ConnectionError(f"[{self.chain_id}] {url}: {e}")

    def _post(self, url: str, json_data: dict, headers: dict | None = None) -> dict:
        try:
            resp = self._client.post(url, json=json_data, headers=headers or {})
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            logger.warning("[%s] POST 실패 %s: %s", self.chain_id, url, e)
            raise ConnectionError(f"[{self.chain_id}] {url}: {e}")

    def fetch_upgrade_proposals(self) -> list[dict]:
        """체인 타입에 따라 적절한 메서드 호출."""
        method = getattr(self, f"_fetch_{self.chain_type}", None)
        if not method:
            logger.error("[%s] 지원하지 않는 체인 타입: %s", self.chain_id, self.chain_type)
            return []
        try:
            return method()
        except (ConnectionError, Exception) as e:
            logger.error("[%s] 조회 실패: %s", self.chain_id, e)
            return []

    # ═══════════════════════════════════════════════════════════
    # Polkadot (OpenGov)
    # ═══════════════════════════════════════════════════════════
    def _fetch_polkadot(self) -> list[dict]:
        """Polkassembly API로 runtime upgrade 레퍼렌덤 조회."""
        api_url = self.gov_config.get("api_url", "https://api.polkassembly.io")
        network = self.gov_config.get("network", "polkadot")

        results = []

        # 최근 레퍼렌덤 조회 (활성 + 최근 완료)
        for status_filter in ["active", "all"]:
            try:
                params = {
                    "proposalType": "referendums_v2",
                    "listingLimit": "15",
                    "sortBy": "newest",
                }
                headers = {"x-network": network}
                data = self._get(
                    f"{api_url}/api/v1/listing/on-chain-posts",
                    params=params, headers=headers,
                )
                posts = data.get("posts", [])

                for p in posts:
                    title = (p.get("title") or "").lower()
                    status = p.get("status", "")

                    # 업그레이드 관련 키워드 필터
                    is_upgrade = any(kw in title for kw in [
                        "upgrade", "runtime", "release", "fellowship",
                        "enact", "system version", "set_code",
                    ])

                    # Whitelisted Caller track = 런타임 업그레이드 빈도 높음
                    track = str(p.get("track_number", ""))
                    if track in ["1", "10", "11", "12", "13", "14", "15"]:
                        is_upgrade = True

                    if is_upgrade or "Executed" in status:
                        results.append({
                            "proposal_id": str(p.get("post_id", "")),
                            "title": p.get("title", ""),
                            "status": status,
                            "plan": {
                                "name": p.get("title", ""),
                                "height": None,  # Polkadot은 블록높이가 아닌 시간 기반
                            },
                            "yes_pct": 0.0,
                            "submit_time": p.get("created_at", ""),
                            "voting_end_time": "",
                            "chain_type": "polkadot",
                        })

                if results:
                    break  # 첫 번째 성공 쿼리로 충분
            except ConnectionError:
                continue

        return results

    # ═══════════════════════════════════════════════════════════
    # Tezos (Self-Amendment)
    # ═══════════════════════════════════════════════════════════
    def _fetch_tezos(self) -> list[dict]:
        """TzKT API로 투표 기간 + 프로포절 조회."""
        api_url = self.gov_config.get("api_url", "https://api.tzkt.io")

        results = []

        # 현재 + 최근 투표 기간 조회
        periods = self._get(f"{api_url}/v1/voting/periods", params={
            "sort.desc": "id", "limit": "5"
        })

        for period in periods:
            kind = period.get("kind", "")
            # proposal, exploration, promotion, adoption 단계가 업그레이드 관련
            if kind in ["proposal", "exploration", "promotion", "adoption", "testing"]:
                epoch_start = period.get("firstLevel", 0)
                epoch_end = period.get("lastLevel", 0)

                # 해당 기간의 프로포절 조회
                try:
                    proposals = self._get(
                        f"{api_url}/v1/voting/periods/{period['index']}/proposals"
                    )
                except ConnectionError:
                    proposals = []

                for prop in (proposals if isinstance(proposals, list) else []):
                    results.append({
                        "proposal_id": f"{period['index']}_{prop.get('hash', '')[:8]}",
                        "title": f"Tezos Protocol {prop.get('hash', '')[:8]} ({kind})",
                        "status": f"TEZOS_{kind.upper()}",
                        "plan": {
                            "name": prop.get("hash", "")[:12],
                            "height": epoch_end,
                        },
                        "yes_pct": prop.get("rolls", 0) / max(period.get("totalRolls", 1), 1) * 100 if period.get("totalRolls") else 0,
                        "submit_time": period.get("startTime", ""),
                        "voting_end_time": period.get("endTime", ""),
                        "chain_type": "tezos",
                    })

            if not results and kind == "proposal":
                # 프로포절 단계이지만 아직 제출된 것이 없을 수 있음
                results.append({
                    "proposal_id": str(period["index"]),
                    "title": f"Tezos Voting Period #{period['index']} ({kind})",
                    "status": f"TEZOS_{kind.upper()}",
                    "plan": {"name": f"period_{period['index']}", "height": period.get("lastLevel")},
                    "yes_pct": 0.0,
                    "submit_time": period.get("startTime", ""),
                    "voting_end_time": period.get("endTime", ""),
                    "chain_type": "tezos",
                })

        return results

    # ═══════════════════════════════════════════════════════════
    # Aptos (AIP Governance)
    # ═══════════════════════════════════════════════════════════
    def _fetch_aptos(self) -> list[dict]:
        """Aptos REST API로 거버넌스 프로포절 + 현재 버전 조회."""
        rpc = self.endpoints[0] if self.endpoints else "https://fullnode.mainnet.aptoslabs.com/v1"

        results = []

        # 현재 체인 상태
        try:
            status = self._get(rpc)
            current_version = status.get("git_hash", "")
            block_height = status.get("block_height", "0")

            results.append({
                "proposal_id": f"aptos_state_{block_height}",
                "title": f"Aptos Current State (block {block_height})",
                "status": "CHAIN_STATE",
                "plan": {
                    "name": f"git:{current_version[:8]}",
                    "height": int(block_height),
                },
                "yes_pct": 100.0,
                "submit_time": datetime.now(timezone.utc).isoformat(),
                "voting_end_time": "",
                "chain_type": "aptos",
            })
        except ConnectionError:
            pass

        # 거버넌스 프로포절 조회 (온체인 리소스)
        try:
            gov_addr = "0x1"
            resource = self._get(
                f"{rpc}/accounts/{gov_addr}/resource/0x1::aptos_governance::GovernanceConfig"
            )
            if resource:
                data = resource.get("data", {})
                results.append({
                    "proposal_id": "aptos_gov_config",
                    "title": f"Aptos Governance Config (min_voting_threshold: {data.get('min_voting_threshold', '?')})",
                    "status": "GOV_CONFIG",
                    "plan": {"name": "governance_config", "height": None},
                    "yes_pct": 0.0,
                    "submit_time": "",
                    "voting_end_time": "",
                    "chain_type": "aptos",
                })
        except ConnectionError:
            pass

        return results

    # ═══════════════════════════════════════════════════════════
    # Sui (Protocol Version)
    # ═══════════════════════════════════════════════════════════
    def _fetch_sui(self) -> list[dict]:
        """Sui RPC로 프로토콜 버전 변경 감지."""
        rpc = self.endpoints[0] if self.endpoints else "https://fullnode.mainnet.sui.io:443"

        results = []

        try:
            data = self._post(rpc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "suix_getLatestSuiSystemState", "params": [],
            })
            r = data.get("result", {})
            protocol_version = r.get("protocolVersion")
            epoch = r.get("epoch")

            if protocol_version:
                results.append({
                    "proposal_id": f"sui_pv_{protocol_version}",
                    "title": f"Sui Protocol Version {protocol_version} (Epoch {epoch})",
                    "status": "ACTIVE_PROTOCOL",
                    "plan": {
                        "name": f"v{protocol_version}",
                        "height": int(epoch) if epoch else None,
                    },
                    "yes_pct": 100.0,
                    "submit_time": datetime.now(timezone.utc).isoformat(),
                    "voting_end_time": "",
                    "chain_type": "sui",
                })
        except ConnectionError:
            pass

        return results

    # ═══════════════════════════════════════════════════════════
    # Algorand (Consensus Upgrade)
    # ═══════════════════════════════════════════════════════════
    def _fetch_algorand(self) -> list[dict]:
        """Algorand API로 프로토콜 업그레이드 투표 상태 조회."""
        rpc = self.endpoints[0] if self.endpoints else "https://mainnet-api.algonode.cloud"

        results = []

        try:
            status = self._get(f"{rpc}/v2/status")
            next_version = status.get("next-version", "")
            next_round = status.get("next-version-round", 0)
            last_round = status.get("last-round", 0)
            supported = status.get("next-version-supported", False)

            # next-version이 현재와 다르면 업그레이드 진행 중
            current_version_parts = next_version.split("/")
            version_short = current_version_parts[-1][:12] if current_version_parts else next_version[:12]

            results.append({
                "proposal_id": f"algo_{version_short}",
                "title": f"Algorand Protocol {version_short}",
                "status": "UPGRADE_PENDING" if next_round > last_round else "CURRENT",
                "plan": {
                    "name": version_short,
                    "height": next_round,
                },
                "yes_pct": 100.0 if supported else 0.0,
                "submit_time": datetime.now(timezone.utc).isoformat(),
                "voting_end_time": "",
                "chain_type": "algorand",
                "extra": {
                    "next_version_full": next_version,
                    "last_round": last_round,
                    "next_version_round": next_round,
                    "supported": supported,
                },
            })
        except ConnectionError:
            pass

        return results

    # ═══════════════════════════════════════════════════════════
    # Cardano (CIP Governance)
    # ═══════════════════════════════════════════════════════════
    def _fetch_cardano(self) -> list[dict]:
        """Koios API (무료, 키 불필요)로 프로토콜 파라미터 + 에포크 정보 조회."""
        api_url = self.gov_config.get("api_url", "https://api.koios.rest/api/v1")

        results = []

        try:
            # 현재 에포크 + 프로토콜 파라미터
            tip = self._get(f"{api_url}/tip")
            if isinstance(tip, list) and tip:
                t = tip[0]
                epoch = t.get("epoch_no", 0)
                block = t.get("block_no", 0)

                results.append({
                    "proposal_id": f"ada_epoch_{epoch}",
                    "title": f"Cardano Epoch {epoch} (Block {block})",
                    "status": "CURRENT_EPOCH",
                    "plan": {
                        "name": f"epoch_{epoch}",
                        "height": block,
                    },
                    "yes_pct": 0.0,
                    "submit_time": datetime.now(timezone.utc).isoformat(),
                    "voting_end_time": "",
                    "chain_type": "cardano",
                })

            # 거버넌스 프로포절 조회 (Chang 이후)
            try:
                proposals = self._get(f"{api_url}/proposal_list")
                if isinstance(proposals, list):
                    for p in proposals[:5]:
                        desc = p.get("proposal_description", {})
                        desc_str = desc.get("tag", "") if isinstance(desc, dict) else str(desc)[:100]
                        results.append({
                            "proposal_id": str(p.get("proposal_id", ""))[:40],
                            "title": f"Cardano {p.get('proposal_type', '')} - {desc_str}",
                            "status": p.get("proposal_status", "ACTIVE"),
                            "plan": {"name": p.get("proposal_type", ""), "height": None},
                            "yes_pct": 0.0,
                            "submit_time": str(p.get("block_time", "")),
                            "voting_end_time": str(p.get("expiration", "")),
                            "chain_type": "cardano",
                        })
            except ConnectionError:
                pass  # 거버넌스 엔드포인트 미지원 가능

        except ConnectionError:
            pass

        return results

    # ═══════════════════════════════════════════════════════════
    # ICON (Network Proposal)
    # ═══════════════════════════════════════════════════════════
    def _fetch_icon(self) -> list[dict]:
        """ICON RPC로 네트워크 프로포절 조회."""
        rpc = self.endpoints[0] if self.endpoints else "https://ctz.solidwallet.io/api/v3"

        results = []

        try:
            # 네트워크 프로포절 목록
            data = self._post(rpc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "icx_call",
                "params": {
                    "to": "cx0000000000000000000000000000000000000001",
                    "dataType": "call",
                    "data": {"method": "getProposals"},
                },
            })
            result = data.get("result", {})

            if isinstance(result, dict):
                proposals = result.get("proposals", [])
                for p in proposals[:10]:
                    p_id = p.get("id", "")
                    status_val = p.get("status", "")

                    results.append({
                        "proposal_id": str(p_id),
                        "title": f"ICON Network Proposal {p_id}",
                        "status": f"ICON_{status_val}",
                        "plan": {"name": str(p_id), "height": None},
                        "yes_pct": 0.0,
                        "submit_time": "",
                        "voting_end_time": "",
                        "chain_type": "icon",
                    })
        except ConnectionError:
            pass

        # 현재 블록 높이
        try:
            block_data = self._post(rpc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "icx_getLastBlock", "params": [],
            })
            block = block_data.get("result", {})
            height = block.get("height", 0)
            if isinstance(height, str):
                height = int(height, 16)

            results.append({
                "proposal_id": f"icx_state_{height}",
                "title": f"ICON Block {height:,}",
                "status": "CHAIN_STATE",
                "plan": {"name": "current", "height": height},
                "yes_pct": 0.0,
                "submit_time": datetime.now(timezone.utc).isoformat(),
                "voting_end_time": "",
                "chain_type": "icon",
            })
        except ConnectionError:
            pass

        return results

    # ═══════════════════════════════════════════════════════════
    # Celo (CGP — On-chain Governance)
    # ═══════════════════════════════════════════════════════════
    def _fetch_celo(self) -> list[dict]:
        """Celo RPC로 거버넌스 컨트랙트 상태 조회."""
        rpc = self.endpoints[0] if self.endpoints else "https://forno.celo.org"

        results = []

        try:
            # 현재 블록
            block_data = self._post(rpc, {
                "jsonrpc": "2.0", "id": 1,
                "method": "eth_blockNumber", "params": [],
            })
            height_hex = block_data.get("result", "0x0")
            height = int(height_hex, 16)

            results.append({
                "proposal_id": f"celo_state_{height}",
                "title": f"Celo Block {height:,}",
                "status": "CHAIN_STATE",
                "plan": {"name": "current", "height": height},
                "yes_pct": 0.0,
                "submit_time": datetime.now(timezone.utc).isoformat(),
                "voting_end_time": "",
                "chain_type": "celo",
            })
        except ConnectionError:
            pass

        return results
