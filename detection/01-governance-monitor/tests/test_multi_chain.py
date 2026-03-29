#!/usr/bin/env python3
"""
비-Cosmos 체인 거버넌스 API 통합 테스트.
각 체인의 실제 API를 호출하여 데이터 조회 가능 여부를 검증한다.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.multi_chain_client import MultiChainGovernanceClient

CONFIG_FILE = Path(__file__).parent.parent / "config" / "multi_chains.json"


def load_config():
    with open(CONFIG_FILE) as f:
        return json.load(f)


def test_polkadot():
    """Polkadot OpenGov 레퍼렌덤 조회."""
    print("\n" + "─" * 50)
    print("🔧 DOT (Polkadot) — OpenGov")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "polkadot")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:3]:
            print(f"    #{p['proposal_id']}: [{p['status']}] {p['title'][:50]}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_tezos():
    """Tezos 투표 기간 + 프로포절 조회."""
    print("\n" + "─" * 50)
    print("🔧 XTZ (Tezos) — Self-Amendment")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "tezos")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:3]:
            print(f"    #{p['proposal_id']}: [{p['status']}] {p['title'][:50]}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "프로포절이 하나도 없음 (투표 기간이 항상 존재해야 함)"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_aptos():
    """Aptos 체인 상태 + 거버넌스 조회."""
    print("\n" + "─" * 50)
    print("🔧 APT (Aptos) — On-chain Governance")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "aptos")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:3]:
            print(f"    #{p['proposal_id'][:30]}: [{p['status']}] {p['title'][:50]}")
            if p.get("plan", {}).get("height"):
                print(f"      블록: {p['plan']['height']:,}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "체인 상태도 못 가져옴"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_sui():
    """Sui 프로토콜 버전 조회."""
    print("\n" + "─" * 50)
    print("🔧 SUI (Sui) — Protocol Version")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "sui")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:3]:
            print(f"    #{p['proposal_id']}: [{p['status']}] {p['title'][:50]}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "프로토콜 버전 조회 실패"
        # 프로토콜 버전이 실제 숫자인지
        pv = proposals[0].get("plan", {}).get("name", "")
        assert pv.startswith("v"), f"프로토콜 버전 형식 이상: {pv}"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_algorand():
    """Algorand 프로토콜 업그레이드 상태 조회."""
    print("\n" + "─" * 50)
    print("🔧 ALGO (Algorand) — Consensus Upgrade")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "algorand")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals:
            extra = p.get("extra", {})
            print(f"    #{p['proposal_id']}: [{p['status']}]")
            print(f"      Version: {p['plan']['name']}")
            print(f"      Last Round: {extra.get('last_round', '?'):,}")
            print(f"      Next Version Round: {extra.get('next_version_round', '?'):,}")
            print(f"      Supported: {extra.get('supported', '?')}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "상태 조회 실패"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_cardano():
    """Cardano 에포크 + 거버넌스 조회."""
    print("\n" + "─" * 50)
    print("🔧 ADA (Cardano) — CIP Governance")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "cardano")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:5]:
            print(f"    #{p['proposal_id'][:30]}: [{p['status']}] {p['title'][:50]}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "에포크 정보도 못 가져옴"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_icon():
    """ICON 네트워크 프로포절 조회."""
    print("\n" + "─" * 50)
    print("🔧 ICX (ICON) — Network Proposal")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "icon")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:3]:
            print(f"    #{p['proposal_id'][:20]}: [{p['status']}] {p['title'][:50]}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "블록 상태도 못 가져옴"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


def test_celo():
    """Celo 블록 + 거버넌스 조회."""
    print("\n" + "─" * 50)
    print("🔧 CELO (Celo) — CGP Governance")
    config = load_config()
    chain = next(c for c in config["chains"] if c["chain_id"] == "celo")
    client = MultiChainGovernanceClient(chain)
    try:
        proposals = client.fetch_upgrade_proposals()
        print(f"  조회 결과: {len(proposals)}건")
        for p in proposals[:3]:
            print(f"    #{p['proposal_id'][:20]}: [{p['status']}] {p['title'][:50]}")
        assert isinstance(proposals, list), "응답이 list가 아님"
        assert len(proposals) > 0, "블록 높이도 못 가져옴"
        print("  ✅ PASSED")
        return True
    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False
    finally:
        client.close()


if __name__ == "__main__":
    tests = [
        test_polkadot,
        test_tezos,
        test_aptos,
        test_sui,
        test_algorand,
        test_cardano,
        test_icon,
        test_celo,
    ]

    passed = 0
    failed = 0
    failed_names = []

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
                failed_names.append(test.__name__)
        except Exception as e:
            print(f"  ❌ ERROR: {type(e).__name__}: {e}")
            failed += 1
            failed_names.append(test.__name__)

    print("\n" + "=" * 50)
    print(f"결과: {passed}/{passed + failed} 통과")
    if failed_names:
        print(f"실패: {', '.join(failed_names)}")
    print("=" * 50)

    if failed:
        sys.exit(1)
