"""Duplicate listing guards for repeated exchange announcement updates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.poller import ExchangeListingPoller
from src.state_store import StateStore
from src.cpp_ultra_engine import CppUltraListingEngineBridge, DEFAULT_LIBRARY
from src.latency import NOOP_LATENCY_TRACE


class FakeBybitClient:
    def lookup_ticker(self, ticker: str) -> dict:
        return {"ticker": ticker, "spot": True, "perp": True}


class FakeSpotBuyer:
    def __init__(self):
        self.calls: list[dict] = []

    def buy_market(self, *, ticker: str, order_link_id: str) -> dict:
        self.calls.append({"ticker": ticker, "order_link_id": order_link_id})
        return {
            "enabled": True,
            "attempted": True,
            "executed": False,
            "reason": "test_buyer",
            "order_link_id": order_link_id,
        }


class FakeSignalEmitter:
    def __init__(self):
        self.persisted: list[dict] = []
        self.trade_proofs: list[dict] = []

    def build(self, *, post: dict, listing: dict, bybit: dict, trade: dict, latency=None) -> dict:
        return {
            "message_id": post["message_id"],
            "ticker": listing["ticker"],
            "asset_name": listing["asset_name"],
            "markets": listing["markets"],
            "trade": trade,
        }

    def persist(self, signal: dict):
        self.persisted.append(signal)

    def persist_trade_proof(self, *, post: dict, listing: dict, trade: dict):
        self.trade_proofs.append(
            {
                "message_id": post["message_id"],
                "ticker": listing["ticker"],
                "trade": trade,
            }
        )


class DisabledUltraEngine:
    def is_enabled(self) -> bool:
        return False


class MultiTickerRawResult:
    matched = 0
    duplicate = 0
    reason = b"multi_ticker"


class MultiTickerRawUltraEngine:
    def __init__(self):
        self.handle_calls = 0

    def is_enabled(self) -> bool:
        return True

    def warmup(self):
        return {"ok": True}

    def handle_post_raw(self, *, exchange: str, message_id: int, title: str):
        self.handle_calls += 1
        return MultiTickerRawResult()

    def payload_from_raw(self, raw_result):
        return None


class RecordingBybitClient(FakeBybitClient):
    def __init__(self, events: list[str]):
        self.events = events

    def lookup_ticker(self, ticker: str) -> dict:
        self.events.append("lookup")
        return {"ticker": ticker, "symbol": f"{ticker}USDT", "spot": True, "perp": True, "any": True}


class RecordingSignalEmitter(FakeSignalEmitter):
    def __init__(self, events: list[str]):
        super().__init__()
        self.events = events

    def persist_trade_proof(self, *, post: dict, listing: dict, trade: dict):
        self.events.append("proof")
        super().persist_trade_proof(post=post, listing=listing, trade=trade)

    def build(self, *, post: dict, listing: dict, bybit: dict, trade: dict, latency=None) -> dict:
        self.events.append("build")
        return super().build(post=post, listing=listing, bybit=bybit, trade=trade, latency=latency)

    def persist(self, signal: dict):
        self.events.append("persist")
        super().persist(signal)


class TraceWithPythonClock:
    def as_dict(self):
        return {
            "total_ns": 1000,
            "total_us": 1.0,
            "total_ms": 0.001,
            "stages_ns": {},
            "marks": ["start", "done"],
        }

    def start_ns(self):
        return 2000

    def last_ns(self):
        return 3000


def test_repeated_bithumb_listing_ticker_does_not_buy_twice(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    first = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 11403,
            "published_at": "2025-10-01T06:28:00+00:00",
            "title": "[마켓 추가/수수료 이벤트] 솜니아(SOMI) 원화 마켓 추가 (거래 수수료 무료)",
            "text": "[마켓 추가/수수료 이벤트] 솜니아(SOMI) 원화 마켓 추가 (거래 수수료 무료)",
            "post_url": "https://t.me/BithumbExchange/11403",
        },
    )
    second = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 11404,
            "published_at": "2025-10-01T06:31:00+00:00",
            "title": "[마켓 추가/수수료 이벤트] 솜니아(SOMI) 원화 마켓 추가 (거래 수수료 무료) (거래 오픈 3시 30분 )",
            "text": "[마켓 추가/수수료 이벤트] 솜니아(SOMI) 원화 마켓 추가 (거래 수수료 무료) (거래 오픈 3시 30분 )",
            "post_url": "https://t.me/BithumbExchange/11404",
        },
    )

    assert first is not None
    assert second is None
    assert [call["ticker"] for call in buyer.calls] == ["SOMI"]
    assert [signal["ticker"] for signal in emitter.persisted] == ["SOMI"]


def test_out_of_order_lower_listing_after_non_listing_is_not_dropped(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    non_listing = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 200,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[빗썸 시세알림] *전일 23:59 기준 대비",
            "text": "[빗썸 시세알림] *전일 23:59 기준 대비",
            "post_url": "https://t.me/BithumbExchange/200",
        },
    )
    listing = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 199,
            "published_at": "2026-06-11T12:59:58+00:00",
            "title": "[마켓 추가] 자마(ZAMA) 원화 마켓 추가(거래 오픈 오후 5시 예정)",
            "text": "[마켓 추가] 자마(ZAMA) 원화 마켓 추가(거래 오픈 오후 5시 예정)",
            "post_url": "https://t.me/BithumbExchange/199",
        },
    )

    assert non_listing is None
    assert listing is not None
    assert listing["ticker"] == "ZAMA"
    assert [call["ticker"] for call in buyer.calls] == ["ZAMA"]


def test_hot_state_accepts_out_of_order_lower_listing(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
        defer_persistence=True,
        hot_state_enabled=True,
        state_flush_interval_sec=0,
    )

    try:
        assert poller.process_post(
            "upbit",
            {
                "channel_handle": "upbit_news",
                "message_id": 300,
                "published_at": "2026-06-11T13:00:00+00:00",
                "title": "[안내] 업비트 이용 안내",
                "text": "[안내] 업비트 이용 안내",
                "post_url": "https://t.me/upbit_news/300",
            },
        ) is None
        signal = poller.process_post(
            "upbit",
            {
                "channel_handle": "upbit_news",
                "message_id": 299,
                "published_at": "2026-06-11T12:59:59+00:00",
                "title": "[거래] 바빌론(BABY) KRW 마켓 디지털 자산 추가",
                "text": "[거래] 바빌론(BABY) KRW 마켓 디지털 자산 추가",
                "post_url": "https://t.me/upbit_news/299",
            },
        )
    finally:
        poller.close()

    assert signal is not None
    assert signal["ticker"] == "BABY"
    assert [call["ticker"] for call in buyer.calls] == ["BABY"]


def test_native_listing_multi_ticker_payload_buys_each_ticker(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    signal = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991010,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "text": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "post_url": "https://t.me/BithumbExchange/991010",
            "native_listing": {
                "signal_type": "market_add",
                "ticker": "WLFI",
                "tickers": ["WLFI", "M"],
                "asset_name": "월드 리버티 파이낸셜",
                "markets": ["KRW"],
            },
        },
    )

    assert isinstance(signal, list)
    assert [item["ticker"] for item in signal] == ["WLFI", "M"]
    assert [item["asset_name"] for item in signal] == ["월드 리버티 파이낸셜", "밈코어"]
    assert [call["ticker"] for call in buyer.calls] == ["WLFI", "M"]
    assert [item["ticker"] for item in emitter.persisted] == ["WLFI", "M"]


def test_native_trades_align_to_fresh_tickers_after_listing_dedupe(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    state_store = StateStore(tmp_path / "state.json")
    state_store.mark_listing_seen("bithumb", "WLFI", 991019)
    poller = ExchangeListingPoller(
        state_store=state_store,
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    signal = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991020,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "text": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "post_url": "https://t.me/BithumbExchange/991020",
            "native_listing": {
                "signal_type": "market_add",
                "ticker": "WLFI",
                "tickers": ["WLFI", "M"],
                "asset_name": "월드 리버티 파이낸셜",
                "markets": ["KRW"],
                "assets": [
                    {"ticker": "WLFI", "asset_name": "월드 리버티 파이낸셜"},
                    {"ticker": "M", "asset_name": "밈코어"},
                ],
            },
            "native_trades": [
                {
                    "ticker": "WLFI",
                    "symbol": "WLFIUSDT",
                    "order_link_id": "native-WLFI",
                    "reason": "native_preflight",
                },
                {
                    "ticker": "M",
                    "symbol": "MUSDT",
                    "order_link_id": "native-M",
                    "reason": "native_preflight",
                },
            ],
        },
    )

    assert signal is not None
    assert signal["ticker"] == "M"
    assert signal["trade"]["ticker"] == "M"
    assert signal["trade"]["order_link_id"] == "native-M"
    assert [item["ticker"] for item in emitter.persisted] == ["M"]
    assert [item["trade"]["ticker"] for item in emitter.persisted] == ["M"]
    assert buyer.calls == []


def test_missing_native_trade_for_fresh_ticker_uses_python_buy_fallback(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    state_store = StateStore(tmp_path / "state.json")
    state_store.mark_listing_seen("bithumb", "WLFI", 991021)
    poller = ExchangeListingPoller(
        state_store=state_store,
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    signal = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991022,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "text": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "post_url": "https://t.me/BithumbExchange/991022",
            "native_listing": {
                "signal_type": "market_add",
                "ticker": "WLFI",
                "tickers": ["WLFI", "M"],
                "asset_name": "월드 리버티 파이낸셜",
                "markets": ["KRW"],
                "assets": [
                    {"ticker": "WLFI", "asset_name": "월드 리버티 파이낸셜"},
                    {"ticker": "M", "asset_name": "밈코어"},
                ],
            },
            "native_trades": [
                {
                    "ticker": "WLFI",
                    "symbol": "WLFIUSDT",
                    "order_link_id": "native-WLFI",
                    "reason": "native_preflight",
                },
            ],
        },
    )

    assert signal is not None
    assert signal["ticker"] == "M"
    assert signal["trade"]["reason"] == "test_buyer"
    assert signal["trade"]["ticker"] == "M"
    assert signal["trade"]["order_link_id"] == "ls-bithumb-991022-M"
    assert [call["ticker"] for call in buyer.calls] == ["M"]
    assert [item["ticker"] for item in emitter.persisted] == ["M"]


def test_short_bulk_buy_result_keeps_listing_aligned_disabled_trade(tmp_path):
    class ShortBulkBuyer(FakeSpotBuyer):
        def buy_markets(self, orders: list[dict]) -> list[dict]:
            self.calls.extend(orders)
            return [{"reason": "first_only"}]

    buyer = ShortBulkBuyer()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=FakeSignalEmitter(),
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    trades = poller._maybe_buy_spots(
        channel=poller._channel_runtime_by_id["bithumb"],
        post={"message_id": 991025},
        listings=[{"ticker": "AAA"}, {"ticker": "BBB"}],
    )

    assert trades == [
        {
            "reason": "first_only",
            "ticker": "AAA",
            "order_link_id": "ls-bithumb-991025-AAA",
        },
        {
            "enabled": False,
            "attempted": False,
            "executed": False,
            "ticker": "BBB",
            "order_link_id": "ls-bithumb-991025-BBB",
            "reason": "python_spot_buyer_missing_result",
        },
    ]


def test_out_of_order_bulk_buy_result_aligns_by_ticker(tmp_path):
    class OutOfOrderBulkBuyer(FakeSpotBuyer):
        def buy_markets(self, orders: list[dict]) -> list[dict]:
            self.calls.extend(orders)
            return [
                {"ticker": "BBB", "reason": "bbb_result"},
                {"ticker": "AAA", "reason": "aaa_result"},
            ]

    buyer = OutOfOrderBulkBuyer()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=FakeSignalEmitter(),
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    trades = poller._maybe_buy_spots(
        channel=poller._channel_runtime_by_id["bithumb"],
        post={"message_id": 991027},
        listings=[{"ticker": "AAA"}, {"ticker": "BBB"}],
    )

    assert [call["ticker"] for call in buyer.calls] == ["AAA", "BBB"]
    assert trades == [
        {
            "ticker": "AAA",
            "reason": "aaa_result",
            "order_link_id": "ls-bithumb-991027-AAA",
        },
        {
            "ticker": "BBB",
            "reason": "bbb_result",
            "order_link_id": "ls-bithumb-991027-BBB",
        },
    ]


def test_empty_bulk_buy_result_keeps_disabled_trade_for_every_listing(tmp_path):
    class EmptyBulkBuyer(FakeSpotBuyer):
        def buy_markets(self, orders: list[dict]):
            self.calls.extend(orders)
            return None

    buyer = EmptyBulkBuyer()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=FakeSignalEmitter(),
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    trades = poller._maybe_buy_spots(
        channel=poller._channel_runtime_by_id["bithumb"],
        post={"message_id": 991026},
        listings=[{"ticker": "AAA"}, {"ticker": "BBB"}],
    )

    assert [trade["ticker"] for trade in trades] == ["AAA", "BBB"]
    assert [trade["reason"] for trade in trades] == [
        "python_spot_buyer_missing_result",
        "python_spot_buyer_missing_result",
    ]
    assert [trade["order_link_id"] for trade in trades] == [
        "ls-bithumb-991026-AAA",
        "ls-bithumb-991026-BBB",
    ]


def test_native_trade_without_ticker_keeps_positional_fallback():
    listings = [{"ticker": "WLFI"}, {"ticker": "M"}]
    native_trades = [
        {"order_link_id": "first-positional"},
        {"order_link_id": "second-positional"},
    ]

    aligned = ExchangeListingPoller._align_native_trades_to_listings(
        listings=listings,
        native_trades=native_trades,
    )

    assert [trade["order_link_id"] for trade in aligned] == [
        "first-positional",
        "second-positional",
    ]


def test_duplicate_native_trade_proof_aligns_by_ticker_after_dedupe(tmp_path):
    emitter = FakeSignalEmitter()
    state_store = StateStore(tmp_path / "state.json")
    state_store.mark_listing_seen("bithumb", "WLFI", 991023)
    poller = ExchangeListingPoller(
        state_store=state_store,
        bybit_client=FakeBybitClient(),
        spot_buyer=FakeSpotBuyer(),
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    poller._finalize_native_trades_post_trade_work(
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991024,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "text": "[마켓 추가] 월드 리버티 파이낸셜(WLFI), 밈코어(M) 원화 마켓 추가",
            "post_url": "https://t.me/BithumbExchange/991024",
            "native_listing": {
                "signal_type": "market_add",
                "ticker": "WLFI",
                "tickers": ["WLFI", "M"],
                "asset_name": "월드 리버티 파이낸셜",
                "markets": ["KRW"],
                "assets": [
                    {"ticker": "WLFI", "asset_name": "월드 리버티 파이낸셜"},
                    {"ticker": "M", "asset_name": "밈코어"},
                ],
            },
        },
        poller._channel_runtime_by_id["bithumb"],
        [
            {"ticker": "WLFI", "order_link_id": "native-WLFI"},
            {"ticker": "M", "order_link_id": "native-M"},
        ],
    )

    assert [item["ticker"] for item in emitter.trade_proofs] == ["M"]
    assert [item["trade"]["order_link_id"] for item in emitter.trade_proofs] == ["native-M"]


def test_native_listing_string_tickers_are_not_split_into_characters(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    signal = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991011,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "native matched payload",
            "text": "native matched payload",
            "post_url": "https://t.me/BithumbExchange/991011",
            "native_listing": {
                "signal_type": "market_add",
                "ticker": "WLFI",
                "tickers": "WLFI",
                "asset_name": "월드 리버티 파이낸셜",
                "markets": "KRW",
            },
        },
    )

    assert signal is not None
    assert signal["ticker"] == "WLFI"
    assert signal["markets"] == ["KRW"]
    assert [call["ticker"] for call in buyer.calls] == ["WLFI"]
    assert [item["ticker"] for item in emitter.persisted] == ["WLFI"]


def test_duplicate_native_trade_payload_is_persisted_without_rebuy(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )
    post = {
        "channel_handle": "BithumbExchange",
        "message_id": 991012,
        "published_at": "2026-06-11T13:00:00+00:00",
        "title": "[마켓 추가] 월드 리버티 파이낸셜(WLFI) 원화 마켓 추가",
        "text": "[마켓 추가] 월드 리버티 파이낸셜(WLFI) 원화 마켓 추가",
        "post_url": "https://t.me/BithumbExchange/991012",
        "native_listing": {
            "signal_type": "market_add",
            "ticker": "WLFI",
            "tickers": ["WLFI"],
            "asset_name": "월드 리버티 파이낸셜",
            "markets": ["KRW"],
        },
    }

    first = poller.process_post("bithumb", dict(post))
    duplicate = poller.process_post(
        "bithumb",
        {
            **post,
            "native_trades": [
                {
                    "ticker": "WLFI",
                    "attempted": True,
                    "executed": True,
                    "reason": "tdlib_native_rest_preflight",
                }
            ],
        },
    )

    assert first is not None
    assert duplicate is None
    assert [call["ticker"] for call in buyer.calls] == ["WLFI"]
    assert [item["ticker"] for item in emitter.persisted] == ["WLFI", "WLFI"]
    assert emitter.persisted[-1]["trade"]["executed"] is True
    assert emitter.persisted[-1]["trade"]["reason"] == "tdlib_native_rest_preflight"
    assert [item["ticker"] for item in emitter.trade_proofs] == ["WLFI"]
    assert emitter.trade_proofs[-1]["trade"]["executed"] is True


def test_invalid_native_listing_falls_back_to_title_classifier(tmp_path):
    buyer = FakeSpotBuyer()
    emitter = FakeSignalEmitter()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )

    signal = poller.process_post(
        "bithumb",
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991013,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 밈코어(M) 원화 마켓 추가",
            "text": "[마켓 추가] 밈코어(M) 원화 마켓 추가",
            "post_url": "https://t.me/BithumbExchange/991013",
            "native_listing": "malformed",
        },
    )

    assert signal is not None
    assert signal["ticker"] == "M"
    assert [call["ticker"] for call in buyer.calls] == ["M"]


def test_deferred_finalize_persists_trade_proof_before_slow_signal_work(tmp_path):
    events: list[str] = []
    emitter = RecordingSignalEmitter(events)
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=RecordingBybitClient(events),
        spot_buyer=FakeSpotBuyer(),
        signal_emitter=emitter,
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
        defer_post_trade_work=True,
    )

    poller._finalize_post_trade_work(
        NOOP_LATENCY_TRACE,
        {
            "channel_handle": "BithumbExchange",
            "message_id": 991014,
            "published_at": "2026-06-11T13:00:00+00:00",
            "title": "[마켓 추가] 스타크넷(STRK) 원화 마켓 추가",
            "received_monotonic_ns": 1000,
        },
        {
            "exchange": "bithumb",
            "display_name": "빗썸",
            "signal_type": "market_add",
            "ticker": "STRK",
            "asset_name": "스타크넷",
            "markets": ["KRW"],
        },
        {
            "enabled": True,
            "attempted": True,
            "executed": False,
            "reason": "tdlib_native_rest_preflight",
            "trade_started_monotonic_ns": 1200,
            "order_send_started_monotonic_ns": 1700,
            "trade_finished_monotonic_ns": 2300,
        },
    )

    assert events == ["proof", "lookup", "build", "persist"]
    assert emitter.trade_proofs[0]["ticker"] == "STRK"
    assert emitter.trade_proofs[0]["trade"]["order_prepare_elapsed_ns"] == 500
    assert emitter.trade_proofs[0]["trade"]["trade_elapsed_ns"] == 1100


def test_latency_payload_separates_python_trace_clock_from_native_receive_clock():
    payload = ExchangeListingPoller._build_latency_payload(
        object(),
        TraceWithPythonClock(),
        {
            "message_id": 991015,
            "received_monotonic_ns": 1000,
            "received_python_monotonic_ns": 1500,
        },
        {"ticker": "STRK"},
        {
            "attempted": True,
            "executed": False,
            "order_send_started_monotonic_ns": 1700,
            "trade_finished_monotonic_ns": 1800,
        },
    )

    assert payload["receive_to_trace_start_ns"] == 500
    assert payload["receive_to_signal_ns"] == 1500
    assert payload["receive_to_order_send_started_ns"] == 700
    assert payload["receive_to_trade_finished_ns"] == 800


def test_cpp_ultra_no_ack_multi_ticker_falls_back_to_python_buy_path(tmp_path):
    buyer = FakeSpotBuyer()
    ultra_engine = MultiTickerRawUltraEngine()
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=buyer,
        signal_emitter=FakeSignalEmitter(),
        cpp_ultra_engine=ultra_engine,
        enable_bybit_warmup=False,
        defer_persistence=True,
        defer_post_trade_work=True,
        emit_ultra_ack=False,
        state_flush_interval_sec=0,
    )

    try:
        result = poller.process_post(
            "bithumb",
            {
                "channel_handle": "BithumbExchange",
                "message_id": 991016,
                "published_at": "2026-06-11T13:00:00+00:00",
                "title": "native matched payload",
                "text": "native matched payload",
                "post_url": "https://t.me/BithumbExchange/991016",
                "native_listing": {
                    "signal_type": "market_add",
                    "ticker": "SENT",
                    "tickers": ["SENT", "ELSA"],
                    "asset_name": "센티언트",
                    "markets": ["KRW"],
                    "assets": [
                        {"ticker": "SENT", "asset_name": "센티언트"},
                        {"ticker": "ELSA", "asset_name": "헤이엘사"},
                    ],
                },
            },
        )
    finally:
        poller.close()

    assert result is None
    assert ultra_engine.handle_calls == 1
    assert [call["ticker"] for call in buyer.calls] == ["SENT", "ELSA"]


def test_cpp_ultra_raw_finalize_preserves_all_multi_ticker_trades(tmp_path):
    poller = ExchangeListingPoller(
        state_store=StateStore(tmp_path / "state.json"),
        bybit_client=FakeBybitClient(),
        spot_buyer=FakeSpotBuyer(),
        signal_emitter=FakeSignalEmitter(),
        cpp_ultra_engine=DisabledUltraEngine(),
        enable_bybit_warmup=False,
    )
    finalized: list[tuple[str, str, str]] = []
    poller._finalize_post_trade_work = (
        lambda _trace, _post, listing, trade: finalized.append(
            (listing["ticker"], trade["symbol"], trade["order_link_id"])
        )
    )

    poller._finalize_cpp_ultra_raw_post_trade_work(
        NOOP_LATENCY_TRACE,
        {
            "message_id": 991017,
            "title": "[마켓 추가] 센티언트(SENT), 헤이엘사(ELSA) 원화 마켓 추가",
        },
        poller._channel_runtime_by_id["bithumb"],
        {
            "duplicate": False,
            "matched": True,
            "signal_type": "market_add",
            "ticker": "SENT",
            "tickers": ["SENT", "ELSA"],
            "asset_name": "센티언트",
            "markets": ["KRW"],
            "trade": {
                "ticker": "SENT",
                "symbol": "SENTUSDT",
                "order_link_id": "ls-b-991017-SENT",
            },
            "trades": [
                {
                    "ticker": "SENT",
                    "symbol": "SENTUSDT",
                    "order_link_id": "ls-b-991017-SENT",
                },
                {
                    "ticker": "ELSA",
                    "symbol": "ELSAUSDT",
                    "order_link_id": "ls-b-991017-ELSA",
                },
            ],
        },
        0,
        0,
    )

    assert finalized == [
        ("SENT", "SENTUSDT", "ls-b-991017-SENT"),
        ("ELSA", "ELSAUSDT", "ls-b-991017-ELSA"),
    ]


def test_cpp_ultra_raw_path_records_listing_ticker_state(tmp_path, monkeypatch):
    if not DEFAULT_LIBRARY.exists():
        pytest.skip("C++ ultra engine library is not built")

    monkeypatch.setenv("BYBIT_SPOT_BUY_ENABLED", "0")
    state_store = StateStore(tmp_path / "state.json")
    poller = ExchangeListingPoller(
        state_store=state_store,
        bybit_client=FakeBybitClient(),
        spot_buyer=FakeSpotBuyer(),
        signal_emitter=FakeSignalEmitter(),
        cpp_ultra_engine=CppUltraListingEngineBridge(enabled=True),
        enable_bybit_warmup=False,
        defer_persistence=True,
        defer_post_trade_work=True,
        emit_ultra_ack=False,
        state_flush_interval_sec=0,
    )

    try:
        result = poller.process_post(
            "bithumb",
            {
                "channel_handle": "BithumbExchange",
                "message_id": 991001,
                "published_at": "2026-06-11T13:00:00+00:00",
                "title": "[마켓 추가/수수료 이벤트] 로우패스(RAWD) 원화 마켓 추가 (거래 수수료 무료)",
                "text": "[마켓 추가/수수료 이벤트] 로우패스(RAWD) 원화 마켓 추가 (거래 수수료 무료)",
                "post_url": "https://t.me/BithumbExchange/991001",
            },
        )
    finally:
        poller.close()

    assert result is None
    assert state_store.has_seen_listing("bithumb", "RAWD")
