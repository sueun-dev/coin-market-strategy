"""Cosmos governance source tests."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cosmos_governance_source import CosmosGovernanceSource


def test_proposal_to_event_converts_upgrade_proposal():
    source = CosmosGovernanceSource()
    target = {"chain_id": "injective"}
    proposal = {
        "id": "628",
        "title": "Real-Time USDC Mainnet Upgrade",
        "summary": "Upgrade proposal",
        "status": "PROPOSAL_STATUS_VOTING_PERIOD",
        "messages": [
            {
                "@type": "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade",
                "plan": {"name": "v1.18.3", "height": "161472000"},
            }
        ],
        "final_tally_result": {
            "yes_count": "10",
            "no_count": "0",
            "abstain_count": "0",
            "no_with_veto_count": "0",
        },
        "voting_end_time": "2026-04-06T14:18:27.150989022Z",
    }
    event = source._proposal_to_event(
        target,
        proposal,
        ["https://injective-rest.publicnode.com"],
        current_height=161470000,
        avg_block_time=0.6,
    )
    source.close()
    assert event is not None
    assert event["source_type"] == "governance"
    assert event["stage"] == "governance_voting"
    assert event["network_event_height"] == 161472000
    assert event["metadata"]["proposal_id"] == "628"


def test_proposal_to_event_skips_past_upgrade_height():
    source = CosmosGovernanceSource()
    target = {"chain_id": "injective"}
    proposal = {
        "id": "624",
        "title": "Past upgrade",
        "summary": "Already happened",
        "status": "PROPOSAL_STATUS_PASSED",
        "messages": [
            {
                "@type": "/cosmos.upgrade.v1beta1.MsgSoftwareUpgrade",
                "plan": {"name": "v1.17.0", "height": "100"},
            }
        ],
        "final_tally_result": {
            "yes_count": "10",
            "no_count": "0",
            "abstain_count": "0",
            "no_with_veto_count": "0",
        },
        "voting_end_time": "2026-04-06T14:18:27.150989022Z",
    }
    event = source._proposal_to_event(
        target,
        proposal,
        ["https://injective-rest.publicnode.com"],
        current_height=200,
        avg_block_time=0.6,
    )
    source.close()
    assert event is None
