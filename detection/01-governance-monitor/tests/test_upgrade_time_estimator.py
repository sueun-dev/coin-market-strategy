"""upgrade_time_estimator 유닛 테스트."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.upgrade_time_estimator import estimate_upgrade_time


def test_normal_estimate():
    result = estimate_upgrade_time(
        current_height=30425000,
        target_height=30466800,
        avg_block_time=6.0,
    )
    assert result["remaining_blocks"] == 41800
    assert result["estimated_seconds"] == 41800 * 6
    assert result["already_passed"] is False
    assert result["lead_time_hours"] > 0
    # ~69.7시간 = ~2.9일
    assert 69.0 < result["lead_time_hours"] < 70.0


def test_already_passed():
    result = estimate_upgrade_time(
        current_height=30500000,
        target_height=30466800,
        avg_block_time=6.0,
    )
    assert result["remaining_blocks"] == 0
    assert result["already_passed"] is True
    assert result["lead_time_hours"] == 0.0


def test_exactly_at_target():
    result = estimate_upgrade_time(
        current_height=30466800,
        target_height=30466800,
        avg_block_time=6.0,
    )
    assert result["already_passed"] is True


def test_fast_chain():
    result = estimate_upgrade_time(
        current_height=100000000,
        target_height=100100000,
        avg_block_time=0.4,  # SEI급 블록타임
    )
    assert result["remaining_blocks"] == 100000
    # 100000 * 0.4 = 40000초 = ~11.1시간
    assert 11.0 < result["lead_time_hours"] < 11.2


def test_estimated_time_is_future():
    from datetime import datetime, timezone
    result = estimate_upgrade_time(
        current_height=1000,
        target_height=2000,
        avg_block_time=10.0,
    )
    est_time = datetime.fromisoformat(result["estimated_time"])
    now = datetime.now(timezone.utc)
    assert est_time > now


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"  ✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n결과: {passed} 통과, {failed} 실패")
