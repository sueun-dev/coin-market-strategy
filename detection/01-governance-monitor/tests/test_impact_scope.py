"""impact_scope 유닛 테스트."""

import json
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.impact_scope import build_impact_scope
from src.signal_emitter import SignalEmitter


def test_build_impact_scope_defaults():
    chain_config = {
        "ticker": "atom",
        "listed": {
            "upbit": True,
            "bithumb": True,
            "coinone": False,
        },
    }

    scope = build_impact_scope(chain_config)

    assert scope["affected_tickers"] == ["ATOM"]
    assert scope["exchanges_affected"] == ["upbit", "bithumb"]


def test_build_impact_scope_uses_explicit_affected_tickers():
    chain_config = {
        "ticker": "POL",
        "affected_tickers": ["POL", "GMT", "POL"],
        "listed": {
            "upbit": True,
            "bithumb": False,
        },
    }

    scope = build_impact_scope(chain_config)

    assert scope["affected_tickers"] == ["POL", "GMT"]
    assert scope["exchanges_affected"] == ["upbit"]


def test_signal_emitter_includes_impact_scope():
    with tempfile.TemporaryDirectory() as tmpdir:
        emitter = SignalEmitter(signals_dir=tmpdir)
        signal = emitter.emit(
            chain_id="polygon",
            ticker="POL",
            proposal={
                "proposal_id": "123",
                "title": "Polygon Upgrade",
                "status": "PROPOSAL_STATUS_VOTING_PERIOD",
                "plan": {"name": "v2", "height": 12345},
                "yes_pct": 88.0,
                "voting_end_time": "2026-04-03T12:00:00Z",
                "expedited": False,
            },
            upgrade_estimate={
                "estimated_time": "2026-04-04T00:00:00Z",
                "lead_time_hours": 24,
                "remaining_blocks": 1000,
                "already_passed": False,
            },
            affected_tickers=["POL", "GMT"],
            exchanges_affected=["upbit"],
            confidence="high",
        )

        assert signal["affected_tickers"] == ["POL", "GMT"]
        assert signal["exchanges_affected"] == ["upbit"]

        signal_files = list(Path(tmpdir).glob("*.json"))
        assert len(signal_files) == 1

        stored = json.loads(signal_files[0].read_text())
        assert stored["affected_tickers"] == ["POL", "GMT"]
        assert stored["exchanges_affected"] == ["upbit"]


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
