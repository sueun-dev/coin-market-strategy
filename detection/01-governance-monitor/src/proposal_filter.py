from __future__ import annotations

"""
프로포절 필터: SoftwareUpgradeProposal만 추출하고 업그레이드 정보를 파싱한다.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 업그레이드 관련 message type
UPGRADE_MSG_TYPES = {
    "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade",
    "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal",  # 구버전
}


def is_upgrade_proposal(proposal: dict) -> bool:
    """프로포절이 소프트웨어 업그레이드인지 판단."""
    # v1: messages 필드 체크
    for msg in proposal.get("messages", []):
        if msg.get("@type") in UPGRADE_MSG_TYPES:
            return True

    # v1beta1 (구버전 체인): content 필드 체크
    content = proposal.get("content", {})
    if content.get("@type") in UPGRADE_MSG_TYPES:
        return True

    return False


def extract_upgrade_plan(proposal: dict) -> dict | None:
    """프로포절에서 업그레이드 plan 정보를 추출한다.

    Returns:
        {
            "name": "v27.1.0",
            "height": 30466800,
            "info": "..."
        }
    """
    # v1: messages[].plan
    for msg in proposal.get("messages", []):
        if msg.get("@type") in UPGRADE_MSG_TYPES:
            plan = msg.get("plan", {})
            if plan:
                return {
                    "name": plan.get("name", ""),
                    "height": _safe_int(plan.get("height")),
                    "info": plan.get("info", ""),
                }

    # v1beta1: content.plan
    content = proposal.get("content", {})
    if content.get("@type") in UPGRADE_MSG_TYPES:
        plan = content.get("plan", {})
        if plan:
            return {
                "name": plan.get("name", ""),
                "height": _safe_int(plan.get("height")),
                "info": plan.get("info", ""),
            }

    return None


def calculate_yes_percentage(proposal: dict) -> float:
    """찬성률(%) 계산. 투표 진행 중이면 현재까지 비율."""
    tally = proposal.get("final_tally_result", {})
    try:
        yes = int(tally.get("yes_count", "0"))
        no = int(tally.get("no_count", "0"))
        abstain = int(tally.get("abstain_count", "0"))
        veto = int(tally.get("no_with_veto_count", "0"))
    except (ValueError, TypeError) as e:
        logger.warning("찬성률 계산 실패 (비정상 tally 값): %s", e)
        return 0.0

    total = yes + no + abstain + veto
    if total == 0:
        return 0.0
    return round((yes / total) * 100, 2)


def filter_upgrade_proposals(proposals: list[dict]) -> list[dict]:
    """프로포절 목록에서 업그레이드 프로포절만 필터링.

    Returns:
        [{
            "proposal_id": "1026",
            "title": "Gaia v27.1.0 Upgrade",
            "status": "PROPOSAL_STATUS_VOTING_PERIOD",
            "plan": {"name": "v27.1.0", "height": 30466800, "info": "..."},
            "yes_pct": 0.0,
            "submit_time": "2026-03-24T14:09:31.849071789Z",
            "voting_end_time": "2026-03-31T14:28:15.379921462Z",
            "expedited": false,
            "summary": "..."
        }]
    """
    results = []
    for p in proposals:
        if not is_upgrade_proposal(p):
            continue

        plan = extract_upgrade_plan(p)
        if not plan or plan["height"] is None:
            logger.warning(
                "프로포절 #%s: 업그레이드이지만 height 없음, 건너뜀", p.get("id")
            )
            continue

        results.append({
            "proposal_id": p.get("id", ""),
            "title": p.get("title", ""),
            "status": p.get("status", ""),
            "plan": plan,
            "yes_pct": calculate_yes_percentage(p),
            "submit_time": p.get("submit_time", ""),
            "voting_end_time": p.get("voting_end_time", ""),
            "expedited": p.get("expedited", False),
            "summary": (p.get("summary", "") or "")[:500],
        })

    return results


def _safe_int(value: Any) -> int | None:
    """문자열/정수를 안전하게 int로 변환."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
