"""Main poller for exchange listing announcements."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from .announcement_filter import (
    extract_listing_assets,
    has_multiple_listing_assets_fast,
    make_listing_title_classifier,
)
from .bybit_client import BybitClient
from .bybit_spot_buyer import BybitSpotBuyer
from .channel_client import TelegramChannelClient
from .cpp_ultra_engine import CppUltraListingEngineBridge
from .latency import LatencyTrace, NOOP_LATENCY_TRACE
from .signal_emitter import SignalEmitter
from .source_emitter import SourceEventEmitter
from .state_store import StateStore

logger = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).parent.parent / "config" / "channels.json"


class _ChannelRuntime:
    __slots__ = (
        "channel_id",
        "channel_handle",
        "exchange",
        "display_name",
        "order_link_prefix",
        "classify_title",
        "classify_title_fast",
    )

    def __init__(
        self,
        *,
        channel_id: str,
        channel_handle: str,
        exchange: str,
        display_name: str,
        order_link_prefix: str,
        classify_title: Callable[[str], dict | None],
        classify_title_fast: Callable[[str], dict | None],
    ):
        self.channel_id = channel_id
        self.channel_handle = channel_handle
        self.exchange = exchange
        self.display_name = display_name
        self.order_link_prefix = order_link_prefix
        self.classify_title = classify_title
        self.classify_title_fast = classify_title_fast


class ExchangeListingPoller:
    """Poll official Telegram channels for listing announcements."""

    def __init__(
        self,
        config_file: Path | str = CONFIG_FILE,
        poll_interval: int = 15,
        channel_client: TelegramChannelClient | None = None,
        bybit_client: BybitClient | None = None,
        spot_buyer: BybitSpotBuyer | None = None,
        state_store: StateStore | None = None,
        signal_emitter: SignalEmitter | None = None,
        source_emitter: SourceEventEmitter | None = None,
        cpp_ultra_engine: CppUltraListingEngineBridge | None = None,
        enable_trading: bool = True,
        defer_persistence: bool = False,
        prefer_cached_lookup: bool = False,
        latency_trace_enabled: bool = False,
        keep_warm_enabled: bool = False,
        keep_warm_interval_sec: int = 30,
        persist_source_events: bool = True,
        state_flush_interval_sec: float = 1.0,
        enable_bybit_warmup: bool = True,
        defer_post_trade_work: bool = False,
        hot_state_enabled: bool = False,
        emit_ultra_ack: bool = True,
    ):
        self.poll_interval = poll_interval
        self.config = self._load_config(config_file)
        self._channels_by_id = {
            channel["id"]: channel for channel in self.config["channels"]
        }
        self._channel_ids_by_handle = {
            channel["channel_handle"].lstrip("@"): channel["id"]
            for channel in self.config["channels"]
        }
        self._order_link_prefix_by_channel_id = {
            channel["id"]: f"ls-{self._exchange_code(channel['exchange'])}-"
            for channel in self.config["channels"]
        }
        self._channel_runtime_by_id = {
            channel["id"]: _ChannelRuntime(
                channel_id=channel["id"],
                channel_handle=channel["channel_handle"],
                exchange=channel["exchange"],
                display_name=channel["display_name"],
                order_link_prefix=self._order_link_prefix_by_channel_id[channel["id"]],
                classify_title=make_listing_title_classifier(
                    exchange=channel["exchange"],
                    display_name=channel["display_name"],
                ),
                classify_title_fast=make_listing_title_classifier(
                    exchange=channel["exchange"],
                    display_name=channel["display_name"],
                    minimal=True,
                ),
            )
            for channel in self.config["channels"]
        }
        self.channel_client = channel_client or TelegramChannelClient()
        self.bybit_client = bybit_client or BybitClient()
        self.spot_buyer = (
            spot_buyer
            if spot_buyer is not None
            else (
                BybitSpotBuyer(market_client=self.bybit_client)
                if enable_trading
                else None
            )
        )
        self.state_store = state_store or StateStore()
        self.signal_emitter = signal_emitter or SignalEmitter()
        self.source_emitter = source_emitter or SourceEventEmitter()
        self.cpp_ultra_engine = cpp_ultra_engine or CppUltraListingEngineBridge()
        self.enable_trading = enable_trading
        self.defer_persistence = defer_persistence
        self.prefer_cached_lookup = prefer_cached_lookup
        self.latency_trace_enabled = latency_trace_enabled
        self.keep_warm_enabled = keep_warm_enabled
        self.keep_warm_interval_sec = max(5, int(keep_warm_interval_sec))
        self.persist_source_events = persist_source_events
        self.state_flush_interval_sec = max(0.0, float(state_flush_interval_sec))
        self.enable_bybit_warmup = enable_bybit_warmup
        self.defer_post_trade_work = defer_post_trade_work
        self.hot_state_enabled = bool(hot_state_enabled and self.defer_persistence)
        self.emit_ultra_ack = bool(emit_ultra_ack)
        self._cpp_ultra_hot_path_enabled = (
            self.defer_post_trade_work
            and self.enable_trading
            and self.cpp_ultra_engine.is_enabled()
        )
        self._bg_executor = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="listing-sniper-bg")
            if self.defer_persistence or self.defer_post_trade_work
            else None
        )
        self._warm_stop = threading.Event()
        self._warm_thread: threading.Thread | None = None
        self._state_flush_stop = threading.Event()
        self._state_flush_thread: threading.Thread | None = None
        self._state_dirty_epoch = 0
        self._state_flushed_epoch = 0
        if self.hot_state_enabled:
            snapshot = self.state_store.snapshot_last_seen()
            self._hot_last_seen = {
                channel_id: int(snapshot.get(channel_id, 0))
                for channel_id in self._channels_by_id
            }
        else:
            self._hot_last_seen = {}
        refresh = getattr(self.bybit_client, "refresh_market_cache", None)
        if self.enable_bybit_warmup and callable(refresh):
            try:
                refresh()
            except Exception as exc:  # pragma: no cover - warmup safeguard
                logger.warning("Bybit 심볼 캐시 사전 로드 실패: %s", exc)
        if self.cpp_ultra_engine.is_enabled():
            try:
                self.cpp_ultra_engine.warmup()
            except Exception as exc:  # pragma: no cover - warmup safeguard
                logger.warning("C++ ultra engine warmup 실패: %s", exc)
        if self.defer_persistence and self.state_flush_interval_sec > 0:
            self._start_state_flush_thread()
        if self.enable_bybit_warmup and self.keep_warm_enabled:
            self._start_keep_warm_thread()
        self._process_post_impl = self._select_process_post_impl()

    def _load_config(self, config_file: Path | str) -> dict:
        with open(config_file, "r") as handle:
            return json.load(handle)

    def _get_channel(self, channel_id: str) -> dict | None:
        return self._channels_by_id.get(channel_id)

    def get_channel_handles(self, channel_id: str | None = None) -> list[str]:
        if channel_id is not None:
            channel = self._get_channel(channel_id)
            return [channel["channel_handle"]] if channel else []
        return [channel["channel_handle"] for channel in self.config["channels"]]

    def get_channel_id_by_handle(self, channel_handle: str) -> str | None:
        return self._channel_ids_by_handle.get(channel_handle.lstrip("@"))

    def process_post(self, channel_id: str, post: dict) -> dict | list[dict] | None:
        return self._process_post_impl(channel_id, post)

    def _select_process_post_impl(self):
        if (
            self.defer_post_trade_work
            and not self.emit_ultra_ack
            and not self.latency_trace_enabled
            and not self._cpp_ultra_hot_path_enabled
        ):
            return self._process_post_ultra_fire_fast
        return self._process_post_general

    def _process_post_general(self, channel_id: str, post: dict) -> dict | list[dict] | None:

        trace = (
            LatencyTrace(enabled=True)
            if self.latency_trace_enabled
            else NOOP_LATENCY_TRACE
        )
        channel = self._channel_runtime_by_id.get(channel_id)
        if channel is None:
            logger.error("거래소 설정 없음: %s", channel_id)
            return None

        message_id = int(post["message_id"])
        if self._cpp_ultra_hot_path_enabled and not self._has_multiple_tickers_fast(
            post.get("title", "")
        ):
            signal = self._process_post_cpp_ultra(
                channel_id=channel_id,
                channel=channel,
                post=post,
                message_id=message_id,
                trace=trace,
            )
            if signal is not None:
                return signal

        marked = self._mark_seen(channel_id, message_id)
        if not marked:
            return None
        trace.mark("dedup")

        if self.defer_persistence:
            self._mark_state_dirty()

        native_listing = post.get("native_listing")
        if native_listing is not None:
            listing = native_listing
            listing["exchange"] = channel.exchange
            listing["display_name"] = channel.display_name
            self._attach_post_assets_to_listing(post=post, listing=listing)
            trace.mark("classify_native")
        else:
            listing = channel.classify_title(post.get("title", ""))
            if listing is None:
                return None
            trace.mark("classify")

        listings = self._expand_listing_by_ticker(listing)
        trades = [
            self._maybe_buy_spot(channel=channel, post=post, listing=item)
            for item in listings
        ]
        trace.mark("trade")
        if self.defer_post_trade_work:
            for item, trade in zip(listings, trades):
                self._submit_background(
                    self._finalize_post_trade_work,
                    trace,
                    post,
                    item,
                    trade,
                )
            if not self.emit_ultra_ack:
                return None
            signals = [
                self._build_ultra_trade_ack(trace, post, item, trade)
                for item, trade in zip(listings, trades)
            ]
            return signals[0] if len(signals) == 1 else signals
        signals = []
        for item, trade in zip(listings, trades):
            self._log_trade_latency(post=post, listing=item, trade=trade)
            bybit = self._lookup_bybit_snapshot(item["ticker"])
            trace.mark("bybit_snapshot")
            initial_latency = self._build_latency_payload(trace, post, item, trade)
            signal = self.signal_emitter.build(
                post=post,
                listing=item,
                bybit=bybit,
                trade=trade,
                latency=initial_latency,
            )
            trace.mark("build_signal")
            final_latency = self._build_latency_payload(trace, post, item, trade)
            if final_latency is not None:
                signal["latency"] = final_latency
            if self.defer_persistence:
                self._submit_background(self.signal_emitter.persist, signal)
            else:
                self.signal_emitter.persist(signal)
            logger.info(
                "[%s] 상장 공지 감지: %s (%s)",
                channel_id,
                item["asset_name"],
                item["ticker"],
            )
            signals.append(signal)
        return signals[0] if len(signals) == 1 else signals

    def _process_post_ultra_fire_fast(self, channel_id: str, post: dict) -> dict | None:
        channel = self._channel_runtime_by_id.get(channel_id)
        if channel is None:
            logger.error("거래소 설정 없음: %s", channel_id)
            return None

        message_id = int(post["message_id"])
        marked = self._mark_seen(channel_id, message_id)
        if not marked:
            return None

        if self.defer_persistence:
            self._mark_state_dirty()

        native_listing = post.get("native_listing")
        if native_listing is not None:
            listing = native_listing
            listing["exchange"] = channel.exchange
            listing["display_name"] = channel.display_name
            self._attach_post_assets_to_listing(post=post, listing=listing)
        else:
            listing = channel.classify_title_fast(post.get("title", ""))
            if listing is None:
                return None

        listings = self._expand_listing_by_ticker(listing)
        for item in listings:
            trade = self._maybe_buy_spot(channel=channel, post=post, listing=item)
            self._submit_background(
                self._finalize_post_trade_work,
                NOOP_LATENCY_TRACE,
                post,
                item,
                trade,
            )
        return None

    def poll_exchange(self, channel_id: str) -> list[dict]:
        channel = self._get_channel(channel_id)
        if channel is None:
            logger.error("거래소 설정 없음: %s", channel_id)
            return []

        posts = self.channel_client.fetch_recent_posts(channel["channel_handle"])
        posts.sort(key=lambda post: post["message_id"])

        signals = []

        for post in posts:
            signal = self.process_post(channel_id, post)
            if signal is not None:
                if isinstance(signal, list):
                    signals.extend(signal)
                else:
                    signals.append(signal)

        return signals

    def _process_post_cpp_ultra(
        self,
        *,
        channel_id: str,
        channel: _ChannelRuntime,
        post: dict,
        message_id: int,
        trace: LatencyTrace,
    ) -> dict | None:
        if not self._would_mark_seen(channel_id, message_id):
            return None
        title = post.get("title", "")
        trade_started_ns = time.monotonic_ns()
        if self.emit_ultra_ack:
            result = self.cpp_ultra_engine.handle_post(
                exchange=channel.exchange,
                message_id=message_id,
                title=title,
            )
        else:
            raw_result = self.cpp_ultra_engine.handle_post_raw(
                exchange=channel.exchange,
                message_id=message_id,
                title=title,
            )
            result = None
        trade_finished_ns = time.monotonic_ns()
        trace.mark("cpp_ultra")
        if not self.emit_ultra_ack:
            if raw_result.duplicate or not raw_result.matched:
                return None
            self._remember_seen(channel_id, message_id)
            if self.defer_persistence:
                self._mark_state_dirty()
            self._submit_background(
                self._finalize_cpp_ultra_raw_post_trade_work,
                trace,
                post,
                channel,
                raw_result,
                trade_started_ns,
                trade_finished_ns,
            )
            return None
        if result is None or result.get("duplicate"):
            return None
        self._remember_seen(channel_id, message_id)
        if self.defer_persistence:
            self._mark_state_dirty()
        listing = {
            "exchange": channel.exchange,
            "display_name": channel.display_name,
            "signal_type": result["signal_type"],
            "ticker": result["ticker"],
            "asset_name": result["asset_name"],
            "markets": result["markets"],
        }
        trade = result["trade"]
        trade.setdefault("trade_started_monotonic_ns", int(trade_started_ns))
        trade["trade_finished_monotonic_ns"] = int(trade_finished_ns)
        trade_elapsed_ns = max(0, trade_finished_ns - trade_started_ns)
        trade["trade_elapsed_ns"] = int(trade_elapsed_ns)
        trade["trade_elapsed_us"] = trade_elapsed_ns / 1_000.0
        trade["trade_elapsed_ms"] = trade_elapsed_ns / 1_000_000.0
        signal = self._build_ultra_trade_ack(trace, post, listing, trade)
        self._submit_background(
            self._finalize_post_trade_work,
            trace,
            post,
            listing,
            trade,
        )
        return signal

    def _finalize_cpp_ultra_raw_post_trade_work(
        self,
        trace: LatencyTrace,
        post: dict,
        channel: _ChannelRuntime,
        raw_result,
        trade_started_ns: int,
        trade_finished_ns: int,
    ):
        result = self.cpp_ultra_engine.payload_from_raw(raw_result)
        if result is None or result.get("duplicate"):
            return
        listing = {
            "exchange": channel.exchange,
            "display_name": channel.display_name,
            "signal_type": result["signal_type"],
            "ticker": result["ticker"],
            "asset_name": result["asset_name"],
            "markets": result["markets"],
        }
        trade = result["trade"]
        trade.setdefault("trade_started_monotonic_ns", int(trade_started_ns))
        trade["trade_finished_monotonic_ns"] = int(trade_finished_ns)
        trade_elapsed_ns = max(0, trade_finished_ns - trade_started_ns)
        trade["trade_elapsed_ns"] = int(trade_elapsed_ns)
        trade["trade_elapsed_us"] = trade_elapsed_ns / 1_000.0
        trade["trade_elapsed_ms"] = trade_elapsed_ns / 1_000_000.0
        self._finalize_post_trade_work(trace, post, listing, trade)

    def poll_all(self) -> list[dict]:
        signals = []
        for channel in self.config["channels"]:
            try:
                signals.extend(self.poll_exchange(channel["id"]))
            except Exception as exc:
                logger.error("[%s] 폴링 중 오류: %s", channel["id"], exc, exc_info=True)
        return signals

    def run(self, on_signals: Callable[[list[dict]], None] | None = None):
        logger.info(
            "상장 공지 모니터 시작 — %d개 채널, %d초 간격",
            len(self.config["channels"]),
            self.poll_interval,
        )
        try:
            while True:
                logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 폴링 시작 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                signals = self.poll_all()
                if signals:
                    logger.info("이번 폴링 결과: %d건 신규 시그널", len(signals))
                    if on_signals is not None:
                        on_signals(signals)
                else:
                    logger.info("이번 폴링 결과: 신규 시그널 없음")
                logger.info("다음 폴링까지 %d초 대기...", self.poll_interval)
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("사용자 중단. 종료.")

    def close(self):
        self._warm_stop.set()
        if self._warm_thread is not None:
            self._warm_thread.join(timeout=2)
        self._state_flush_stop.set()
        if self._state_flush_thread is not None:
            self._state_flush_thread.join(timeout=2)
        if self.defer_persistence:
            self._flush_state_if_dirty()
        bybit_close = getattr(self.bybit_client, "close", None)
        if callable(bybit_close):
            bybit_close()
        buyer_close = getattr(self.spot_buyer, "close", None)
        if callable(buyer_close):
            buyer_close()
        if self._bg_executor is not None:
            self._bg_executor.shutdown(wait=True)
        return None

    @staticmethod
    def _has_multiple_tickers_fast(title: str) -> bool:
        return has_multiple_listing_assets_fast(title)

    @staticmethod
    def _attach_post_assets_to_listing(*, post: dict, listing: dict):
        assets = extract_listing_assets(post.get("title", ""))
        if not assets:
            return
        tickers = [asset["ticker"] for asset in assets]
        listing["assets"] = assets
        listing["tickers"] = tickers
        listing.setdefault("ticker", tickers[0])
        listing.setdefault("asset_name", assets[0]["asset_name"])

    @staticmethod
    def _asset_name_for_ticker(listing: dict, ticker: str) -> str | None:
        for asset in listing.get("assets") or []:
            if asset.get("ticker") == ticker:
                return asset.get("asset_name")
        if listing.get("ticker") == ticker:
            return listing.get("asset_name")
        return None

    def _expand_listing_by_ticker(self, listing: dict) -> list[dict]:
        tickers = [
            str(ticker)
            for ticker in (listing.get("tickers") or [listing.get("ticker")])
            if ticker
        ]
        if not tickers:
            return [listing]
        if len(tickers) == 1 and tickers[0] == listing.get("ticker"):
            return [listing]
        expanded: list[dict] = []
        total = len(tickers)
        for index, ticker in enumerate(tickers, start=1):
            item = dict(listing)
            item["ticker"] = ticker
            item["tickers"] = tickers
            item["multi_ticker_count"] = total
            item["multi_ticker_index"] = index
            asset_name = self._asset_name_for_ticker(listing, ticker)
            if asset_name:
                item["asset_name"] = asset_name
            expanded.append(item)
        return expanded

    def _maybe_buy_spot(self, *, channel: _ChannelRuntime, post: dict, listing: dict) -> dict:
        if not self.enable_trading:
            return {
                "enabled": False,
                "attempted": False,
                "executed": False,
                "reason": "cli_disabled",
            }

        order_link_id = self._make_order_link_id(
            prefix=channel.order_link_prefix,
            message_id=int(post["message_id"]),
            ticker=listing["ticker"],
        )
        trade = self.spot_buyer.buy_market(
            ticker=listing["ticker"],
            order_link_id=order_link_id,
        )
        return trade

    def _lookup_bybit_snapshot(self, ticker: str) -> dict:
        if self.prefer_cached_lookup:
            return self.bybit_client.lookup_ticker_cached(ticker)
        return self.bybit_client.lookup_ticker(ticker)

    def _build_ultra_trade_ack(
        self,
        trace: LatencyTrace,
        post: dict,
        listing: dict,
        trade: dict,
    ) -> dict:
        signal = {
            "exchange": listing["exchange"],
            "exchange_name": listing["display_name"],
            "signal_type": listing["signal_type"],
            "ticker": listing["ticker"],
            "asset_name": listing["asset_name"],
            "markets": listing["markets"],
            "channel_handle": post["channel_handle"],
            "message_id": post["message_id"],
            "title": post.get("title", ""),
            "text": post.get("text", post.get("title", "")),
            "post_url": post.get(
                "post_url",
                f"https://t.me/{post['channel_handle']}/{post['message_id']}",
            ),
            "published_at": self._format_post_timestamp(post["published_at"]),
            "trade": trade,
            "ultra_deferred": True,
        }
        latency = self._build_latency_payload(trace, post, listing, trade)
        if latency is not None:
            signal["latency"] = latency
        return signal

    @staticmethod
    def _format_post_timestamp(value) -> str:
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def _finalize_post_trade_work(
        self,
        trace: LatencyTrace,
        post: dict,
        listing: dict,
        trade: dict,
    ):
        listing = self._enrich_listing_if_needed(post=post, listing=listing)
        self._log_trade_result(listing=listing, trade=trade)
        self._log_trade_latency(post=post, listing=listing, trade=trade)
        trace.mark("deferred_finalize")
        bybit = self._lookup_bybit_snapshot(listing["ticker"])
        trace.mark("bybit_snapshot")
        initial_latency = self._build_latency_payload(trace, post, listing, trade)
        signal = self.signal_emitter.build(
            post=post,
            listing=listing,
            bybit=bybit,
            trade=trade,
            latency=initial_latency,
        )
        trace.mark("build_signal")
        final_latency = self._build_latency_payload(trace, post, listing, trade)
        if final_latency is not None:
            signal["latency"] = final_latency
        self.signal_emitter.persist(signal)
        logger.info(
            "[%s] 상장 공지 감지: %s (%s)",
            listing["exchange"],
            listing["asset_name"],
            listing["ticker"],
        )

    def _enrich_listing_if_needed(self, *, post: dict, listing: dict) -> dict:
        if "asset_name" in listing and "markets" in listing:
            return listing
        channel = self._channel_runtime_by_id.get(listing["exchange"])
        if channel is None:
            channel_id = self.get_channel_id_by_handle(post.get("channel_handle", ""))
            if channel_id is not None:
                channel = self._channel_runtime_by_id.get(channel_id)
        if channel is None:
            return listing
        enriched = channel.classify_title(post.get("title", ""))
        if enriched is None:
            return listing
        ticker = listing["ticker"]
        asset_name = self._asset_name_for_ticker(enriched, ticker) or enriched.get("asset_name")
        enriched.update(
            {
                "exchange": listing["exchange"],
                "display_name": listing["display_name"],
                "signal_type": listing["signal_type"],
                "ticker": ticker,
            }
        )
        if asset_name:
            enriched["asset_name"] = asset_name
        return enriched

    def _build_latency_payload(
        self,
        trace: LatencyTrace,
        post: dict,
        listing: dict,
        trade: dict,
    ) -> dict | None:
        payload = trace.as_dict()
        if not payload:
            return None
        payload["message_id"] = int(post["message_id"])
        payload["ticker"] = listing["ticker"]
        payload["trade_attempted"] = bool(trade.get("attempted"))
        payload["trade_executed"] = bool(trade.get("executed"))
        if trade.get("transport"):
            payload["trade_transport"] = trade["transport"]
        if trade.get("trade_elapsed_ns") is not None:
            payload["trade_elapsed_ns"] = int(trade["trade_elapsed_ns"])
            payload["trade_elapsed_ms"] = float(trade.get("trade_elapsed_ms", 0.0))
        received_monotonic_ns = post.get("received_monotonic_ns")
        if received_monotonic_ns is not None:
            received_monotonic_ns = int(received_monotonic_ns)
            payload["received_monotonic_ns"] = received_monotonic_ns
            start_ns = trace.start_ns()
            end_ns = trace.last_ns()
            if start_ns is not None:
                payload["receive_to_trace_start_ns"] = max(0, start_ns - received_monotonic_ns)
            if end_ns is not None:
                receive_to_signal_ns = max(0, end_ns - received_monotonic_ns)
                payload["receive_to_signal_ns"] = receive_to_signal_ns
                payload["receive_to_signal_ms"] = receive_to_signal_ns / 1_000_000.0
            trade_finished_ns = trade.get("trade_finished_monotonic_ns")
            if trade_finished_ns is not None:
                receive_to_trade_ns = max(0, int(trade_finished_ns) - received_monotonic_ns)
                payload["receive_to_trade_finished_ns"] = receive_to_trade_ns
                payload["receive_to_trade_finished_ms"] = receive_to_trade_ns / 1_000_000.0
        return payload

    @staticmethod
    def _log_trade_result(listing: dict, trade: dict):
        if trade.get("executed"):
            logger.info(
                "[%s] Bybit spot 매수 성공: %s order_id=%s",
                listing["exchange"],
                trade.get("symbol"),
                trade.get("order_id", ""),
            )
        elif trade.get("attempted"):
            logger.warning(
                "[%s] Bybit spot 매수 실패: %s (%s)",
                listing["exchange"],
                trade.get("symbol"),
                trade.get("reason", "unknown"),
            )

    @staticmethod
    def _log_trade_latency(post: dict, listing: dict, trade: dict):
        if not trade.get("attempted"):
            return
        received_monotonic_ns = post.get("received_monotonic_ns")
        trade_finished_ns = trade.get("trade_finished_monotonic_ns")
        if received_monotonic_ns is None or trade_finished_ns is None:
            return
        receive_to_trade_ns = max(0, int(trade_finished_ns) - int(received_monotonic_ns))
        logger.info(
            "[%s] 발견→주문완료 %.3fms transport=%s executed=%s symbol=%s",
            listing["exchange"],
            receive_to_trade_ns / 1_000_000.0,
            trade.get("transport", "python_rest"),
            bool(trade.get("executed")),
            trade.get("symbol", ""),
        )

    def process_source_post(self, channel_id: str, post: dict) -> dict | None:
        trace = (
            LatencyTrace(enabled=True)
            if self.latency_trace_enabled
            else NOOP_LATENCY_TRACE
        )
        channel = self._channel_runtime_by_id.get(channel_id)
        if channel is None:
            logger.error("거래소 설정 없음: %s", channel_id)
            return None

        message_id = int(post["message_id"])
        marked = self._mark_seen(channel_id, message_id)
        if not marked:
            return None
        trace.mark("dedup")

        if self.defer_persistence:
            self._mark_state_dirty()

        event: dict | None = None
        if self.persist_source_events:
            event = self.source_emitter.build(
                channel={
                    "id": channel.channel_id,
                    "exchange": channel.exchange,
                    "display_name": channel.display_name,
                    "channel_handle": channel.channel_handle,
                },
                post=post,
                latency=self._build_source_latency_payload(trace, post, channel),
            )
            trace.mark("build_source_event")
            final_latency = self._build_source_latency_payload(trace, post, channel)
            if final_latency is not None:
                event["latency"] = final_latency
            if self.defer_persistence:
                self._submit_background(self.source_emitter.persist, event)
            else:
                self.source_emitter.persist(event)
            return event

        return self._build_source_ack(trace, post, channel)

    def _build_source_latency_payload(
        self,
        trace: LatencyTrace,
        post: dict,
        channel: _ChannelRuntime,
    ) -> dict | None:
        payload = trace.as_dict()
        if not payload:
            return None
        payload["message_id"] = int(post["message_id"])
        payload["channel_id"] = channel.channel_id
        payload["source_only"] = True
        return payload

    def _build_source_ack(
        self,
        trace: LatencyTrace,
        post: dict,
        channel: _ChannelRuntime,
    ) -> dict:
        event = {
            "event_type": "telegram_source_post",
            "channel_id": channel.channel_id,
            "exchange": channel.exchange,
            "message_id": int(post["message_id"]),
        }
        received_monotonic_ns = post.get("received_monotonic_ns")
        if received_monotonic_ns is not None:
            event["received_monotonic_ns"] = int(received_monotonic_ns)
        latency = self._build_source_latency_payload(trace, post, channel)
        if latency is not None:
            event["latency"] = latency
        return event

    def _start_keep_warm_thread(self):
        if self._warm_thread is not None:
            return
        self._warm_thread = threading.Thread(
            target=self._keep_warm_loop,
            name="listing-sniper-warm",
            daemon=True,
        )
        self._warm_thread.start()

    def _keep_warm_loop(self):
        logger.info(
            "저지연 keep-warm 시작 (interval=%ss)",
            self.keep_warm_interval_sec,
        )
        while not self._warm_stop.wait(self.keep_warm_interval_sec):
            self._run_keep_warm_once()

    def _start_state_flush_thread(self):
        if self._state_flush_thread is not None:
            return
        self._state_flush_thread = threading.Thread(
            target=self._state_flush_loop,
            name="listing-sniper-state-flush",
            daemon=True,
        )
        self._state_flush_thread.start()

    def _state_flush_loop(self):
        while not self._state_flush_stop.wait(self.state_flush_interval_sec):
            self._flush_state_if_dirty()

    def _run_keep_warm_once(self):
        if self.cpp_ultra_engine.is_enabled():
            try:
                self.cpp_ultra_engine.warmup()
            except Exception as exc:  # pragma: no cover - keep-warm safeguard
                logger.warning("C++ ultra engine keep-warm 실패: %s", exc)

        warmup = getattr(self.spot_buyer, "warmup", None)
        if callable(warmup):
            try:
                warmup(force_refresh_market_cache=True)
                return
            except Exception as exc:  # pragma: no cover - keep-warm safeguard
                logger.warning("저지연 warmup 실패: %s", exc)

        refresh = getattr(self.bybit_client, "refresh_market_cache", None)
        if callable(refresh):
            try:
                refresh(force=True)
            except Exception as exc:  # pragma: no cover - keep-warm safeguard
                logger.warning("Bybit 심볼 캐시 keep-warm 실패: %s", exc)

    def _submit_background(self, fn, *args):
        if self._bg_executor is None:
            fn(*args)
            return
        self._bg_executor.submit(self._run_background_task, fn, *args)

    def reset_state(self):
        self.state_store.clear()
        if self.hot_state_enabled:
            self._hot_last_seen = {
                channel_id: 0 for channel_id in self._channels_by_id
            }
        self._state_dirty_epoch = 0
        self._state_flushed_epoch = 0

    def _mark_seen(self, channel_id: str, message_id: int) -> bool:
        if not self.hot_state_enabled:
            return self.state_store.mark_seen(
                channel_id,
                message_id,
                persist=not self.defer_persistence,
            )

        last_seen = int(self._hot_last_seen.get(channel_id, 0))
        if message_id <= last_seen:
            return False
        self._hot_last_seen[channel_id] = int(message_id)
        return True

    def _would_mark_seen(self, channel_id: str, message_id: int) -> bool:
        if not self.hot_state_enabled:
            state = self.state_store.snapshot_last_seen()
            return int(message_id) > int(state.get(channel_id, 0))
        return int(message_id) > int(self._hot_last_seen.get(channel_id, 0))

    def _remember_seen(self, channel_id: str, message_id: int):
        if not self.hot_state_enabled:
            self.state_store.mark_seen(
                channel_id,
                message_id,
                persist=not self.defer_persistence,
            )
            return
        self._hot_last_seen[channel_id] = int(message_id)

    def _mark_state_dirty(self):
        self._state_dirty_epoch += 1

    def _flush_state_if_dirty(self):
        target_epoch = self._state_dirty_epoch
        if target_epoch == self._state_flushed_epoch:
            return
        if self.hot_state_enabled:
            self.state_store.replace_last_seen_snapshot(self._hot_last_seen, persist=True)
        else:
            self.state_store.flush()
        self._state_flushed_epoch = target_epoch

    @staticmethod
    def _run_background_task(fn, *args):
        try:
            fn(*args)
        except Exception as exc:  # pragma: no cover - background safeguard
            logger.error("백그라운드 작업 실패: %s", exc, exc_info=True)

    # Bybit V5 caps orderLinkId at 36 chars; the C++ ultra engine truncates to
    # the same bound (see cpp/listing_ultra_engine.cpp). Keep these identical so a
    # repeated (exchange, message_id, ticker) yields the same orderLinkId on both
    # paths and Bybit dedups a double-fire.
    ORDER_LINK_ID_MAX_LEN = 36

    @staticmethod
    def _exchange_code(exchange: str) -> str:
        # Must match the C++ ultra engine, which embeds the full exchange name
        # (`ls-<exchange>-<message_id>-<ticker>`); a 1-letter abbreviation here
        # would make the two engines' orderLinkIds diverge and defeat dedup.
        return exchange

    def _make_order_link_id(self, *, prefix: str, message_id: int, ticker: str) -> str:
        return f"{prefix}{message_id}-{ticker}"[: self.ORDER_LINK_ID_MAX_LEN]
