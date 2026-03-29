#!/usr/bin/env python3
"""
01. 거버넌스 프로포절 모니터 — 메인 엔트리포인트.

사용법:
  python main.py              # 단일 폴링 (1회 실행)
  python main.py --loop       # 10분 간격 반복 폴링
  python main.py --loop --interval 300  # 5분 간격
  python main.py --chain cosmoshub  # 특정 체인만
"""

import argparse
import logging
import sys
from pathlib import Path

# 모듈 임포트를 위한 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.poller import GovernancePoller


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%d %H:%M:%S")
    # httpx 로그 줄이기
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


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
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    poller = GovernancePoller(poll_interval=args.interval)

    if args.reset:
        logger.info("감지 상태 초기화")
        poller.state_store.clear()

    if args.chain:
        # 특정 체인만
        logger.info("단일 체인 폴링: %s", args.chain)
        signals = poller.poll_chain(args.chain)
        if not signals:
            print(f"\n[{args.chain}] 신규 업그레이드 시그널 없음")
    elif args.loop:
        # 반복 폴링 (run() 내부에서 close 처리)
        poller.run()
        return
    else:
        # 단일 실행
        logger.info("전체 체인 단일 폴링 시작")
        signals = poller.poll_all()
        if not signals:
            print("\n신규 업그레이드 시그널 없음")
        else:
            print(f"\n총 {len(signals)}건 시그널 감지")

    poller.close()


if __name__ == "__main__":
    main()
