from __future__ import annotations

import sys
from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_DIR))

from main import (  # noqa: E402
    _env_csv_set,
    _env_int,
    _python_bybit_order_path_enabled,
    _race_run_options_from_env,
    _tdlib_native_buy_parallel_race,
    _tdlib_native_buy_relay_active,
)


class _Args:
    def __init__(
        self,
        *,
        realtime_backend: str = "race",
        ultra_buy: bool = True,
        no_trade: bool = False,
        source_only: bool = False,
    ):
        self.realtime_backend = realtime_backend
        self.ultra_buy = ultra_buy
        self.no_trade = no_trade
        self.source_only = source_only


def test_env_int_reads_valid_value(monkeypatch):
    monkeypatch.setenv("LISTING_RACE_MIN_READY_BACKENDS", "2")

    assert _env_int("LISTING_RACE_MIN_READY_BACKENDS", 1) == 2


def test_env_int_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("LISTING_RACE_MIN_READY_BACKENDS", "bad")

    assert _env_int("LISTING_RACE_MIN_READY_BACKENDS", 1) == 1


def test_env_csv_set_normalizes_required_backends(monkeypatch):
    monkeypatch.setenv("LISTING_RACE_REQUIRED_BACKENDS", "tdlib, Telethon,,")

    assert _env_csv_set("LISTING_RACE_REQUIRED_BACKENDS") == {"tdlib", "telethon"}


def test_race_run_options_include_min_ready_and_required_backends(monkeypatch):
    monkeypatch.setenv("LISTING_RACE_MIN_READY_BACKENDS", "3")
    monkeypatch.setenv("LISTING_RACE_REQUIRED_BACKENDS", "tdlib,pyrogram")

    assert _race_run_options_from_env() == {
        "min_ready_backends": 3,
        "required_backends": {"tdlib", "pyrogram"},
    }


def test_race_run_options_default_min_ready_is_configurable(monkeypatch):
    monkeypatch.delenv("LISTING_RACE_MIN_READY_BACKENDS", raising=False)
    monkeypatch.delenv("LISTING_RACE_REQUIRED_BACKENDS", raising=False)

    assert _race_run_options_from_env(default_min_ready=2) == {
        "min_ready_backends": 2,
    }


def test_tdlib_native_parallel_race_requires_explicit_env(monkeypatch):
    args = _Args(realtime_backend="race")
    monkeypatch.delenv("LISTING_RACE_TDLIB_NATIVE_BUY_ENABLED", raising=False)

    assert not _tdlib_native_buy_parallel_race(args, realtime_mode=True)

    monkeypatch.setenv("LISTING_RACE_TDLIB_NATIVE_BUY_ENABLED", "1")
    assert _tdlib_native_buy_parallel_race(args, realtime_mode=True)
    assert _tdlib_native_buy_relay_active(args, realtime_mode=True)
    assert not _python_bybit_order_path_enabled(args, realtime_mode=True)


def test_tdlib_native_disabled_when_no_trade_or_source_only(monkeypatch):
    monkeypatch.setenv("LISTING_RACE_TDLIB_NATIVE_BUY_ENABLED", "1")

    assert not _tdlib_native_buy_relay_active(
        _Args(no_trade=True),
        realtime_mode=True,
    )
    assert not _tdlib_native_buy_relay_active(
        _Args(source_only=True),
        realtime_mode=True,
    )
