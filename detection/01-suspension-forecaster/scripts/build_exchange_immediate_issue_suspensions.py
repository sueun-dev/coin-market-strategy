#!/usr/bin/env python3
"""Scan the Bloomingbit exchange-announcement archive and rebuild strict immediate-stop outputs."""

from __future__ import annotations

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCAN_OUTPUT = ROOT / "config" / "exchange_notice_archive_scan.json"
DEFAULT_STRICT_OUTPUT = ROOT / "config" / "exchange_immediate_issue_suspensions.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "EXCHANGE_IMMEDIATE_ISSUE_SUSPENSIONS.md"
ARCHIVE_MAX_PAGE = 60
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"

CARD_PATTERN = re.compile(
    r'<a class="feedRealTimeLink[^"]*" href="(?P<link>/feed/news/\d+)">.*?'
    r'<h4 class="title">(?P<title>.*?)</h4>.*?'
    r'<p class="content">(?P<content>.*?)</p>',
    re.S,
)

DATE_PATTERN = re.compile(
    r"입력\s*(오전|오후)\s*(\d{1,2}:\d{2})\s*·\s*(\d{4})\.\s*(\d{2})\.\s*(\d{2})\."
)

OFFICIAL_URL_PATTERNS = (
    re.compile(r"https://upbit\.com/service_center/notice\?id=\d+"),
    re.compile(r"https://feed\.bithumb\.com/notice/\d+"),
)

POSITIVE_IMMEDIATE_PATTERNS = (
    "입출금을 일시 중단합니다",
    "입출금을 일시 중단합니다",
    "입출금 서비스를 일시 중단합니다",
    "입출금 지원을 일시 중단합니다",
    "입출금을 일시 중지합니다",
    "입출금 서비스를 일시 중지합니다",
    "입출금 서비스가 일시 중단된다고 밝혔다",
    "입출금 서비스가 일시 중단한다고 밝혔다",
    "출금을 일시 중단합니다",
    "출금 서비스를 일시 중단합니다",
    "공지 등록 시점",
    "공지사항 등록 시점",
)

DELAY_PATTERNS = (
    "입출금 서비스가 지연중입니다",
    "입출금 서비스가 지연되고 있습니다",
    "입출금이 지연되고 있습니다",
    "입금이 지연되고 있습니다",
    "출금이 지연되고 있습니다",
    "처리가 지연되고 있습니다",
    "출금 요청량 증가로 인하여 출금이 지연되고 있습니다",
    "일시 지연 안내",
)

FUTURE_SCHEDULE_PATTERNS = (
    "진행될 예정으로",
    "진행될 예정입니다",
    "중지 될 예정입니다",
    "중단될 예정입니다",
    "일시 중단될 예정입니다",
    "중지 시점",
    "입출금 지원 중단 시점",
    "출금 지원 중단 시점",
)

FUTURE_TITLE_PATTERN = re.compile(r"\((?:\d{1,4}[./-])?\d{1,2}[./-]\d{1,2}[^)]*~")

ISSUE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "block_generation_stop": ("블록 생성 중단", "블록생성 중단"),
    "node_sync_issue": ("노드 동기화 문제",),
    "node_issue": ("블록체인 노드 문제", "블록체인 노드 이슈", "노드 문제"),
    "network_issue": ("네트워크 이슈", "메인넷 네트워크 이슈"),
    "wallet_system_check": ("월렛 시스템 점검", "내부 월렛 시스템 점검"),
    "withdrawal_surge": ("출금량 증가", "출금 요청량 증가"),
    "security_issue": ("보안 취약점", "보안 이슈", "보안 취약"),
    "project_issue_or_investor_caution": (
        "프로젝트 이슈",
        "유의촉구",
        "거래유의종목",
        "투자 유의",
        "디지털 자산 거래소 공동협의체",
    ),
}

IMMEDIATE_REVIEW_HINTS = (
    "네트워크 이슈",
    "블록 생성 중단",
    "블록생성 중단",
    "블록체인 노드",
    "노드 동기화 문제",
    "월렛 시스템 점검",
    "내부 월렛 시스템 점검",
    "보안 취약",
    "보안 이슈",
    "프로젝트 이슈",
    "유의촉구",
    "거래유의종목",
    "출금량 증가",
    "출금 요청량 증가",
    "지연 안내",
    "지연중입니다",
    "지연되고 있습니다",
)

SCHEDULED_REVIEW_HINTS = (
    "네트워크 업그레이드",
    "월렛 업그레이드",
    "네트워크 전환",
    "토큰 스왑",
    "리브랜딩",
    "메인넷 런칭",
)

MANUAL_CONFIRMED_BITHUMB_STRICT_ROWS = [
    {
        "occurred_at_kst": "2024-10-15 00:12:35",
        "assets": ["SUI", "LWA"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to system check",
        "official_url": "https://feed.bithumb.com/notice/1645139",
        "supporting_url": "https://feed.bithumb.com/notice/1645139",
        "title": "수이(SUI), 루미웨이브(LWA) 입출금 일시 중지 안내 (10/18 재개)",
    },
    {
        "occurred_at_kst": "2024-10-04 08:39:38",
        "assets": ["SEI"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1645124",
        "supporting_url": "https://feed.bithumb.com/notice/1645124",
        "title": "세이(SEI) 입출금 일시 중지 안내 (10/04 재개)",
    },
    {
        "occurred_at_kst": "2024-10-01 03:18:44",
        "assets": [
            "EOS",
            "IQ",
            "EOSDAC",
            "MEETONE",
            "HORUS",
            "ADD",
            "CHL",
            "BLACK",
            "ATD",
        ],
        "scope": "mixed_scope",
        "reason_type": "network_issue",
        "strict_basis": "official body says EOS-family service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1645119",
        "supporting_url": "https://feed.bithumb.com/notice/1645119",
        "title": "이오스(EOS) 및 이오스 계열 입출금 일시 중지 안내 (10/02 재개)",
    },
    {
        "occurred_at_kst": "2024-08-08 23:25:06",
        "assets": ["ASTR"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1645006",
        "supporting_url": "https://feed.bithumb.com/notice/1645006",
        "title": "아스타(ASTR) 입출금 일시 중지 안내 (08/09 재개)",
    },
    {
        "occurred_at_kst": "2024-07-27 20:09:24",
        "assets": ["CSPR"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644980",
        "supporting_url": "https://feed.bithumb.com/notice/1644980",
        "title": "캐스퍼(CSPR) 입출금 일시 중지 안내(08/09 재개)",
    },
    {
        "occurred_at_kst": "2024-07-24 20:09:40",
        "assets": ["XLM", "AQUA"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to system check",
        "official_url": "https://feed.bithumb.com/notice/1644975",
        "supporting_url": "https://feed.bithumb.com/notice/1644975",
        "title": "스텔라루멘(XLM), 아쿠아(AQUA) 입출금 일시 중지 안내 (07/25 재개)",
    },
    {
        "occurred_at_kst": "2024-07-11 20:10:41",
        "assets": ["MTL"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to system check",
        "official_url": "https://feed.bithumb.com/notice/1644936",
        "supporting_url": "https://feed.bithumb.com/notice/1644936",
        "title": "메탈(MTL) 입출금 일시 중지 안내 (07/12 재개)",
    },
    {
        "occurred_at_kst": "2024-07-06 03:17:10",
        "assets": ["SUI", "LWA"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644914",
        "supporting_url": "https://feed.bithumb.com/notice/1644914",
        "title": "수이(SUI), 루미웨이브(LWA) 입출금 일시 중지 안내 (07/06 재개)",
    },
    {
        "occurred_at_kst": "2024-06-19 13:57:03",
        "assets": ["KSM"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to wallet check",
        "official_url": "https://feed.bithumb.com/notice/1644868",
        "supporting_url": "https://feed.bithumb.com/notice/1644868",
        "title": "쿠사마(KSM) 입출금 일시 중지 안내 (06/19 재개)",
    },
    {
        "occurred_at_kst": "2024-06-11 23:26:35",
        "assets": ["KSM"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644849",
        "supporting_url": "https://feed.bithumb.com/notice/1644849",
        "title": "쿠사마(KSM) 입출금 일시 중지 안내 (06/12 재개)",
    },
    {
        "occurred_at_kst": "2024-06-10 17:54:22",
        "assets": ["AR"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644846",
        "supporting_url": "https://feed.bithumb.com/notice/1644846",
        "title": "알위브(AR) 입출금 일시 중지 안내 (06/11 재개)",
    },
    {
        "occurred_at_kst": "2024-06-08 13:00:02",
        "assets": ["FLOW"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to system check",
        "official_url": "https://feed.bithumb.com/notice/1644843",
        "supporting_url": "https://feed.bithumb.com/notice/1644843",
        "title": "플로우(FLOW) 입출금 일시 중지 안내 (06/15 재개)",
    },
    {
        "occurred_at_kst": "2024-05-22 01:33:43",
        "assets": ["SPURS"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense because the CHZ network had an issue",
        "official_url": "https://feed.bithumb.com/notice/1644805",
        "supporting_url": "https://feed.bithumb.com/notice/1644805",
        "title": "토트넘 홋스퍼(SPURS) 입출금 일시 중지 안내 (05/23 재개)",
    },
    {
        "occurred_at_kst": "2024-04-29 05:14:03",
        "assets": ["ENTC"],
        "scope": "deposit_withdrawal",
        "reason_type": "project_issue_or_investor_caution",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to foundation request",
        "official_url": "https://feed.bithumb.com/notice/1644734",
        "supporting_url": "https://feed.bithumb.com/notice/1644734",
        "title": "엔터버튼(ENTC) 입출금 일시 중지 안내",
    },
    {
        "occurred_at_kst": "2024-04-05 17:54:36",
        "assets": ["STRK"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644687",
        "supporting_url": "https://feed.bithumb.com/notice/1644687",
        "title": "스타크넷(STRK) 입출금 일시 중지 안내 (04/08 재개)",
    },
    {
        "occurred_at_kst": "2024-03-19 12:00:13",
        "assets": ["WAVES", "NSBT"],
        "scope": "mixed_scope",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says WAVES deposit/withdrawal and NSBT withdrawal were suspended immediately due to wallet check",
        "official_url": "https://feed.bithumb.com/notice/1644611",
        "supporting_url": "https://feed.bithumb.com/notice/1644611",
        "title": "웨이브(WAVES), 뉴트리노토큰(NSBT) 입출금 일시 중지 안내 (03/22 재개)",
    },
    {
        "occurred_at_kst": "2024-03-02 17:03:36",
        "assets": ["ASTR"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644581",
        "supporting_url": "https://feed.bithumb.com/notice/1644581",
        "title": "아스타(ASTR) 입출금 일시 중지 안내 (03/11 재개)",
    },
    {
        "occurred_at_kst": "2024-02-19 04:12:18",
        "assets": ["XRP"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to system check",
        "official_url": "https://feed.bithumb.com/notice/1644548",
        "supporting_url": "https://feed.bithumb.com/notice/1644548",
        "title": "리플(XRP) 입출금 일시 중지 안내 (02/19 재개)",
    },
    {
        "occurred_at_kst": "2024-02-01 18:33:00",
        "assets": ["AERGO"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644452",
        "supporting_url": "https://feed.bithumb.com/notice/1644452",
        "title": "아르고(AERGO) 입출금 일시 중지 안내 (02/15 재개)",
    },
    {
        "occurred_at_kst": "2024-01-27 10:19:00",
        "assets": ["SSX"],
        "scope": "deposit_withdrawal",
        "reason_type": "project_issue_or_investor_caution",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to foundation request",
        "official_url": "https://feed.bithumb.com/notice/1644437",
        "supporting_url": "https://feed.bithumb.com/notice/1644437",
        "title": "썸씽(SSX) 입출금 일시 중지 안내 (02/27 출금 재개)",
    },
    {
        "occurred_at_kst": "2024-01-24 18:12:56",
        "assets": ["MATIC", "ORB", "FIT"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644427",
        "supporting_url": "https://feed.bithumb.com/notice/1644427",
        "title": "폴리곤(MATIC), 오브시티(ORB), 300피트 네트워크(FIT) 입출금 일시 중지 안내 (01/24 재개)",
    },
    {
        "occurred_at_kst": "2024-01-18 19:55:00",
        "assets": ["MANTA"],
        "scope": "withdrawal_only",
        "reason_type": "network_issue",
        "strict_basis": "official body says withdrawal service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644425",
        "supporting_url": "https://feed.bithumb.com/notice/1644425",
        "title": "만타 네트워크(MANTA) 출금 일시 중단 안내 (01/22 재개)",
    },
    {
        "occurred_at_kst": "2023-12-18 22:14:00",
        "assets": ["ZIL"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1644341",
        "supporting_url": "https://feed.bithumb.com/notice/1644341",
        "title": "질리카(ZIL) 입출금 일시 중지 안내 (12/20 재개)",
    },
    {
        "occurred_at_kst": "2023-07-29 01:46:49",
        "assets": ["APT"],
        "scope": "deposit_withdrawal",
        "reason_type": "wallet_system_check",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to system check",
        "official_url": "https://feed.bithumb.com/notice/1644004",
        "supporting_url": "https://feed.bithumb.com/notice/1644004",
        "title": "앱토스(APT) 입출금 일시 중단 안내 (7/29 재개)",
    },
    {
        "occurred_at_kst": "2022-05-30 22:32:01",
        "assets": ["XLM", "VELO", "AQUA"],
        "scope": "deposit_withdrawal",
        "reason_type": "network_issue",
        "strict_basis": "official body says service is suspended immediately in direct present tense due to network issue",
        "official_url": "https://feed.bithumb.com/notice/1642934",
        "supporting_url": "https://feed.bithumb.com/notice/1642934",
        "title": "스텔라루멘(XLM), 벨로프로토콜(VELO), 아쿠아(AQUA) 입출금 일시 중지 안내 (05/31 재개)",
    },
]

ASSET_LINE_PATTERN = re.compile(
    r"(?:대상 디지털 자산|출금 중단 대상|입출금 중단 대상)\s*:\s*(.+?)(?:중단 범위|추가 영향 범위|중단 기간|재개 범위|유의사항|출금 중단 대상|입출금 중단 대상)"
)

TITLE_TICKER_PATTERN = re.compile(r"\(([A-Z0-9-]{2,15})\)")


def fetch_text(url: str) -> str:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_html(html: str) -> str:
    html = re.sub(r"<script.*?</script>", " ", html, flags=re.S)
    html = re.sub(r"<style.*?</style>", " ", html, flags=re.S)
    text = unescape(re.sub(r"<[^>]+>", " ", html))
    return normalize_spaces(text)


def crawl_archive(max_page: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for page in range(1, max_page + 1):
        html = fetch_text(
            f"https://bloomingbit.io/reporters/exchange-announcement-bot?page={page}"
        )
        for match in CARD_PATTERN.finditer(html):
            title = normalize_spaces(unescape(match.group("title")))
            content = normalize_spaces(
                unescape(match.group("content"))
                .replace("<br />", " ")
                .replace("<br/>", " ")
            )
            rows.append(
                {
                    "page": page,
                    "article_url": f"https://bloomingbit.io{match.group('link')}",
                    "title": title,
                    "card_content": content,
                }
            )
    return rows


def is_keyword_candidate(row: dict[str, Any]) -> bool:
    title = row["title"]
    if not (title.startswith("[업비트]") or title.startswith("[빗썸]")):
        return False
    if "원화 " in title or "원화 입출금" in title:
        return False
    return ("입출금" in title or "출금" in title) and any(
        keyword in title for keyword in ("중단", "중지", "지연")
    )


def needs_body_review(row: dict[str, Any]) -> bool:
    text = f"{row['title']} {row['card_content']}"
    if any(keyword in text for keyword in IMMEDIATE_REVIEW_HINTS):
        return True
    if FUTURE_TITLE_PATTERN.search(row["title"]):
        return False
    if any(keyword in text for keyword in FUTURE_SCHEDULE_PATTERNS):
        return False
    if any(keyword in text for keyword in SCHEDULED_REVIEW_HINTS):
        return False
    return True


def detect_reason_type(text: str) -> str | None:
    for reason_type, keywords in ISSUE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return reason_type
    return None


def parse_occurred_at_kst(text: str) -> str | None:
    match = DATE_PATTERN.search(text)
    if not match:
        return None
    ampm, time_part, year, month, day = match.groups()
    hour, minute = (int(part) for part in time_part.split(":"))
    if ampm == "오후" and hour != 12:
        hour += 12
    if ampm == "오전" and hour == 12:
        hour = 0
    return f"{year}-{month}-{day} {hour:02d}:{minute:02d}"


def detect_scope(title: str, text: str) -> str:
    if "출금" in title and "입출금" not in title:
        return "withdrawal_only"
    if "출금만을 지원" in text:
        return "withdrawal_only"
    if "입금" in title and "출금" not in title:
        return "deposit_only"
    return "deposit_withdrawal"


def extract_assets(title: str, text: str) -> list[str]:
    match = ASSET_LINE_PATTERN.search(text)
    if match:
        segment = match.group(1)
        tickers = sorted(set(re.findall(r"\(([A-Z0-9-]{2,15})\)", segment)))
        if tickers:
            return tickers
        upper_tokens = re.findall(r"\b[A-Z0-9-]{2,15}\b", segment)
        filtered = sorted(set(token for token in upper_tokens if token != "KST"))
        if filtered:
            return filtered

    title_tickers = TITLE_TICKER_PATTERN.findall(title)
    if title_tickers:
        return sorted(set(title_tickers))

    before_notice = re.split(r"입출금|출금", title, maxsplit=1)[0]
    fallback_tokens = re.findall(r"\b[A-Z0-9-]{2,15}\b", before_notice)
    return sorted(set(fallback_tokens))


def build_strict_basis(text: str, reason_type: str | None) -> str:
    if "공지 등록 시점" in text or "공지사항 등록 시점" in text:
        return "body says suspension starts from notice registration time"
    if "입출금을 일시 중단합니다" in text or "입출금 서비스를 일시 중단합니다" in text:
        return "body uses direct present-tense immediate suspension wording"
    if "출금을 일시 중단합니다" in text:
        return "body uses direct present-tense immediate withdrawal suspension wording"
    if reason_type == "security_issue":
        return "body says a security issue was identified and service was suspended immediately"
    if reason_type == "project_issue_or_investor_caution":
        return "body says a project-risk or investor-caution issue was identified and service was suspended immediately"
    return "body indicates the issue was already live and the service was stopped immediately"


def fetch_candidate_detail(row: dict[str, Any]) -> dict[str, Any]:
    html = fetch_text(row["article_url"])
    text = strip_html(html)
    official_url = None
    for pattern in OFFICIAL_URL_PATTERNS:
        match = pattern.search(html)
        if match:
            official_url = match.group(0)
            break

    exchange = "upbit" if row["title"].startswith("[업비트]") else "bithumb"
    reason_type = detect_reason_type(text)
    immediate_positive = any(pattern in text for pattern in POSITIVE_IMMEDIATE_PATTERNS)
    delay_only = any(pattern in text for pattern in DELAY_PATTERNS)
    future_negative = FUTURE_TITLE_PATTERN.search(row["title"]) is not None or any(
        pattern in text for pattern in FUTURE_SCHEDULE_PATTERNS
    )
    strict_immediate_stop = bool(immediate_positive and reason_type and not delay_only)
    if (
        future_negative
        and "공지 등록 시점" not in text
        and "공지사항 등록 시점" not in text
    ):
        strict_immediate_stop = False

    return {
        "page": row["page"],
        "article_url": row["article_url"],
        "title": row["title"],
        "official_url": official_url,
        "exchange": exchange,
        "occurred_at_kst": parse_occurred_at_kst(text),
        "assets": extract_assets(row["title"], text),
        "scope": detect_scope(row["title"], text),
        "reason_type": reason_type,
        "card_content": row["card_content"],
        "strict_immediate_stop": strict_immediate_stop,
        "strict_basis": build_strict_basis(text, reason_type)
        if strict_immediate_stop
        else None,
        "delay_only": delay_only,
        "future_negative": future_negative,
        "has_notice_registration_time": "공지 등록 시점" in text
        or "공지사항 등록 시점" in text,
        "error": None,
    }


def review_candidates(rows: list[dict[str, Any]], workers: int) -> list[dict[str, Any]]:
    reviewed: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(fetch_candidate_detail, row): row["article_url"]
            for row in rows
        }
        for future in as_completed(future_map):
            article_url = future_map[future]
            try:
                reviewed.append(future.result())
            except (HTTPError, URLError, TimeoutError) as exc:
                reviewed.append(
                    {
                        "page": None,
                        "article_url": article_url,
                        "title": None,
                        "official_url": None,
                        "exchange": None,
                        "occurred_at_kst": None,
                        "assets": [],
                        "scope": None,
                        "reason_type": None,
                        "card_content": None,
                        "strict_immediate_stop": False,
                        "strict_basis": None,
                        "delay_only": False,
                        "future_negative": False,
                        "has_notice_registration_time": False,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
    return sorted(
        reviewed,
        key=lambda item: (
            item["occurred_at_kst"] or "",
            item["article_url"] or "",
        ),
        reverse=True,
    )


def unique_by_official_url(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = row.get("official_url") or row.get("article_url")
        current = seen.get(key)
        if current is None or (row.get("occurred_at_kst") or "") > (
            current.get("occurred_at_kst") or ""
        ):
            seen[key] = row
    return sorted(
        seen.values(),
        key=lambda item: (
            item.get("occurred_at_kst") or "",
            item.get("official_url") or item.get("article_url") or "",
        ),
        reverse=True,
    )


def build_scan_payload(
    all_rows: list[dict[str, Any]],
    keyword_candidates: list[dict[str, Any]],
    review_candidates_input: list[dict[str, Any]],
    reviewed: list[dict[str, Any]],
) -> dict[str, Any]:
    strict_rows = [
        row for row in reviewed if row["strict_immediate_stop"] and row["official_url"]
    ]
    strict_rows = unique_by_official_url(strict_rows)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "archive_scan": {
            "pages_scanned": ARCHIVE_MAX_PAGE,
            "total_rows": len(all_rows),
            "keyword_candidate_count": len(keyword_candidates),
            "body_review_candidate_count": len(review_candidates_input),
            "reviewed_candidate_count": len(reviewed),
            "review_error_count": sum(1 for row in reviewed if row["error"]),
            "strict_immediate_stop_count": len(strict_rows),
        },
        "notes": [
            "Source archive: Bloomingbit reporter page `exchange-announcement-bot`, scanned from page 1 through page 60 because page 61 and beyond returned zero notice rows.",
            "Keyword candidates were exchange notices whose titles mentioned deposit/withdrawal or withdrawal plus suspension/stop/delay wording.",
            "Strict immediate-stop requires body text that reads as already-live trouble with current-tense stop wording. Scheduled future-stop wording was excluded.",
        ],
        "candidates": reviewed,
        "strict_immediate_stop_candidates": strict_rows,
    }


def build_strict_payload(scan_payload: dict[str, Any]) -> dict[str, Any]:
    exchanges = {"upbit": [], "bithumb": []}
    excluded_examples = {"future_scheduled_examples": [], "delay_only_examples": []}

    future_examples_seen: set[str] = set()
    delay_examples_seen: set[str] = set()

    for row in scan_payload["candidates"]:
        if row["error"] or not row["official_url"]:
            continue
        if row["strict_immediate_stop"]:
            exchanges[row["exchange"]].append(
                {
                    "occurred_at_kst": row["occurred_at_kst"],
                    "assets": row["assets"],
                    "scope": row["scope"],
                    "reason_type": row["reason_type"],
                    "strict_basis": row["strict_basis"],
                    "official_url": row["official_url"],
                    "supporting_url": row["article_url"],
                    "title": row["title"],
                }
            )
            continue

        if row["future_negative"] and row["official_url"] not in future_examples_seen:
            excluded_examples["future_scheduled_examples"].append(
                {
                    "official_url": row["official_url"],
                    "title": row["title"],
                }
            )
            future_examples_seen.add(row["official_url"])

        if row["delay_only"] and row["official_url"] not in delay_examples_seen:
            excluded_examples["delay_only_examples"].append(
                {
                    "official_url": row["official_url"],
                    "title": row["title"],
                }
            )
            delay_examples_seen.add(row["official_url"])

    for exchange in exchanges:
        exchanges[exchange] = unique_by_official_url(exchanges[exchange])

    exchanges["bithumb"] = unique_by_official_url(
        exchanges["bithumb"] + MANUAL_CONFIRMED_BITHUMB_STRICT_ROWS
    )
    total_strict_count = len(exchanges["upbit"]) + len(exchanges["bithumb"])
    archive_scan = dict(scan_payload["archive_scan"])
    archive_scan["manual_bithumb_confirmed_count"] = len(
        MANUAL_CONFIRMED_BITHUMB_STRICT_ROWS
    )
    archive_scan["strict_immediate_stop_count"] = total_strict_count

    return {
        "generated_at": scan_payload["generated_at"],
        "strict_rule": "Count only notices whose readable body indicates the issue was already live and the service was suspended immediately at notice registration time or in direct present tense. Exclude notices that clearly schedule the stop for later.",
        "notes": [
            "This file is rebuilt from a page-1-through-page-60 Bloomingbit exchange-announcement archive scan.",
            "Official notice URLs are preserved when they were exposed on the mirrored article page.",
            "Rows in the strict set include chain issues, wallet/system issues, security issues, and project-risk notices only when the body text reads as an immediate current stop.",
            "Bithumb rows also include a manual confirmed supplement from official-domain search-indexed notice snippets because many mirrored Bithumb articles do not preserve the full body text.",
        ],
        "archive_scan": archive_scan,
        "exchanges": {
            "upbit": exchanges["upbit"],
            "bithumb": exchanges["bithumb"],
            "excluded_examples": excluded_examples,
        },
    }


def render_rows(rows: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for row in rows:
        rendered.append(
            "| {date} | {assets} | {scope} | {reason} | {basis} | [{id}]({url}) |".format(
                date=row["occurred_at_kst"] or "-",
                assets=", ".join(row["assets"]) if row["assets"] else "-",
                scope=row["scope"],
                reason=row["reason_type"] or "-",
                basis=row["strict_basis"],
                id=row["official_url"].split("=")[-1]
                if "upbit.com" in row["official_url"]
                else row["official_url"].rstrip("/").split("/")[-1],
                url=row["official_url"],
            )
        )
    return rendered


def build_markdown(payload: dict[str, Any]) -> str:
    upbit_rows = payload["exchanges"]["upbit"]
    bithumb_rows = payload["exchanges"]["bithumb"]
    scan = payload["archive_scan"]

    lines = [
        "# Exchange Immediate Issue Suspensions",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Archive scan pages: 1 through {scan['pages_scanned']}",
        f"- Archive rows scanned: {scan['total_rows']}",
        f"- Keyword candidates reviewed: {scan['reviewed_candidate_count']}",
        "- Strict rule: only count notices whose body reads as already-live trouble with immediate stop wording.",
        "- Excluded: scheduled upgrades/swaps/rebrandings, future-stop wording, and delay-only notices.",
        "",
        "## Result",
        "",
        f"- UPBIT: {len(upbit_rows)} strict immediate-stop cases confirmed",
        f"- BITHUMB: {len(bithumb_rows)} strict immediate-stop cases confirmed",
        "",
        "## UPBIT Strict Immediate Cases",
        "",
        "| Date (KST) | Assets | Scope | Trigger | Why It Counts | Official |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    lines.extend(render_rows(upbit_rows))

    lines.extend(
        [
            "",
            "## BITHUMB Strict Immediate Cases",
            "",
            "| Date (KST) | Assets | Scope | Trigger | Why It Counts | Official |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    lines.extend(render_rows(bithumb_rows) or ["| - | - | - | - | - | - |"])

    excluded = payload["exchanges"]["excluded_examples"]
    if excluded["future_scheduled_examples"]:
        lines.extend(
            [
                "",
                "## Excluded Scheduled Examples",
                "",
            ]
        )
        for item in excluded["future_scheduled_examples"][:10]:
            lines.append(f"- [{item['title']}]({item['official_url']})")

    if excluded["delay_only_examples"]:
        lines.extend(
            [
                "",
                "## Excluded Delay-Only Examples",
                "",
            ]
        )
        for item in excluded["delay_only_examples"][:10]:
            lines.append(f"- [{item['title']}]({item['official_url']})")

    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-output", type=Path, default=DEFAULT_SCAN_OUTPUT)
    parser.add_argument("--strict-output", type=Path, default=DEFAULT_STRICT_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    all_rows = crawl_archive(ARCHIVE_MAX_PAGE)
    keyword_candidates = unique_by_official_url(
        [row for row in all_rows if is_keyword_candidate(row)]
    )
    review_candidates_input = [
        row for row in keyword_candidates if needs_body_review(row)
    ]
    reviewed = review_candidates(review_candidates_input, workers=args.workers)

    scan_payload = build_scan_payload(
        all_rows,
        keyword_candidates,
        review_candidates_input,
        reviewed,
    )
    strict_payload = build_strict_payload(scan_payload)

    write_json(args.scan_output, scan_payload)
    write_json(args.strict_output, strict_payload)
    args.markdown_output.write_text(build_markdown(strict_payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "scan_output": str(args.scan_output),
                "strict_output": str(args.strict_output),
                "markdown_output": str(args.markdown_output),
                "archive_rows": scan_payload["archive_scan"]["total_rows"],
                "reviewed_candidates": scan_payload["archive_scan"][
                    "reviewed_candidate_count"
                ],
                "strict_upbit": len(strict_payload["exchanges"]["upbit"]),
                "strict_bithumb": len(strict_payload["exchanges"]["bithumb"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
