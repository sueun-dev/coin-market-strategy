from __future__ import annotations

"""
메인 폴링 루프. 모든 체인을 순회하며 업그레이드 프로포절을 감지한다.
"""

import json
import logging
import time
from pathlib import Path

from .cosmos_client import CosmosClient
from .impact_scope import build_impact_scope
from .proposal_filter import filter_upgrade_proposals
from .upgrade_time_estimator import estimate_upgrade_time
from .signal_emitter import SignalEmitter
from .state_store import StateStore

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent / "config" / "chains.json"
DEFAULT_POLL_INTERVAL = 600  # 10분


class GovernancePoller:
    """거버넌스 프로포절 폴러. 모든 체인 순회하며 업그레이드 감지."""

    def __init__(
        self,
        config_file: Path | str = CONFIG_FILE,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ):
        self.poll_interval = poll_interval
        self.config = self._load_config(config_file)
        self.clients: dict[str, CosmosClient] = {}
        self.state_store = StateStore()
        self.signal_emitter = SignalEmitter()

        # 체인별 클라이언트 생성
        for chain in self.config["chains"]:
            cid = chain["chain_id"]
            self.clients[cid] = CosmosClient(chain)
            logger.info("클라이언트 생성: %s (%s)", cid, chain["ticker"])

    def _load_config(self, config_file: Path | str) -> dict:
        with open(config_file, "r") as f:
            return json.load(f)

    def _get_chain_config(self, chain_id: str) -> dict | None:
        for c in self.config["chains"]:
            if c["chain_id"] == chain_id:
                return c
        return None

    def poll_chain(self, chain_id: str) -> list[dict]:
        """단일 체인 폴링. 감지된 시그널 목록 반환."""
        client = self.clients.get(chain_id)
        if not client:
            logger.error("체인 %s 클라이언트 없음", chain_id)
            return []

        chain_config = self._get_chain_config(chain_id)
        if not chain_config:
            logger.error("체인 %s 설정 없음", chain_id)
            return []
        impact_scope = build_impact_scope(chain_config)
        signals = []

        # 투표 중 + 통과된 프로포절 모두 조회
        all_proposals = []
        voting = client.fetch_voting_proposals()
        passed = client.fetch_passed_proposals(limit=5)
        all_proposals.extend(voting)
        all_proposals.extend(passed)

        if not all_proposals:
            logger.debug("[%s] 프로포절 없음", chain_id)
            return []

        # 업그레이드 프로포절만 필터링
        upgrades = filter_upgrade_proposals(all_proposals)
        if not upgrades:
            logger.debug("[%s] 업그레이드 프로포절 없음", chain_id)
            return []

        logger.info("[%s] 업그레이드 프로포절 %d건 감지", chain_id, len(upgrades))

        for upgrade in upgrades:
            proposal_id = upgrade["proposal_id"]
            status = upgrade["status"]

            # 중복 체크
            if not self.state_store.is_new_signal(chain_id, proposal_id, status):
                logger.debug(
                    "[%s] #%s 이미 감지됨 (상태: %s)", chain_id, proposal_id, status
                )
                continue

            # 현재 블록 높이 조회
            current_height = client.get_latest_block_height()
            if current_height is None:
                logger.error("[%s] 블록 높이 조회 실패, 건너뜀", chain_id)
                continue

            # 블록타임 동적 계산 시도, 실패 시 config 기본값 사용
            avg_block_time = client.get_avg_block_time(sample_count=100)
            if avg_block_time is None:
                avg_block_time = chain_config["avg_block_time_seconds"]
                logger.warning(
                    "[%s] 블록타임 동적 계산 실패, 기본값 사용: %.1fs",
                    chain_id, avg_block_time,
                )

            # 업그레이드 시간 예측
            target_height = upgrade["plan"]["height"]
            estimate = estimate_upgrade_time(
                current_height, target_height, avg_block_time
            )

            # 이미 지난 업그레이드는 건너뜀
            if estimate["already_passed"]:
                logger.debug(
                    "[%s] #%s 이미 완료된 업그레이드 (블록 %d < 현재 %d)",
                    chain_id, proposal_id, target_height, current_height,
                )
                self.state_store.mark_detected(
                    chain_id, proposal_id, status, {"already_passed": True}
                )
                continue

            # 신뢰도 판단
            yes_pct = upgrade.get("yes_pct", 0)
            if status == "PROPOSAL_STATUS_PASSED":
                confidence = "high"
            elif yes_pct >= 70:
                confidence = "high"
            elif yes_pct >= 50:
                confidence = "medium"
            elif yes_pct > 0:
                confidence = "low"
            else:
                # 투표 시작 직후 (아직 투표 없음)
                confidence = "medium"

            # 시그널 발행
            signal = self.signal_emitter.emit(
                chain_id=chain_id,
                ticker=client.ticker,
                proposal=upgrade,
                upgrade_estimate=estimate,
                affected_tickers=impact_scope["affected_tickers"],
                exchanges_affected=impact_scope["exchanges_affected"],
                confidence=confidence,
            )
            signals.append(signal)

            # 상태 기록
            self.state_store.mark_detected(
                chain_id, proposal_id, status, signal
            )

        return signals

    def poll_all(self) -> list[dict]:
        """모든 체인 한 번 폴링."""
        all_signals = []
        for chain_id in self.clients:
            try:
                signals = self.poll_chain(chain_id)
                all_signals.extend(signals)
            except Exception as e:
                logger.error("[%s] 폴링 중 오류: %s", chain_id, e, exc_info=True)
        return all_signals

    def run(self):
        """메인 폴링 루프 (무한 반복)."""
        logger.info(
            "거버넌스 모니터 시작 — %d개 체인, %d초 간격",
            len(self.clients), self.poll_interval,
        )
        try:
            while True:
                logger.info("━" * 40 + " 폴링 시작 " + "━" * 40)
                signals = self.poll_all()
                if signals:
                    logger.info("이번 폴링 결과: %d건 신규 시그널", len(signals))
                else:
                    logger.info("이번 폴링 결과: 신규 시그널 없음")
                logger.info("다음 폴링까지 %d초 대기...", self.poll_interval)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("사용자 중단. 종료.")
        finally:
            self.close()

    def close(self):
        for client in self.clients.values():
            client.close()
