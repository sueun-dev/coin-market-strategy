"""통합 테스트: 실제 RPC에 연결하여 E2E 검증."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cosmos_client import CosmosClient
from src.proposal_filter import filter_upgrade_proposals
from src.upgrade_time_estimator import estimate_upgrade_time


COSMOS_CONFIG = {
    "chain_id": "cosmoshub",
    "name": "Cosmos Hub",
    "ticker": "ATOM",
    "rpc_endpoints": [
        "https://cosmos-rest.publicnode.com",
        "https://rest.cosmos.directory/cosmoshub",
    ],
    "gov_api_version": "v1",
    "avg_block_time_seconds": 6.0,
}


def test_fetch_voting_proposals():
    """실제 RPC에서 투표 중 프로포절 조회."""
    client = CosmosClient(COSMOS_CONFIG)
    try:
        proposals = client.fetch_voting_proposals()
        assert isinstance(proposals, list)
        print(f"  투표 중 프로포절: {len(proposals)}건")
        for p in proposals:
            print(f"    #{p['id']}: {p.get('title', 'N/A')}")
    finally:
        client.close()


def test_fetch_passed_proposals():
    """실제 RPC에서 통과된 프로포절 조회."""
    client = CosmosClient(COSMOS_CONFIG)
    try:
        proposals = client.fetch_passed_proposals(limit=3)
        assert isinstance(proposals, list)
        assert len(proposals) > 0
        print(f"  통과된 프로포절: {len(proposals)}건")
    finally:
        client.close()


def test_get_block_height():
    """현재 블록 높이 조회."""
    client = CosmosClient(COSMOS_CONFIG)
    try:
        height = client.get_latest_block_height()
        assert height is not None
        assert height > 30000000  # 2026년 기준 3천만 이상
        print(f"  현재 블록 높이: {height:,}")
    finally:
        client.close()


def test_calculate_block_time():
    """블록타임 동적 계산."""
    client = CosmosClient(COSMOS_CONFIG)
    try:
        bt = client.calculate_avg_block_time(sample_count=50)
        assert bt is not None
        assert 4.0 < bt < 10.0  # Cosmos Hub은 보통 5~7초
        print(f"  블록타임: {bt:.2f}s")
    finally:
        client.close()


def test_e2e_upgrade_detection():
    """E2E: 프로포절 조회 → 필터링 → 시간 예측까지."""
    client = CosmosClient(COSMOS_CONFIG)
    try:
        # 투표 중 + 통과 프로포절 수집
        all_proposals = client.fetch_voting_proposals() + client.fetch_passed_proposals(limit=5)
        assert len(all_proposals) > 0
        print(f"  전체 프로포절: {len(all_proposals)}건")

        # 업그레이드 필터링
        upgrades = filter_upgrade_proposals(all_proposals)
        print(f"  업그레이드 프로포절: {len(upgrades)}건")

        if upgrades:
            # 첫 번째 업그레이드에 대해 시간 예측
            upgrade = upgrades[0]
            current_height = client.get_latest_block_height()
            assert current_height is not None

            target_height = upgrade["plan"]["height"]
            bt = client.get_avg_block_time(50) or 6.0

            estimate = estimate_upgrade_time(current_height, target_height, bt)

            print("  첫 번째 업그레이드:")
            print(f"    이름: {upgrade['plan']['name']}")
            print(f"    타겟 블록: {target_height:,}")
            print(f"    현재 블록: {current_height:,}")
            print(f"    이미 완료: {estimate['already_passed']}")
            if not estimate["already_passed"]:
                print(f"    남은 블록: {estimate['remaining_blocks']:,}")
                print(f"    리드타임: {estimate['lead_time_hours']}시간")
    finally:
        client.close()


def test_rpc_failover():
    """RPC 장애 시 백업 전환 테스트."""
    config = COSMOS_CONFIG.copy()
    config["rpc_endpoints"] = [
        "https://invalid-endpoint.example.com",  # 실패할 주소
        "https://cosmos-rest.publicnode.com",     # 백업
    ]
    client = CosmosClient(config)
    try:
        height = client.get_latest_block_height()
        assert height is not None
        print(f"  Failover 성공, 블록 높이: {height:,}")
    finally:
        client.close()


if __name__ == "__main__":
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        print(f"\n{'─'*40}")
        print(f"🔧 {name}")
        try:
            test()
            print("  ✅ PASSED")
            passed += 1
        except AssertionError as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{'='*40}")
    print(f"결과: {passed} 통과, {failed} 실패")
