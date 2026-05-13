#!/usr/bin/env python3
from __future__ import annotations

"""
02. Exchange Listing Sniper - 메인 엔트리포인트.

사용법:
  python main.py                 # 단일 HTML 폴링
  python main.py --loop          # 반복 감시 (실시간 세션이 있으면 realtime 우선)
  python main.py --exchange upbit
  python main.py --test-telegram
  python main.py --no-trade
  python main.py --realtime
  python main.py --login-source-telegram
"""

import argparse
import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from src.poller import ExchangeListingPoller
from src.race_realtime_client import RaceRealtimeChannelClient
from src.tdlib_realtime_client import TdlibRealtimeChannelClient
from src.telegram_notifier import ExchangeListingTelegramNotifier
from src.telegram_realtime_client import RealtimeTelegramChannelClient


class AsyncSignalNotifier:
    """Offload Telegram sends so the hot path can return immediately."""

    def __init__(self, notifier: ExchangeListingTelegramNotifier | None):
        self.notifier = notifier
        self._executor = (
            ThreadPoolExecutor(max_workers=1, thread_name_prefix="listing-telegram")
            if notifier is not None
            else None
        )

    def dispatch(self, signals: list[dict]):
        if self.notifier is None or not signals:
            return
        payload = list(signals)
        if self._executor is None:
            self.notifier.send_signals(payload)
            return
        self._executor.submit(self._send_safe, payload)

    def close(self):
        if self._executor is not None:
            self._executor.shutdown(wait=True)

    def _send_safe(self, signals: list[dict]):
        try:
            self.notifier.send_signals(signals)
        except Exception:
            logging.getLogger(__name__).exception("텔레그램 알림 전송 실패")


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")
    if not verbose:
        for name in (
            "httpx",
            "httpcore",
            "telethon.network",
            "pyrogram",
            "urllib3",
        ):
            logging.getLogger(name).setLevel(logging.WARNING)


def dispatch_signals_to_telegram(
    notifier: AsyncSignalNotifier,
    signals: list[dict],
):
    notifier.dispatch(signals)


def main():
    parser = argparse.ArgumentParser(
        description="거래소 상장 공지 텔레그램 감시 모니터"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="반복 감시 모드"
    )
    parser.add_argument(
        "--interval", type=int, default=15,
        help="HTML 폴링 간격 (초, 기본: 15)"
    )
    parser.add_argument(
        "--exchange", type=str, default=None,
        help="특정 거래소만 감시 (예: upbit, bithumb)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="디버그 로그 출력"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="감지 상태 초기화 후 실행"
    )
    parser.add_argument(
        "--test-telegram", action="store_true",
        help="02 전용 텔레그램 테스트 메시지 전송"
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="텔레그램 전송 없이 콘솔/파일 출력만 수행"
    )
    parser.add_argument(
        "--no-trade", action="store_true",
        help="Bybit 자동매수를 비활성화하고 감지만 수행"
    )
    parser.add_argument(
        "--source-only", action="store_true",
        help="텔레그램 소스 수신만 최우선 처리하고 분류/매수는 생략"
    )
    parser.add_argument(
        "--persist-source-events", action="store_true",
        help="source-only 모드에서 raw source 이벤트를 비동기 저장"
    )
    parser.add_argument(
        "--realtime", action="store_true",
        help="MTProto 기반 실시간 텔레그램 수신"
    )
    parser.add_argument(
        "--realtime-backend",
        choices=("telethon", "tdlib", "pyrogram", "race"),
        default="race",
        help="실시간 텔레그램 수신 백엔드 선택 (기본: race)"
    )
    parser.add_argument(
        "--login-source-telegram", action="store_true",
        help="실시간 수신용 텔레그램 유저 세션 로그인"
    )
    parser.add_argument(
        "--strict-realtime", action="store_true",
        help="실시간 세션이 없거나 realtime 경로를 못 쓰면 즉시 실패"
    )
    parser.add_argument(
        "--keep-warm-interval", type=int, default=30,
        help="저지연 keep-warm 주기 (초, 기본: 30)"
    )
    parser.add_argument(
        "--latency-trace", action="store_true",
        help="실시간 경로 단계별 latency trace를 남김"
    )
    parser.add_argument(
        "--state-flush-interval", type=float, default=1.0,
        help="deferred state flush 최소 간격 (초, 기본: 1.0)"
    )
    parser.add_argument(
        "--memory-state", action="store_true",
        help="dedup/state를 핫패스 메모리 last-seen 맵으로 처리하고 flush만 뒤로 미룸"
    )
    parser.add_argument(
        "--ultra-buy", action="store_true",
        help="핫패스를 감지->매수까지만 남기고 후속 작업은 백그라운드로 미룸"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    notifier = None if args.no_telegram else ExchangeListingTelegramNotifier()
    if args.realtime_backend == "race":
        realtime_client = RaceRealtimeChannelClient()
    elif args.realtime_backend == "tdlib":
        realtime_client = TdlibRealtimeChannelClient()
    elif args.realtime_backend == "pyrogram":
        from src.pyrogram_realtime_client import PyrogramRealtimeChannelClient

        realtime_client = PyrogramRealtimeChannelClient()
    else:
        realtime_client = RealtimeTelegramChannelClient()
    realtime_mode = args.realtime or (args.loop and realtime_client.is_configured())

    if (args.realtime or args.login_source_telegram) and not realtime_client.is_configured():
        raise RuntimeError(
            "실시간 텔레그램 소스 설정이 없습니다. "
            "BotFather 토큰이 아니라 LISTING_SOURCE_TELEGRAM_API_ID, "
            "LISTING_SOURCE_TELEGRAM_API_HASH, LISTING_SOURCE_TELEGRAM_PHONE 을 채워야 합니다."
        )

    if args.test_telegram:
        ok = notifier.send_test_message() if notifier else False
        print("Test message sent!" if ok else "Failed to send test message.")
        return

    poller = ExchangeListingPoller(
        poll_interval=args.interval,
        enable_trading=(not args.no_trade) and (not args.source_only),
        defer_persistence=realtime_mode,
        prefer_cached_lookup=realtime_mode,
        latency_trace_enabled=args.latency_trace,
        keep_warm_enabled=realtime_mode and (not args.source_only) and (not args.no_trade),
        keep_warm_interval_sec=args.keep_warm_interval,
        persist_source_events=args.persist_source_events,
        state_flush_interval_sec=args.state_flush_interval,
        enable_bybit_warmup=(not args.source_only) and (not args.no_trade),
        defer_post_trade_work=(
            realtime_mode
            and args.ultra_buy
            and (not args.no_trade)
            and (not args.source_only)
        ),
        emit_ultra_ack=not (
            realtime_mode
            and args.ultra_buy
            and args.no_telegram
            and (not args.source_only)
        ),
        hot_state_enabled=(
            realtime_mode
            and (
                args.memory_state
                or args.ultra_buy
                or args.source_only
            )
        ),
    )
    notifier_dispatcher = AsyncSignalNotifier(notifier)

    try:
        if args.login_source_telegram:
            ok = asyncio.run(realtime_client.login_interactive())
            print(
                "Realtime Telegram login complete!"
                if ok
                else "Realtime Telegram login failed."
            )
            return

        if args.reset:
            logger.info("감지 상태 초기화")
            poller.reset_state()

        if args.strict_realtime and not realtime_mode:
            raise RuntimeError(
                "strict realtime 모드인데 realtime 경로를 사용할 수 없습니다. "
                "LISTING_SOURCE_TELEGRAM_* 설정과 세션 파일을 확인하세요."
            )

        if realtime_mode:
            if args.strict_realtime and not realtime_client.has_session_file():
                raise RuntimeError(
                    "strict realtime 모드인데 텔레그램 세션 파일이 없습니다. "
                    "먼저 `python main.py --login-source-telegram` 을 실행하세요."
                )
            channel_handles = poller.get_channel_handles(args.exchange)
            if not channel_handles:
                print("실시간 감시 대상 채널이 없습니다.")
                return

            logger.info(
                "실시간 텔레그램 모드 시작 (%s, backend=%s)",
                ", ".join(channel_handles),
                args.realtime_backend,
            )
            if args.ultra_buy and not args.source_only:
                logger.info("ultra-buy 활성: 주문 이후 작업은 백그라운드로 이관")
            if args.memory_state or args.ultra_buy or args.source_only:
                logger.info("memory-state 활성: dedup/state는 메모리 우선 flush")

            def _on_post(post: dict):
                channel_id = poller.get_channel_id_by_handle(post["channel_handle"])
                if channel_id is None:
                    logger.warning("알 수 없는 채널 핸들: %s", post["channel_handle"])
                    return
                if args.source_only:
                    poller.process_source_post(channel_id, post)
                    return

                signal = poller.process_post(channel_id, post)
                if signal is not None and not args.source_only and not args.ultra_buy:
                    signals = signal if isinstance(signal, list) else [signal]
                    dispatch_signals_to_telegram(notifier_dispatcher, signals)

            asyncio.run(
                realtime_client.run(
                    channel_handles=channel_handles,
                    on_post=_on_post,
                    minimal_post=args.source_only and not args.persist_source_events,
                    trade_post=args.ultra_buy and not args.source_only,
                )
            )
            return
        if args.exchange:
            logger.info("단일 거래소 폴링: %s", args.exchange)
            signals = poller.poll_exchange(args.exchange)
            if not args.ultra_buy:
                dispatch_signals_to_telegram(notifier_dispatcher, signals)
            if not signals:
                print(f"\n[{args.exchange}] 신규 상장 시그널 없음")
            return
        if args.loop:
            poller.run(
                on_signals=(
                    None
                    if args.ultra_buy
                    else lambda signals: dispatch_signals_to_telegram(
                        notifier_dispatcher,
                        signals,
                    )
                )
            )
            return

        logger.info("전체 거래소 단일 폴링 시작")
        signals = poller.poll_all()
        if not args.ultra_buy:
            dispatch_signals_to_telegram(notifier_dispatcher, signals)
        if not signals:
            print("\n신규 상장 시그널 없음")
        else:
            print(f"\n총 {len(signals)}건 시그널 감지")
    finally:
        notifier_dispatcher.close()
        poller.close()


if __name__ == "__main__":
    main()
