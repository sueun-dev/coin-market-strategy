#!/usr/bin/env python3
from __future__ import annotations

"""
01. 거버넌스 프로포절 모니터 — 메인 엔트리포인트.

사용법:
  python main.py              # 단일 폴링 (1회 실행)
  python main.py --loop       # 10분 간격 반복 폴링
  python main.py --loop --interval 300  # 5분 간격
  python main.py --chain cosmoshub  # 특정 체인만
  python main.py --test-telegram    # 01 전용 텔레그램 연결 테스트
"""

import argparse
import logging
import sys
from pathlib import Path

# 모듈 임포트를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.poller import GovernancePoller
from src.telegram_notifier import GovernanceTelegramNotifier


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")
    # httpx 로그 줄이기
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def send_signals_to_telegram(
    notifier: GovernanceTelegramNotifier | None,
    signals: list[dict],
):
    if notifier is None or not signals:
        return
    notifier.send_signals(signals)


def main():
    parser = argparse.ArgumentParser(
        description="거버넌스 프로포절 모니터 — 입출금 정지 사전 감지"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="반복 폴링 모드 (기본: 단일 실행)"
    )
    parser.add_argument(
        "--interval", type=int, default=600,
        help="폴링 간격 (초, 기본: 600)"
    )
    parser.add_argument(
        "--chain", type=str, default=None,
        help="특정 체인만 폴링 (예: cosmoshub)"
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
        help="01 전용 텔레그램 테스트 메시지 전송"
    )
    parser.add_argument(
        "--no-telegram", action="store_true",
        help="텔레그램 전송 없이 콘솔/파일 출력만 수행"
    )
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    notifier = None if args.no_telegram else GovernanceTelegramNotifier()

    if args.test_telegram:
        ok = notifier.send_test_message() if notifier else False
        print("Test message sent!" if ok else "Failed to send test message.")
        return

    poller = GovernancePoller(poll_interval=args.interval)

    if args.reset:
        logger.info("감지 상태 초기화")
        poller.state_store.clear()

    if args.chain:
        # 특정 체인만
        logger.info("단일 체인 폴링: %s", args.chain)
        signals = poller.poll_chain(args.chain)
        send_signals_to_telegram(notifier, signals)
        if not signals:
            print(f"\n[{args.chain}] 신규 업그레이드 시그널 없음")
    elif args.loop:
        # 반복 폴링 (run() 내부에서 close 처리)
        poller.run(on_signals=lambda signals: send_signals_to_telegram(notifier, signals))
        return
    else:
        # 단일 실행
        logger.info("전체 체인 단일 폴링 시작")
        signals = poller.poll_all()
        send_signals_to_telegram(notifier, signals)
        if not signals:
            print("\n신규 업그레이드 시그널 없음")
        else:
            print(f"\n총 {len(signals)}건 시그널 감지")

    poller.close()


if __name__ == "__main__":
    main()
