from __future__ import annotations

import os
import sys
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

import src.cpp_ultra_engine as cpp_ultra_engine  # noqa: E402
from src.cpp_ultra_engine import (  # noqa: E402
    CppUltraListingEngineBridge,
    NativeUltraResultV1Struct,
    NativeUltraResultV2Struct,
)


def test_cpp_ultra_payload_supports_v1_result_struct():
    bridge = CppUltraListingEngineBridge(enabled=False)
    result = NativeUltraResultV1Struct()
    result.matched = 1
    result.market_flags = 1
    result.ret_code = -1
    result.ticker = b"SENT"
    result.asset_name = "센티언트".encode("utf-8")
    result.signal_type = b"market_add"
    result.reason = b"buy_disabled"

    payload = bridge.payload_from_raw(result)

    assert payload["ticker"] == "SENT"
    assert payload["tickers"] == ["SENT"]
    assert payload["markets"] == ["KRW"]
    assert payload["trade"]["enabled"] is False
    assert payload["trade"]["reason"] == "buy_disabled"


def test_cpp_ultra_payload_supports_v2_multi_trade_fetch():
    bridge = CppUltraListingEngineBridge(enabled=False)
    result = NativeUltraResultV2Struct()
    result.matched = 1
    result.market_flags = 1
    result.trade_count = 2
    result.attempted_count = 2
    result.ticker = b"SENT"
    result.asset_name = "센티언트".encode("utf-8")
    result.signal_type = b"market_add"
    result.reason = b"cpp_ultra_rest"

    def fake_get_trades(exchange, message_id, out, capacity):
        out[0].attempted = 1
        out[0].ticker = b"SENT"
        out[0].symbol = b"SENTUSDT"
        out[0].order_link_id = b"ls-b-1-SENT"
        out[0].transport = b"cpp_ultra"
        out[0].reason = b"test"
        out[1].attempted = 1
        out[1].ticker = b"ELSA"
        out[1].symbol = b"ELSAUSDT"
        out[1].order_link_id = b"ls-b-1-ELSA"
        out[1].transport = b"cpp_ultra"
        out[1].reason = b"test"
        return 2

    bridge._get_trades = fake_get_trades

    payload = bridge.payload_from_raw(result, exchange="bithumb", message_id=1)

    assert payload["ticker"] == "SENT"
    assert payload["tickers"] == ["SENT", "ELSA"]
    assert payload["trade_count"] == 2
    assert [trade["symbol"] for trade in payload["trades"]] == ["SENTUSDT", "ELSAUSDT"]


def test_cpp_ultra_bridge_primes_native_runtime_env(monkeypatch):
    native_env = {
        "BYBIT_TIMESTAMP_BIAS_MS": "-50",
        "LISTING_CPP_ULTRA_ORDER_ON_CACHE_MISS": "1",
        "LISTING_CPP_ULTRA_ORDER_PREFLIGHT_ONLY": "1",
    }
    for key in native_env:
        monkeypatch.delenv(key, raising=False)

    def fake_load_env_settings(keys):
        if native_env.keys() <= keys:
            return native_env
        return {}

    monkeypatch.setattr(cpp_ultra_engine, "load_env_settings", fake_load_env_settings)

    CppUltraListingEngineBridge(enabled=False)

    for key, value in native_env.items():
        assert os.environ[key] == value
