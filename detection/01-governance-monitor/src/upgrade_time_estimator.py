"""
업그레이드 블록높이 → 예상 시간 계산.
"""

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def estimate_upgrade_time(
    current_height: int,
    target_height: int,
    avg_block_time: float,
) -> dict:
    """업그레이드 예상 시간과 리드타임을 계산한다.

    Args:
        current_height: 현재 블록 높이
        target_height: 업그레이드 타겟 블록 높이
        avg_block_time: 평균 블록 생성 시간 (초)

    Returns:
        {
            "remaining_blocks": 40982,
            "estimated_seconds": 249990,
            "estimated_time": "2026-04-01T14:00:00+00:00",
            "lead_time_hours": 69.4,
            "already_passed": False
        }
    """
    remaining = target_height - current_height
    now = datetime.now(timezone.utc)

    if remaining <= 0:
        return {
            "remaining_blocks": 0,
            "estimated_seconds": 0,
            "estimated_time": now.isoformat(),
            "lead_time_hours": 0.0,
            "already_passed": True,
        }

    est_seconds = remaining * avg_block_time
    est_time = now + timedelta(seconds=est_seconds)
    lead_hours = round(est_seconds / 3600, 1)

    logger.info(
        "업그레이드 예상: %d 블록 남음, %.1f시간 후 (%s)",
        remaining,
        lead_hours,
        est_time.strftime("%Y-%m-%d %H:%M UTC"),
    )

    return {
        "remaining_blocks": remaining,
        "estimated_seconds": round(est_seconds),
        "estimated_time": est_time.isoformat(),
        "lead_time_hours": lead_hours,
        "already_passed": False,
    }
