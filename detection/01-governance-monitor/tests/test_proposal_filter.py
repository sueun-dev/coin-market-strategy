"""proposal_filter 유닛 테스트."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.proposal_filter import (
    is_upgrade_proposal,
    extract_upgrade_plan,
    calculate_yes_percentage,
    filter_upgrade_proposals,
)


# ── 실제 ATOM v27.1.0 프로포절 데이터 (v1 형식) ──────────────

ATOM_V27_1_PROPOSAL = {
    "id": "1026",
    "messages": [
        {
            "@type": "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade",
            "authority": "cosmos10d07y265gmmuvt4z0w9aw880jnsr700j6zn9kn",
            "plan": {
                "name": "v27.1.0",
                "time": "0001-01-01T00:00:00Z",
                "height": "30466800",
                "info": '{"binaries": {}}',
                "upgraded_client_state": None,
            },
        }
    ],
    "status": "PROPOSAL_STATUS_VOTING_PERIOD",
    "final_tally_result": {
        "yes_count": "0",
        "abstain_count": "0",
        "no_count": "0",
        "no_with_veto_count": "0",
    },
    "submit_time": "2026-03-24T14:09:31.849071789Z",
    "voting_end_time": "2026-03-31T14:28:15.379921462Z",
    "title": "Gaia v27.1.0 Upgrade",
    "summary": "The v27.1.0 upgrade bumps wasmd...",
    "expedited": False,
}

ATOM_V25_3_PROPOSAL = {
    "id": "1021",
    "messages": [
        {
            "@type": "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade",
            "plan": {
                "name": "v25.3.0",
                "height": "29288700",
            },
        }
    ],
    "status": "PROPOSAL_STATUS_PASSED",
    "final_tally_result": {
        "yes_count": "132286133419111",
        "abstain_count": "222402037805",
        "no_count": "15826876569",
        "no_with_veto_count": "2589270456",
    },
    "submit_time": "2026-01-06T17:10:55.020355684Z",
    "voting_end_time": "2026-01-09T17:23:19.375514836Z",
    "title": "Gaia v25.3.0 Upgrade",
    "summary": "",
    "expedited": True,
}

# IBC 프로포절 (업그레이드 아님)
IBC_RECOVERY_PROPOSAL = {
    "id": "1027",
    "messages": [
        {
            "@type": "/ibc.core.client.v1.MsgRecoverClient",
            "subject_client_id": "07-tendermint-620",
        }
    ],
    "status": "PROPOSAL_STATUS_VOTING_PERIOD",
    "final_tally_result": {
        "yes_count": "0",
        "abstain_count": "0",
        "no_count": "0",
        "no_with_veto_count": "0",
    },
    "title": "Recover expired IBC Client for EVMOS Network",
}

# v1beta1 형식 (정규화 후)
V1BETA1_UPGRADE = {
    "id": "108",
    "messages": [
        {
            "@type": "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal",
            "plan": {
                "name": "v5.0.0",
                "height": "120000000",
            },
        }
    ],
    "content": {
        "@type": "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal",
        "title": "SEI v5.0.0 Upgrade",
        "plan": {
            "name": "v5.0.0",
            "height": "120000000",
        },
    },
    "status": "PROPOSAL_STATUS_PASSED",
    "final_tally_result": {
        "yes_count": "1000000",
        "abstain_count": "100000",
        "no_count": "50000",
        "no_with_veto_count": "10000",
    },
    "submit_time": "2025-05-20T00:00:00Z",
    "voting_end_time": "2025-05-27T00:00:00Z",
    "title": "SEI v5.0.0 Upgrade",
    "summary": "",
    "expedited": False,
}


def test_is_upgrade_proposal_v1():
    assert is_upgrade_proposal(ATOM_V27_1_PROPOSAL) is True
    assert is_upgrade_proposal(ATOM_V25_3_PROPOSAL) is True


def test_is_not_upgrade_proposal():
    assert is_upgrade_proposal(IBC_RECOVERY_PROPOSAL) is False


def test_is_upgrade_v1beta1():
    assert is_upgrade_proposal(V1BETA1_UPGRADE) is True


def test_extract_plan_v1():
    plan = extract_upgrade_plan(ATOM_V27_1_PROPOSAL)
    assert plan is not None
    assert plan["name"] == "v27.1.0"
    assert plan["height"] == 30466800


def test_extract_plan_v25():
    plan = extract_upgrade_plan(ATOM_V25_3_PROPOSAL)
    assert plan is not None
    assert plan["name"] == "v25.3.0"
    assert plan["height"] == 29288700


def test_extract_plan_v1beta1():
    plan = extract_upgrade_plan(V1BETA1_UPGRADE)
    assert plan is not None
    assert plan["name"] == "v5.0.0"
    assert plan["height"] == 120000000


def test_extract_plan_non_upgrade():
    plan = extract_upgrade_plan(IBC_RECOVERY_PROPOSAL)
    assert plan is None


def test_yes_percentage_passed():
    pct = calculate_yes_percentage(ATOM_V25_3_PROPOSAL)
    assert pct > 99.0  # 99.82%


def test_yes_percentage_zero_votes():
    pct = calculate_yes_percentage(ATOM_V27_1_PROPOSAL)
    assert pct == 0.0


def test_yes_percentage_mixed():
    pct = calculate_yes_percentage(V1BETA1_UPGRADE)
    # 1000000 / (1000000 + 50000 + 100000 + 10000) = 86.2%
    assert 86.0 < pct < 87.0


def test_filter_upgrade_proposals():
    proposals = [ATOM_V27_1_PROPOSAL, IBC_RECOVERY_PROPOSAL, ATOM_V25_3_PROPOSAL]
    results = filter_upgrade_proposals(proposals)
    assert len(results) == 2
    ids = {r["proposal_id"] for r in results}
    assert "1026" in ids
    assert "1021" in ids
    assert "1027" not in ids


def test_filter_preserves_data():
    results = filter_upgrade_proposals([ATOM_V27_1_PROPOSAL])
    r = results[0]
    assert r["proposal_id"] == "1026"
    assert r["title"] == "Gaia v27.1.0 Upgrade"
    assert r["status"] == "PROPOSAL_STATUS_VOTING_PERIOD"
    assert r["plan"]["name"] == "v27.1.0"
    assert r["plan"]["height"] == 30466800
    assert r["yes_pct"] == 0.0
    assert r["expedited"] is False


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
