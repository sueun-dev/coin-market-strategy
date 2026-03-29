"""
시그널 발행기. 감지된 업그레이드 프로포절을 구조화된 시그널로 변환하여 출력한다.
파일 저장 + stdout 출력. 이후 18번(알림 시스템) 연동 시 Telegram 발송 추가 예정.
"""

import json
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

SIGNALS_DIR = Path(__file__).parent.parent / "data" / "signals"


class SignalEmitter:
    """시그널을 JSON 파일로 저장하고 콘솔에 출력."""

    def __init__(self, signals_dir: Path | str = SIGNALS_DIR):
        self.signals_dir = Path(signals_dir)
        self.signals_dir.mkdir(parents=True, exist_ok=True)
        self._emitted: list[dict] = []

    def emit(
        self,
        chain_id: str,
        ticker: str,
        proposal: dict,
        upgrade_estimate: dict,
        confidence: str = "high",
    ) -> dict:
        """시그널 발행.

        Args:
            chain_id: 체인 ID (예: "cosmoshub")
            ticker: 코인 티커 (예: "ATOM")
            proposal: proposal_filter에서 추출한 프로포절 정보
            upgrade_estimate: upgrade_time_estimator의 결과
            confidence: 신뢰도 ("high", "medium", "low")

        Returns:
            발행된 시그널 dict
        """
        now = datetime.now(timezone.utc)
        plan = proposal.get("plan", {})

        signal = {
            "signal_id": uuid.uuid4().hex[:12],
            "signal_type": "governance_upgrade",
            "chain": chain_id,
            "ticker": ticker,
            "proposal_id": proposal["proposal_id"],
            "proposal_title": proposal["title"],
            "proposal_status": proposal["status"],
            "upgrade_name": plan.get("name", ""),
            "upgrade_height": plan.get("height"),
            "estimated_time": upgrade_estimate.get("estimated_time"),
            "lead_time_hours": upgrade_estimate.get("lead_time_hours"),
            "remaining_blocks": upgrade_estimate.get("remaining_blocks"),
            "already_passed": upgrade_estimate.get("already_passed", False),
            "vote_yes_pct": proposal.get("yes_pct", 0),
            "voting_end_time": proposal.get("voting_end_time"),
            "expedited": proposal.get("expedited", False),
            "confidence": confidence,
            "detected_at": now.isoformat(),
        }

        # 파일 저장 (원자적 쓰기)
        filename = f"{now.strftime('%Y%m%d_%H%M%S')}_{chain_id}_{proposal['proposal_id']}.json"
        filepath = self.signals_dir / filename
        tmp = filepath.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(signal, f, indent=2, ensure_ascii=False)
        import os
        os.replace(tmp, filepath)

        self._emitted.append(signal)

        # 콘솔 출력
        self._print_signal(signal)

        logger.info(
            "시그널 발행: %s #%s [%s] → %s",
            ticker,
            proposal["proposal_id"],
            proposal["status"],
            filepath.name,
        )

        return signal

    def _print_signal(self, signal: dict):
        """시그널을 읽기 좋게 콘솔 출력."""
        status_emoji = {
            "PROPOSAL_STATUS_VOTING_PERIOD": "🗳️  투표 중",
            "PROPOSAL_STATUS_PASSED": "✅ 통과",
        }
        status = status_emoji.get(signal["proposal_status"], signal["proposal_status"])

        already = " (이미 완료)" if signal["already_passed"] else ""

        print("\n" + "=" * 60)
        print(f"🔔 [SIGNAL] 거버넌스 업그레이드 감지")
        print("=" * 60)
        print(f"  체인:        {signal['chain']} ({signal['ticker']})")
        print(f"  프로포절:    #{signal['proposal_id']} - {signal['proposal_title']}")
        print(f"  상태:        {status}")
        print(f"  업그레이드:  {signal['upgrade_name']}")
        height = signal.get('upgrade_height')
        remaining = signal.get('remaining_blocks')
        lead = signal.get('lead_time_hours')
        print(f"  타겟 블록:   {height:,}" if height is not None else "  타겟 블록:   N/A")
        print(f"  남은 블록:   {remaining:,}{already}" if remaining is not None else f"  남은 블록:   N/A{already}")
        print(f"  예상 시간:   {signal.get('estimated_time', 'N/A')}")
        print(f"  리드타임:    {lead}시간 ({lead/24:.1f}일)" if lead is not None else "  리드타임:    N/A")
        print(f"  찬성률:      {signal['vote_yes_pct']}%")
        print(f"  신뢰도:      {signal['confidence']}")
        print(f"  감지 시각:   {signal['detected_at']}")
        print("=" * 60)

    def get_emitted(self) -> list[dict]:
        return self._emitted.copy()
