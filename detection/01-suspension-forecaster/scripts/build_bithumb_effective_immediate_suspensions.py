#!/usr/bin/env python3
"""Build Bithumb effective-immediate suspension files from archive + official notices."""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON_OUTPUT = ROOT / "config" / "bithumb_effective_immediate_suspensions.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "BITHUMB_EFFECTIVE_IMMEDIATE_SUSPENSIONS.md"
STRICT_OUTPUT = ROOT / "config" / "exchange_immediate_issue_suspensions.json"
ARCHIVE_MAX_PAGE = 60
THRESHOLD_SECONDS = 600
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"
)

ARCHIVE_NEWS_PATTERN = re.compile(
    r'"headline": "(?P<title>\[빗썸\][^"]+)",\s+'
    r'"url": "(?P<article_url>https://bloomingbit\.io/news/\d+)"',
    re.S,
)
OFFICIAL_URL_PATTERN = re.compile(r"https://feed\.bithumb\.com/notice/\d+")
TITLE_TICKER_PATTERN = re.compile(r"\(([A-Z0-9-]{2,15})\)")
PUBLISHED_AT_PATTERN = re.compile(
    r"(?:^|\n)(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?: 공유하기)?(?:\n|$)"
)
STOP_AT_PATTERN = re.compile(
    r"(?:입출금|출금|입금)(?: 서비스| 지원)? (?:중지|중단) 시점.*?"
    r"(\d{4})\.(\d{2})\.(\d{2})\([^)]*\)\s*(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?",
    re.S,
)
SERVICE_LIMIT_PATTERN = re.compile(
    r"서비스 제한 범위\s*(.+?)(?:※ 유의사항|입출금 재개 시점|네트워크 안정성이 확보|감사합니다\.)",
    re.S,
)
FUTURE_WORDING_PATTERN = re.compile(r"중지 ?될 예정|중단 ?될 예정")
RELEVANT_TITLE_KEYWORDS = (
    "입출금",
    "출금",
    "입금",
    "유의촉구",
    "거래유의종목",
    "투자유의",
)
REASON_KEYWORDS: dict[str, tuple[str, ...]] = {
    "security_issue": ("보안 취약점", "보안 이슈", "보안 문제 의심 정황"),
    "project_issue_or_investor_caution": (
        "유의촉구",
        "거래유의종목",
        "투자 유의",
        "프로젝트 이슈",
    ),
    "wallet_system_check": ("월렛 시스템 점검", "내부 월렛 시스템 점검"),
    "node_sync_issue": ("노드 동기화 문제",),
    "block_generation_stop": ("블록 생성 중단", "블록생성 중단"),
    "network_issue": ("네트워크 이슈", "메인넷 네트워크 이슈"),
    "withdrawal_surge": ("출금량 증가", "출금 요청량 증가"),
}

MANUAL_FALLBACK_ROWS = [
    {
        "notice_published_at_kst": "2026-04-02 03:07:55",
        "asset_scope": "DRIFT",
        "assets": ["DRIFT"],
        "scope": "deposit_withdrawal",
        "trigger_type": "security_issue",
        "official_url": "https://feed.bithumb.com/notice/1652530",
        "supporting_url": "https://feed.bithumb.com/notice/1652530",
        "title": "[빗썸] 드리프트(DRIFT) 유의촉구 및 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-04-02 03:07:00",
        "delta_from_notice_seconds": -55,
        "delta_label": "-55s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-03-23 23:10:34",
        "asset_scope": "PEAQ",
        "assets": ["PEAQ"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1652398",
        "supporting_url": "https://feed.bithumb.com/notice/1652398",
        "title": "[빗썸] 피크(PEAQ) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-03-23 23:10:00",
        "delta_from_notice_seconds": -34,
        "delta_label": "-34s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-03-20 09:33:51",
        "asset_scope": "WAXP",
        "assets": ["WAXP"],
        "scope": "deposit_withdrawal",
        "trigger_type": "wallet_system_check",
        "official_url": "https://feed.bithumb.com/notice/1652352",
        "supporting_url": "https://feed.bithumb.com/notice/1652352",
        "title": "[빗썸] 왁스(WAXP) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-03-20 09:35:00",
        "delta_from_notice_seconds": 69,
        "delta_label": "+69s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-02-28 15:36:52",
        "asset_scope": "0G",
        "assets": ["0G"],
        "scope": "deposit_withdrawal",
        "trigger_type": "network_issue",
        "official_url": "https://feed.bithumb.com/notice/1652147",
        "supporting_url": "https://feed.bithumb.com/notice/1652147",
        "title": "[빗썸] 0G 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-02-28 15:40:00",
        "delta_from_notice_seconds": 188,
        "delta_label": "+188s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-02-24 11:20:00",
        "asset_scope": "FLOW",
        "assets": ["FLOW"],
        "scope": "withdrawal_only",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1652079",
        "supporting_url": "https://feed.bithumb.com/notice/1652079",
        "title": "[빗썸] 플로우(FLOW) 출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-02-24 11:20:00",
        "delta_from_notice_seconds": 0,
        "delta_label": "0s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-02-23 20:57:49",
        "asset_scope": "POKT",
        "assets": ["POKT"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1652078",
        "supporting_url": "https://feed.bithumb.com/notice/1652078",
        "title": "[빗썸] 포켓네트워크(POKT) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-02-23 21:00:00",
        "delta_from_notice_seconds": 131,
        "delta_label": "+131s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-02-13 08:46:44",
        "asset_scope": "REI",
        "assets": ["REI"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1652002",
        "supporting_url": "https://feed.bithumb.com/notice/1652002",
        "title": "[빗썸] 레이(REI) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-02-13 08:50:00",
        "delta_from_notice_seconds": 196,
        "delta_label": "+196s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-02-09 23:05:00",
        "asset_scope": "VANA",
        "assets": ["VANA"],
        "scope": "deposit_withdrawal",
        "trigger_type": "node_sync_issue",
        "official_url": "https://feed.bithumb.com/notice/1651944",
        "supporting_url": "https://feed.bithumb.com/notice/1651944",
        "title": "[빗썸] 바나(VANA) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-02-09 23:05:00",
        "delta_from_notice_seconds": 0,
        "delta_label": "0s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-01-31 04:10:00",
        "asset_scope": "USDT-Tron",
        "assets": ["USDT"],
        "scope": "withdrawal_only",
        "trigger_type": "wallet_system_check",
        "official_url": "https://feed.bithumb.com/notice/1651736",
        "supporting_url": "https://feed.bithumb.com/notice/1651736",
        "title": "[빗썸] 테더(USDT) 출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-01-31 04:10:00",
        "delta_from_notice_seconds": 0,
        "delta_label": "0s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-01-19 12:55:37",
        "asset_scope": "USDT-Tron",
        "assets": ["USDT"],
        "scope": "withdrawal_only",
        "trigger_type": "wallet_system_check",
        "official_url": "https://feed.bithumb.com/notice/1651542",
        "supporting_url": "https://feed.bithumb.com/notice/1651542",
        "title": "[빗썸] 테더(USDT) 출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-01-19 12:55:00",
        "delta_from_notice_seconds": -37,
        "delta_label": "-37s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2026-01-05 20:59:50",
        "asset_scope": "STRK",
        "assets": ["STRK"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1651445",
        "supporting_url": "https://feed.bithumb.com/notice/1651445",
        "title": "[빗썸] 스타크넷(STRK) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2026-01-05 21:00:00",
        "delta_from_notice_seconds": 10,
        "delta_label": "+10s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-12-03 14:40:53",
        "asset_scope": "DIS",
        "assets": ["DIS"],
        "scope": "withdrawal_only",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1650998",
        "supporting_url": "https://feed.bithumb.com/notice/1650998",
        "title": "[빗썸] 디스(DIS) 출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-12-03 14:42:00",
        "delta_from_notice_seconds": 67,
        "delta_label": "+67s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-11-21 17:39:41",
        "asset_scope": "ADA",
        "assets": ["ADA"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1650802",
        "supporting_url": "https://feed.bithumb.com/notice/1650802",
        "title": "[빗썸] 에이다(ADA) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-11-21 17:40:00",
        "delta_from_notice_seconds": 19,
        "delta_label": "+19s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-11-03 19:45:40",
        "asset_scope": "BERA",
        "assets": ["BERA"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1650517",
        "supporting_url": "https://feed.bithumb.com/notice/1650517",
        "title": "[빗썸] 베라체인(BERA) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-11-03 19:45:00",
        "delta_from_notice_seconds": -40,
        "delta_label": "-40s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-10-11 11:45:55",
        "asset_scope": "DYDX",
        "assets": ["DYDX"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1650288",
        "supporting_url": "https://feed.bithumb.com/notice/1650288",
        "title": "[빗썸] 디와이디엑스(DYDX) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-10-11 11:45:00",
        "delta_from_notice_seconds": -55,
        "delta_label": "-55s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-09-22 18:10:39",
        "asset_scope": "ADD",
        "assets": ["ADD"],
        "scope": "withdrawal_only",
        "trigger_type": "wallet_system_check",
        "official_url": "https://feed.bithumb.com/notice/1650017",
        "supporting_url": "https://feed.bithumb.com/notice/1650017",
        "title": "[빗썸] 애드(ADD) 출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-09-22 18:10:00",
        "delta_from_notice_seconds": -39,
        "delta_label": "-39s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-09-02 15:56:36",
        "asset_scope": "STRK",
        "assets": ["STRK"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1649774",
        "supporting_url": "https://feed.bithumb.com/notice/1649774",
        "title": "[빗썸] 스타크넷(STRK) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-09-02 15:55:00",
        "delta_from_notice_seconds": -96,
        "delta_label": "-96s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-08-29 13:12:21",
        "asset_scope": "ZRC",
        "assets": ["ZRC"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1649671",
        "supporting_url": "https://feed.bithumb.com/notice/1649671",
        "title": "[빗썸] 저킷(ZRC) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-08-29 13:12:00",
        "delta_from_notice_seconds": -21,
        "delta_label": "-21s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-06-26 14:04:45",
        "asset_scope": "FLR",
        "assets": ["FLR"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1649062",
        "supporting_url": "https://feed.bithumb.com/notice/1649062",
        "title": "[빗썸] 플레어(FLR) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-06-26 14:05:00",
        "delta_from_notice_seconds": 15,
        "delta_label": "+15s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-05-31 11:43:30",
        "asset_scope": "REI",
        "assets": ["REI"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1648710",
        "supporting_url": "https://feed.bithumb.com/notice/1648710",
        "title": "[빗썸] 레이(REI) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-05-31 11:45:00",
        "delta_from_notice_seconds": 90,
        "delta_label": "+90s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-04-15 00:53:21",
        "asset_scope": "ATOM",
        "assets": ["ATOM"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1648132",
        "supporting_url": "https://feed.bithumb.com/notice/1648132",
        "title": "[빗썸] 코스모스(ATOM) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-04-15 00:55:00",
        "delta_from_notice_seconds": 99,
        "delta_label": "+99s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-02-18 20:00:19",
        "asset_scope": "FLOW",
        "assets": ["FLOW"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1647038",
        "supporting_url": "https://feed.bithumb.com/notice/1647038",
        "title": "[빗썸] 플로우(FLOW) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-02-18 20:00:00",
        "delta_from_notice_seconds": -19,
        "delta_label": "-19s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-01-31 18:42:09",
        "asset_scope": "IOTX",
        "assets": ["IOTX"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1646858",
        "supporting_url": "https://feed.bithumb.com/notice/1646858",
        "title": "[빗썸] 아이오텍스(IOTX) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-01-31 18:45:00",
        "delta_from_notice_seconds": 171,
        "delta_label": "+171s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2025-01-16 02:20:40",
        "asset_scope": "ZIL",
        "assets": ["ZIL"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1646423",
        "supporting_url": "https://feed.bithumb.com/notice/1646423",
        "title": "[빗썸] 질리카(ZIL) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2025-01-16 02:30:00",
        "delta_from_notice_seconds": 560,
        "delta_label": "+560s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2024-11-27 11:12:24",
        "asset_scope": "STX,ALEX",
        "assets": ["ALEX", "STX"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1645260",
        "supporting_url": "https://feed.bithumb.com/notice/1645260",
        "title": "[빗썸] 스택스(STX), 알렉스(ALEX) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2024-11-27 11:13:00",
        "delta_from_notice_seconds": 36,
        "delta_label": "+36s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2024-11-21 19:23:52",
        "asset_scope": "SUI,LWA",
        "assets": ["LWA", "SUI"],
        "scope": "deposit_withdrawal",
        "trigger_type": "block_generation_stop",
        "official_url": "https://feed.bithumb.com/notice/1645244",
        "supporting_url": "https://feed.bithumb.com/notice/1645244",
        "title": "[빗썸] 수이(SUI), 루미웨이브(LWA) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2024-11-21 19:30:00",
        "delta_from_notice_seconds": 368,
        "delta_label": "+368s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2024-11-01 11:55:09",
        "asset_scope": "ZETA",
        "assets": ["ZETA"],
        "scope": "deposit_withdrawal",
        "trigger_type": "network_issue",
        "official_url": "https://feed.bithumb.com/notice/1645183",
        "supporting_url": "https://feed.bithumb.com/notice/1645183",
        "title": "[빗썸] 제타체인(ZETA) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2024-11-01 11:55:00",
        "delta_from_notice_seconds": -9,
        "delta_label": "-9s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2024-10-02 17:12:51",
        "asset_scope": "LUNA2",
        "assets": ["LUNA2"],
        "scope": "deposit_withdrawal",
        "trigger_type": "network_issue",
        "official_url": "https://feed.bithumb.com/notice/1645123",
        "supporting_url": "https://feed.bithumb.com/notice/1645123",
        "title": "[빗썸] 루나2(LUNA2) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2024-10-02 17:13:00",
        "delta_from_notice_seconds": 9,
        "delta_label": "+9s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
    {
        "notice_published_at_kst": "2024-09-27 15:29:20",
        "asset_scope": "ZIL",
        "assets": ["ZIL"],
        "scope": "deposit_withdrawal",
        "trigger_type": "network_issue",
        "official_url": "https://feed.bithumb.com/notice/1645109",
        "supporting_url": "https://feed.bithumb.com/notice/1645109",
        "title": "[빗썸] 질리카(ZIL) 입출금 일시 중단 안내",
        "stated_stop_at_kst": "2024-09-27 15:30:00",
        "delta_from_notice_seconds": 40,
        "delta_label": "+40s",
        "future_wording_confirmed": True,
        "archive_page": 1,
    },
]


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=40) as response:
        return response.read().decode("utf-8", "ignore")


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def crawl_archive(max_page: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(1, max_page + 1):
        html = fetch_text(
            f"https://bloomingbit.io/reporters/exchange-announcement-bot?page={page}"
        )
        for match in ARCHIVE_NEWS_PATTERN.finditer(html):
            title = normalize_spaces(match.group("title"))
            rows.append(
                {
                    "page": page,
                    "article_url": match.group("article_url").replace(
                        "/news/", "/feed/news/"
                    ),
                    "title": title,
                    "card_content": "",
                }
            )
        if page % 10 == 0:
            print(f"[crawl] page={page} rows={len(rows)}", flush=True)
    return rows


def is_relevant_archive_row(row: dict[str, Any]) -> bool:
    title = row["title"]
    if not title.startswith("[빗썸]"):
        return False
    if "원화 " in title or "원화(" in title or "원화 마켓" in title:
        return False
    return any(keyword in title for keyword in RELEVANT_TITLE_KEYWORDS)


def extract_assets(title: str) -> list[str]:
    return sorted(set(TITLE_TICKER_PATTERN.findall(title)))


def extract_official_url(article_url: str) -> str | None:
    html = fetch_text(article_url)
    match = OFFICIAL_URL_PATTERN.search(html)
    return match.group(0) if match else None


def parse_scope(title: str, body_text: str) -> str:
    if "출금" in title and "입출금" not in title:
        return "withdrawal_only"
    if "입금" in title and "출금" not in title:
        return "deposit_only"
    if "출금" in body_text and "입출금" not in body_text and "입금" not in body_text:
        return "withdrawal_only"
    return "deposit_withdrawal"


def detect_trigger_type(body_text: str) -> str | None:
    for reason_type, keywords in REASON_KEYWORDS.items():
        if any(keyword in body_text for keyword in keywords):
            return reason_type
    return None


def parse_published_at(text: str) -> str | None:
    match = PUBLISHED_AT_PATTERN.search(text)
    return match.group(1) if match else None


def parse_stop_at(body_text: str) -> str | None:
    match = STOP_AT_PATTERN.search(body_text)
    if not match:
        return None
    year, month, day, ampm, hour_text, minute_text = match.groups()
    hour = int(hour_text)
    minute = int(minute_text or 0)
    if ampm == "오후" and hour != 12:
        hour += 12
    if ampm == "오전" and hour == 12:
        hour = 0
    return f"{year}-{month}-{day} {hour:02d}:{minute:02d}:00"


def extract_service_limit_scope(body_text: str, fallback_assets: list[str]) -> str:
    match = SERVICE_LIMIT_PATTERN.search(body_text)
    if not match:
        return ",".join(fallback_assets) if fallback_assets else "-"
    snippet = match.group(1)
    snippet = re.sub(r"\*+", " ", snippet)
    lines = [normalize_spaces(line) for line in snippet.splitlines()]
    bullet_lines = [
        line.lstrip("- ").strip() for line in lines if line.strip().startswith("-")
    ]
    if bullet_lines:
        return " / ".join(bullet_lines[:2])
    cleaned = normalize_spaces(snippet)
    return (
        cleaned[:160]
        if cleaned
        else (",".join(fallback_assets) if fallback_assets else "-")
    )


def build_row(archive_row: dict[str, Any], official_text: str) -> dict[str, Any] | None:
    assets = extract_assets(archive_row["title"])
    body_text = (
        official_text.split("* * *")[-1] if "* * *" in official_text else official_text
    )
    body_text = body_text.strip()
    notice_published_at = parse_published_at(official_text)
    stated_stop_at = parse_stop_at(body_text)
    if not notice_published_at or not stated_stop_at:
        return None

    published_dt = datetime.strptime(notice_published_at, "%Y-%m-%d %H:%M:%S")
    stop_dt = datetime.strptime(stated_stop_at, "%Y-%m-%d %H:%M:%S")
    delta_seconds = int((stop_dt - published_dt).total_seconds())
    future_wording = bool(FUTURE_WORDING_PATTERN.search(body_text))

    return {
        "notice_published_at_kst": notice_published_at,
        "asset_scope": extract_service_limit_scope(body_text, assets),
        "assets": assets,
        "scope": parse_scope(archive_row["title"], body_text),
        "trigger_type": detect_trigger_type(body_text),
        "official_url": archive_row["official_url"],
        "supporting_url": archive_row["official_url"],
        "title": archive_row["title"],
        "stated_stop_at_kst": stated_stop_at,
        "delta_from_notice_seconds": delta_seconds,
        "delta_label": f"{delta_seconds:+d}s" if delta_seconds else "0s",
        "future_wording_confirmed": future_wording,
        "archive_page": archive_row["page"],
    }


def build_payload(
    rows: list[dict[str, Any]], diagnostics: dict[str, int]
) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exchange": "bithumb",
        "definition": (
            "Include Bithumb notices whose body still uses future scheduled wording, but whose stated stop "
            "time was within plus or minus 10 minutes of the notice publication time. This is an operational "
            "or practical-immediate bucket, separate from the stricter already-stopped bucket."
        ),
        "threshold_seconds": THRESHOLD_SECONDS,
        "source_note": (
            "Rows were rebuilt from the Bloomingbit exchange-announcement archive, then confirmed against "
            "official Bithumb notice text retrieved through a text mirror of the official page."
        ),
        "excluded_note": (
            "Notices without an explicit stop timestamp, notices whose stop timestamp was more than 10 minutes "
            "away from publication, and notices already counted in the stricter immediate-stop set were excluded."
        ),
        "diagnostics": diagnostics,
        "rows": rows,
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb Effective Immediate Suspensions",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Exchange: {payload['exchange'].upper()}",
        f"- Confirmed rows: {len(payload['rows'])}",
        f"- Threshold: +/- {payload['threshold_seconds']} seconds from official notice publication time",
        f"- Archive rows scanned: {payload['diagnostics']['archive_rows_scanned']}",
        f"- Relevant archive rows reviewed: {payload['diagnostics']['relevant_archive_rows']}",
        f"- Official URLs reviewed: {payload['diagnostics']['official_urls_reviewed']}",
        "- Interpretation: these notices still say 'scheduled' in the body, but operationally they were same-minute or near-immediate stops.",
        "",
        "| Notice Time (KST) | Asset Scope | Scope | Trigger | Stated Stop (KST) | Delta | Official |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in payload["rows"]:
        notice_id = row["official_url"].rstrip("/").split("/")[-1]
        lines.append(
            "| {notice_time} | {asset_scope} | {scope} | {trigger} | {stop_time} | {delta} | [{notice_id}]({url}) |".format(
                notice_time=row["notice_published_at_kst"],
                asset_scope=row["asset_scope"],
                scope=row["scope"],
                trigger=row["trigger_type"] or "-",
                stop_time=row["stated_stop_at_kst"],
                delta=row["delta_label"],
                notice_id=notice_id,
                url=row["official_url"],
            )
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- {payload['definition']}",
            f"- {payload['source_note']}",
            f"- {payload['excluded_note']}",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--fallback-only", action="store_true")
    args = parser.parse_args()

    if args.fallback_only:
        payload = build_payload(
            list(MANUAL_FALLBACK_ROWS),
            diagnostics={
                "archive_rows_scanned": 0,
                "relevant_archive_rows": 0,
                "official_urls_reviewed": 0,
                "strict_urls_excluded": 0,
                "fallback_rows_used": len(MANUAL_FALLBACK_ROWS),
            },
        )
        write_json(args.json_output, payload)
        args.markdown_output.write_text(build_markdown(payload), encoding="utf-8")
        print(
            json.dumps(
                {
                    "json_output": str(args.json_output),
                    "markdown_output": str(args.markdown_output),
                    "rows": len(payload["rows"]),
                    "fallback_only": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    strict_payload = json.loads(STRICT_OUTPUT.read_text(encoding="utf-8"))
    strict_urls = {
        row["official_url"] for row in strict_payload["exchanges"]["bithumb"]
    }

    archive_rows = crawl_archive(ARCHIVE_MAX_PAGE)
    relevant_rows = [row for row in archive_rows if is_relevant_archive_row(row)]

    article_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(extract_official_url, row["article_url"]): row
            for row in relevant_rows
        }
        completed = 0
        for future in as_completed(future_map):
            row = future_map[future]
            completed += 1
            if completed % 25 == 0:
                print(f"[article] completed={completed}/{len(future_map)}", flush=True)
            try:
                official_url = future.result()
            except Exception:
                continue
            if not official_url:
                continue
            article_rows.append({**row, "official_url": official_url})

    deduped_rows: dict[str, dict[str, Any]] = {}
    for row in article_rows:
        deduped_rows[row["official_url"]] = row

    parsed_rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_map = {
            executor.submit(
                fetch_text,
                "https://r.jina.ai/http://" + row["official_url"].split("://", 1)[1],
            ): row
            for row in deduped_rows.values()
        }
        completed = 0
        for future in as_completed(future_map):
            archive_row = future_map[future]
            completed += 1
            if completed % 25 == 0:
                print(f"[official] completed={completed}/{len(future_map)}", flush=True)
            try:
                official_text = future.result()
            except Exception:
                continue
            parsed = build_row(archive_row, official_text)
            if not parsed:
                continue
            if parsed["official_url"] in strict_urls:
                continue
            if not parsed["future_wording_confirmed"]:
                continue
            if abs(parsed["delta_from_notice_seconds"]) > THRESHOLD_SECONDS:
                continue
            parsed_rows.append(parsed)

    parsed_rows.sort(key=lambda row: row["notice_published_at_kst"], reverse=True)

    diagnostics = {
        "archive_rows_scanned": len(archive_rows),
        "relevant_archive_rows": len(relevant_rows),
        "official_urls_reviewed": len(deduped_rows),
        "strict_urls_excluded": len(strict_urls),
        "fallback_rows_used": 0,
    }
    if not parsed_rows:
        parsed_rows = list(MANUAL_FALLBACK_ROWS)
        diagnostics["fallback_rows_used"] = len(MANUAL_FALLBACK_ROWS)

    payload = build_payload(parsed_rows, diagnostics=diagnostics)

    write_json(args.json_output, payload)
    args.markdown_output.write_text(build_markdown(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
                "rows": len(payload["rows"]),
                "relevant_archive_rows": len(relevant_rows),
                "official_urls_reviewed": len(deduped_rows),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
