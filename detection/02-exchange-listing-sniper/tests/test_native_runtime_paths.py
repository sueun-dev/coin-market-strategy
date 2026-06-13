"""Smoke tests for compiled native runtime paths.

These tests do not place orders. They verify that the compiled binaries load,
classify the same actionable titles as Python, and report disabled trading as
disabled instead of as a successful or enabled trade path.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cpp_fast_buyer import CppFastBuyerBridge, DEFAULT_BINARY
from src.cpp_ultra_engine import CppUltraListingEngineBridge, DEFAULT_LIBRARY

CASES_PATH = Path(__file__).parent / "fixtures" / "listing_title_cases.json"
CASES = json.loads(CASES_PATH.read_text())
CASE_INDEX = {case["id"]: index for index, case in enumerate(CASES, start=1)}
SINGLE_TICKER_CASES = [
    case
    for case in CASES
    if case["expected"] is not None and len(case["expected"]["tickers"]) == 1
]
NEGATIVE_CASES = [case for case in CASES if case["expected"] is None]
TDLIB_RELAY_BINARY = Path(__file__).parent.parent / "bin" / "tdlib_json_relay"


def case_id(case: dict) -> str:
    return case["id"]


def message_id_for_case(case: dict) -> int:
    return 900000 + CASE_INDEX[case["id"]]


@pytest.mark.parametrize("case", SINGLE_TICKER_CASES, ids=case_id)
def test_cpp_ultra_engine_classifies_without_buying_when_trading_disabled(
    monkeypatch,
    case,
):
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    monkeypatch.setenv("BYBIT_SPOT_BUY_ENABLED", "0")
    bridge = CppUltraListingEngineBridge(enabled=True)

    listing = bridge.handle_post(
        exchange=case["exchange"],
        message_id=message_id_for_case(case),
        title=case["title"],
    )

    assert listing is not None
    assert listing["ticker"] == case["expected"]["ticker"]
    assert listing["asset_name"] == case["expected"]["asset_name"]
    assert listing["markets"] == case["expected"]["markets"]
    assert listing["trade"]["enabled"] is False
    assert listing["trade"]["attempted"] is False
    assert listing["trade"]["executed"] is False
    assert listing["trade"]["ret_code"] == -1
    assert listing["trade"]["reason"] == "buy_disabled"


@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=case_id)
def test_cpp_ultra_engine_rejects_non_actionable_posts(monkeypatch, case):
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    monkeypatch.setenv("BYBIT_SPOT_BUY_ENABLED", "0")
    bridge = CppUltraListingEngineBridge(enabled=True)

    listing = bridge.handle_post(
        exchange=case["exchange"],
        message_id=message_id_for_case(case),
        title=case["title"],
    )

    assert listing is None


def test_cpp_ultra_engine_dedups_repeated_listing_ticker(monkeypatch):
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    monkeypatch.setenv("BYBIT_SPOT_BUY_ENABLED", "0")
    bridge = CppUltraListingEngineBridge(enabled=True)
    title = "[마켓 추가/수수료 이벤트] 듀프테스트(DUPT) 원화 마켓 추가 (거래 수수료 무료)"

    first = bridge.handle_post(
        exchange="bithumb",
        message_id=990001,
        title=title,
    )
    second = bridge.handle_post(
        exchange="bithumb",
        message_id=990002,
        title=f"{title} (거래 오픈 3시 30분 )",
    )

    assert first is not None
    assert first["ticker"] == "DUPT"
    assert second == {
        "duplicate": True,
        "matched": False,
        "reason": "duplicate_listing_ticker",
    }


def test_cpp_ultra_engine_dedups_every_ticker_from_multi_listing(monkeypatch):
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    monkeypatch.setenv("BYBIT_SPOT_BUY_ENABLED", "0")
    bridge = CppUltraListingEngineBridge(enabled=True)
    first = bridge.handle_post(
        exchange="bithumb",
        message_id=990101,
        title="[마켓 추가] 알파테스트(TSTA), 베타테스트(TSTB) 원화 마켓 추가",
    )
    second = bridge.handle_post(
        exchange="bithumb",
        message_id=990102,
        title="[마켓 추가] 베타테스트(TSTB) 원화 마켓 추가",
    )

    assert first is not None
    assert first["tickers"] == ["TSTA", "TSTB"]
    assert second == {
        "duplicate": True,
        "matched": False,
        "reason": "duplicate_listing_ticker",
    }


def test_cpp_ultra_engine_keeps_fresh_tickers_from_mixed_multi_listing(monkeypatch):
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    monkeypatch.setenv("BYBIT_SPOT_BUY_ENABLED", "0")
    bridge = CppUltraListingEngineBridge(enabled=True)
    first = bridge.handle_post(
        exchange="bithumb",
        message_id=990201,
        title="[마켓 추가] 기존테스트(PRTD) 원화 마켓 추가",
    )
    second = bridge.handle_post(
        exchange="bithumb",
        message_id=990202,
        title="[마켓 추가] 기존테스트(PRTD), 신규테스트(PRTE) 원화 마켓 추가",
    )

    assert first is not None
    assert first["ticker"] == "PRTD"
    assert second is not None
    assert second["duplicate"] is False
    assert second["ticker"] == "PRTE"
    assert second["tickers"] == ["PRTE"]
    assert second["asset_name"] == "신규테스트"
    assert second["trade"]["reason"] == "buy_disabled"


def test_cpp_ultra_preflight_order_link_id_matches_python_contract():
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    script = """
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from src.cpp_ultra_engine import CppUltraListingEngineBridge

bridge = CppUltraListingEngineBridge(enabled=True)
listing = bridge.handle_post(
    exchange="bithumb",
    message_id=12345,
    title="[마켓 추가] 센티언트(SENT) 원화 마켓 추가",
)
print(json.dumps(listing, ensure_ascii=False))
"""
    env = os.environ.copy()
    env.update(
        {
            "BYBIT_API_KEY": "test-key",
            "BYBIT_API_SECRET": "test-secret",
            "BYBIT_SPOT_BUY_ENABLED": "1",
            "BYBIT_SPOT_BUY_USDT_AMOUNT": "5",
            "BYBIT_PREFER_CACHED_SYMBOL_CHECK": "1",
            "LISTING_CPP_ULTRA_ORDER_ON_CACHE_MISS": "1",
            "LISTING_CPP_ULTRA_ORDER_PREFLIGHT_ONLY": "1",
        }
    )

    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(DEFAULT_LIBRARY.parent.parent),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=5,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["trade"]["order_link_id"] == "ls-bithumb-12345-SENT"
    assert payload["trade"]["reason"] == "cpp_ultra_rest_preflight"


def test_cpp_fast_buyer_binary_ping():
    if not DEFAULT_BINARY.exists():
        pytest.skip("C++ fast buyer binary is not built")

    bridge = CppFastBuyerBridge(enabled=True)
    try:
        assert bridge.ping() == {"ok": True, "pong": True}
    finally:
        bridge.close()


@pytest.mark.parametrize("case", CASES, ids=case_id)
def test_tdlib_relay_cli_classifier_matches_golden_cases(case):
    if not TDLIB_RELAY_BINARY.exists():
        pytest.skip("TDLib relay binary is not built")

    completed = subprocess.run(
        [
            str(TDLIB_RELAY_BINARY),
            "--classify-title",
            case["exchange"],
            case["title"],
        ],
        cwd=str(TDLIB_RELAY_BINARY.parent.parent),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=5,
        check=False,
    )

    assert completed.returncode == 0, completed.stdout
    payload = json.loads(completed.stdout)
    expected = case["expected"]
    if expected is None:
        assert payload == {"matched": False}
        return

    assert payload["matched"] is True
    assert payload["signal_type"] == expected["signal_type"]
    assert payload["ticker"] == expected["ticker"]
    assert payload["tickers"] == expected["tickers"]
    assert payload["asset_name"] == expected["asset_name"]
    assert payload["markets"] == expected["markets"]
