"""state_store 유닛 테스트."""

import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_store import StateStore


def _make_store():
    """임시 파일로 StateStore 생성."""
    tmp = tempfile.mktemp(suffix=".json")
    return StateStore(state_file=tmp)


def test_new_proposal_is_new():
    store = _make_store()
    assert store.is_new_signal("cosmos", "1026", "VOTING") is True


def test_same_proposal_not_new():
    store = _make_store()
    store.mark_detected("cosmos", "1026", "VOTING")
    assert store.is_new_signal("cosmos", "1026", "VOTING") is False


def test_status_change_is_new():
    store = _make_store()
    store.mark_detected("cosmos", "1026", "VOTING")
    # 상태 변경: VOTING → PASSED
    assert store.is_new_signal("cosmos", "1026", "PASSED") is True


def test_different_chain_same_id():
    store = _make_store()
    store.mark_detected("cosmos", "100", "VOTING")
    assert store.is_new_signal("sei", "100", "VOTING") is True


def test_status_history():
    store = _make_store()
    store.mark_detected("cosmos", "1026", "VOTING")
    store.mark_detected("cosmos", "1026", "PASSED")

    entry = store.get("cosmos", "1026")
    assert entry is not None
    assert entry["last_status"] == "PASSED"
    assert len(entry["status_history"]) == 2
    assert entry["status_history"][0]["status"] == "VOTING"
    assert entry["status_history"][1]["status"] == "PASSED"


def test_persistence():
    tmp = tempfile.mktemp(suffix=".json")
    store1 = StateStore(state_file=tmp)
    store1.mark_detected("cosmos", "999", "VOTING")

    # 새 인스턴스로 다시 로드
    store2 = StateStore(state_file=tmp)
    assert store2.is_new_signal("cosmos", "999", "VOTING") is False
    assert store2.get("cosmos", "999") is not None


def test_clear():
    store = _make_store()
    store.mark_detected("cosmos", "1", "VOTING")
    store.mark_detected("sei", "2", "PASSED")
    store.clear()
    assert store.is_new_signal("cosmos", "1", "VOTING") is True
    assert store.get_all() == {}


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
