#!/usr/bin/env python3
"""Build an expanded Bithumb notice-posted immediate suspension dataset.

This expands beyond exact same-minute stop timestamps and also captures notices
that, in practice, suspend immediately upon notice publication but do not
publish a separate stop timestamp in the body.
"""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_JSON = ROOT / "config" / "bithumb_notice_posted_immediate_suspensions.json"
OUTPUT_MD = ROOT / "BITHUMB_NOTICE_POSTED_IMMEDIATE_SUSPENSIONS.md"
LIST_URL = "https://r.jina.ai/http://feed.bithumb.com/notice?page={page}"
NOTICE_URL = "https://r.jina.ai/http://feed.bithumb.com/notice/{notice_id}"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36"
)
MAX_PAGES = 80
MAX_WORKERS = 2
EXPLICIT_THRESHOLD_SECONDS = 600
FETCH_RETRIES = 6
RETRY_SLEEP_SECONDS = 2.0

LIST_ITEM_PATTERN = re.compile(
    r"^\*\s+\[(?P<label>.+?)\]\(http://feed\.bithumb\.com/notice/(?P<notice_id>\d+)\)$"
)
LIST_LABEL_PATTERN = re.compile(
    r"^(?P<category>거래유의/거래지원종료|거래유의|거래지원종료|안내|입출금|업데이트|이벤트|점검|공시|마켓 추가)\s+"
    r"(?P<title>.+?)(?P<listed_date>20\d{2}\.\d{2}\.\d{2})$"
)
PUBLISHED_AT_PATTERN = re.compile(
    r"(?:^|\n)(20\d{2}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:\n|$)"
)
STOP_AT_PATTERN = re.compile(
    r"(?:입출금|출금|입금)(?: 서비스| 지원)? (?:중지|중단) 시점.*?"
    r"(\d{4})\.(\d{2})\.(\d{2})\([^)]*\)\s*(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?",
    re.S,
)
TITLE_SUSPENSION_KEYWORDS = (
    "입출금 일시 중단 안내",
    "입출금 일시 중지 안내",
    "출금 일시 중단 안내",
    "출금 일시 중지 안내",
    "입금 일시 중단 안내",
    "입금 일시 중지 안내",
)
TRIGGER_PATTERNS: dict[str, tuple[str, ...]] = {
    "security_issue": ("보안 문제", "보안 이슈", "보안 취약점", "보안 문제 의심 정황"),
    "block_generation_stop": ("블록 생성 중단", "블록생성 중단"),
    "network_issue": ("네트워크 이슈", "메인넷 네트워크 이슈"),
    "node_sync_issue": ("노드 동기화 문제",),
    "wallet_system_check": ("월렛 시스템 점검", "내부 월렛 시스템 점검"),
    "withdrawal_surge": ("출금량 증가", "출금 요청량 증가"),
    "bridge_issue": ("브릿지",),
}
IMPLICIT_IMMEDIATE_PATTERNS = (
    re.compile(
        r"(?:안정성 확보 시점까지|이로 인해|또한).{0,140}?"
        r"(?:입출금|출금|입금)(?: 서비스| 지원)?가 (?:일시 )?(?:중단|중지) ?될 예정입니다",
        re.S,
    ),
    re.compile(
        r"(?:안정성 확보 시점까지|이로 인해|또한).{0,140}?"
        r"(?:입출금|출금|입금)(?: 서비스| 지원)?를 (?:일시 )?(?:중단|중지) ?할 예정입니다",
        re.S,
    ),
)
MANUAL_RECOVERY_ROWS = [
    {
        "notice_id": "1652014",
        "official_url": "https://feed.bithumb.com/notice/1652014",
        "page": None,
        "category": "입출금",
        "title": "테더(USDT) Kaia 네트워크 출금 일시 중단 안내",
        "listed_date": "2026.02.14",
        "published_at_kst": "2026-02-14 09:20:34",
        "classification": "explicit_near_immediate",
        "trigger_type": "wallet_system_check",
        "stated_stop_at_kst": "2026-02-14 09:20:00",
        "delta_seconds": -34,
        "delta_label": "-34s",
        "implicit_phrase": None,
        "confidence": "high",
        "inclusion_reason": "공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류",
        "excerpt": "테더(USDT)지갑 시스템 점검에 따라 안정적인 서비스 제공을 위해 아래와 같이 출금이 일시 중지될 예정이며, 출금 중지 시점은 2026.02.14(토) 오전 9시 20분 예정으로 공지 시각과 사실상 동일하다.",
    },
    {
        "notice_id": "1650635",
        "official_url": "https://feed.bithumb.com/notice/1650635",
        "page": None,
        "category": "입출금",
        "title": "멀린 체인(MERL) 입출금 일시 중지 안내 (11/10 재개)",
        "listed_date": "2025.11.07",
        "published_at_kst": "2025-11-07 21:35:30",
        "classification": "explicit_near_immediate",
        "trigger_type": "unknown",
        "stated_stop_at_kst": "2025-11-07 21:35:00",
        "delta_seconds": -30,
        "delta_label": "-30s",
        "implicit_phrase": None,
        "confidence": "high",
        "inclusion_reason": "공식 원문이 `오후 21시 35분`처럼 24시간 표기와 PM 표기를 섞어 썼지만, 정규화하면 공지 시각과 30초 차이의 near-immediate 케이스",
        "excerpt": "멀린 체인(MERL) 네트워크 업그레이드 지원에 따라 입출금이 일시 중지될 예정이며, 본문 중지 시점은 2025.11.07(금) 오후 21시 35분 예정으로 공지 시각과 사실상 동일하다.",
    },
    {
        "notice_id": "1648448",
        "official_url": "https://feed.bithumb.com/notice/1648448",
        "page": None,
        "category": "입출금",
        "title": "레이(REI) 입출금 일시 중지 안내 (5/20 재개)",
        "listed_date": "2025.05.20",
        "published_at_kst": "2025-05-20 19:00:12",
        "classification": "explicit_near_immediate",
        "trigger_type": "block_generation_stop",
        "stated_stop_at_kst": "2025-05-20 19:00:00",
        "delta_seconds": -12,
        "delta_label": "-12s",
        "implicit_phrase": None,
        "confidence": "high",
        "inclusion_reason": "공식 원문이 `오후 19시 00분`처럼 표기했지만, 정규화하면 공지 시각과 12초 차이의 near-immediate 케이스",
        "excerpt": "레이(REI) 네트워크 이슈로 인해 일시적으로 입출금 서비스가 중지될 예정이며, 본문 중지 시점은 2025.05.20(화) 오후 19시 00분 예정으로 공지 시각과 사실상 동일하다.",
    },
]


def fetch_text(url: str) -> str:
    last_error: Exception | None = None
    for attempt in range(1, FETCH_RETRIES + 1):
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=60) as response:
                return response.read().decode("utf-8", "ignore")
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == FETCH_RETRIES:
                raise
        except Exception as exc:  # pragma: no cover - network variability
            last_error = exc
            if attempt == FETCH_RETRIES:
                raise
        time.sleep(RETRY_SLEEP_SECONDS * attempt)
    assert last_error is not None
    raise last_error


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def fetch_list_page(page: int) -> list[dict[str, Any]]:
    text = fetch_text(LIST_URL.format(page=page))
    rows: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        match = LIST_ITEM_PATTERN.match(line)
        if not match:
            continue
        label_match = LIST_LABEL_PATTERN.match(match.group("label"))
        if not label_match:
            continue
        title = normalize_spaces(label_match.group("title"))
        if not any(keyword in title for keyword in TITLE_SUSPENSION_KEYWORDS):
            continue
        if title_implies_future_start(title):
            continue
        rows.append(
            {
                "page": page,
                "notice_id": match.group("notice_id"),
                "official_url": f"https://feed.bithumb.com/notice/{match.group('notice_id')}",
                "category": label_match.group("category"),
                "title": title,
                "listed_date": label_match.group("listed_date"),
            }
        )
    return rows


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
    # Some Bithumb notices mix AM/PM markers with 24-hour values like "오후 21시".
    # When the hour is already 13 or greater, trust the numeric hour as-is.
    if hour <= 12:
        if ampm == "오후" and hour != 12:
            hour += 12
        if ampm == "오전" and hour == 12:
            hour = 0
    return f"{year}-{month}-{day} {hour:02d}:{minute:02d}:00"


def body_for_original_notice(text: str) -> str:
    if "* * *" in text:
        return text.split("* * *")[-1].strip()
    return text.strip()


def detect_trigger(text: str) -> str | None:
    for trigger, keywords in TRIGGER_PATTERNS.items():
        if any(keyword in text for keyword in keywords):
            return trigger
    return None


def title_implies_future_start(title: str) -> bool:
    return bool(re.search(r"\([^)]+(?:오전|오후)[^)]+~\)", title))


def implicit_immediate_match(body_text: str) -> str | None:
    for pattern in IMPLICIT_IMMEDIATE_PATTERNS:
        match = pattern.search(body_text)
        if match:
            return normalize_spaces(match.group(0))
    return None


def build_row(candidate: dict[str, Any]) -> dict[str, Any] | None:
    notice_text = fetch_text(NOTICE_URL.format(notice_id=candidate["notice_id"]))
    published_at = parse_published_at(notice_text)
    if not published_at:
        return None

    original_body = body_for_original_notice(notice_text)
    stop_at = parse_stop_at(original_body)
    trigger = detect_trigger(original_body) or detect_trigger(candidate["title"])
    implicit_phrase = implicit_immediate_match(original_body)

    classification: str | None = None
    delta_seconds: int | None = None
    delta_label: str | None = None
    inclusion_reason: str | None = None
    confidence = "medium"

    published_dt = datetime.strptime(published_at, "%Y-%m-%d %H:%M:%S")

    if stop_at:
        stop_dt = datetime.strptime(stop_at, "%Y-%m-%d %H:%M:%S")
        delta_seconds = int((stop_dt - published_dt).total_seconds())
        delta_label = f"{delta_seconds:+d}s" if delta_seconds else "0s"
        if abs(delta_seconds) <= EXPLICIT_THRESHOLD_SECONDS:
            classification = "explicit_near_immediate"
            inclusion_reason = "공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내여서 사실상 공지 직후 중단으로 분류"
            confidence = "high"
    elif implicit_phrase and not title_implies_future_start(candidate["title"]):
        classification = "implicit_on_notice"
        inclusion_reason = "원문 본문이 별도 미래 중지 시각 없이 공지와 함께 즉시형/무기한 중단 문구를 사용"
        confidence = "medium"

    if classification is None:
        return None

    excerpt_lines = [
        line.strip() for line in original_body.splitlines() if line.strip()
    ]
    excerpt = normalize_spaces(" ".join(excerpt_lines[:8]))[:280]

    return {
        "notice_id": candidate["notice_id"],
        "official_url": candidate["official_url"],
        "page": candidate["page"],
        "category": candidate["category"],
        "title": candidate["title"],
        "listed_date": candidate["listed_date"],
        "published_at_kst": published_at,
        "classification": classification,
        "trigger_type": trigger or "unknown",
        "stated_stop_at_kst": stop_at,
        "delta_seconds": delta_seconds,
        "delta_label": delta_label,
        "implicit_phrase": implicit_phrase,
        "confidence": confidence,
        "inclusion_reason": inclusion_reason,
        "excerpt": excerpt,
    }


def crawl_candidates(max_pages: int) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    empty_streak = 0
    last_page = 0
    for page in range(1, max_pages + 1):
        page_rows = fetch_list_page(page)
        last_page = page
        if not page_rows:
            empty_streak += 1
        else:
            empty_streak = 0
            rows.extend(page_rows)
        print(
            f"[list] page={page} candidates={len(page_rows)} total={len(rows)}",
            flush=True,
        )
        if empty_streak >= 3:
            break
    deduped: dict[str, dict[str, Any]] = {}
    for row in rows:
        deduped[row["notice_id"]] = row
    return list(deduped.values()), last_page


def build_payload(
    rows: list[dict[str, Any]], diagnostics: dict[str, Any]
) -> dict[str, Any]:
    explicit = sum(
        1 for row in rows if row["classification"] == "explicit_near_immediate"
    )
    implicit = sum(1 for row in rows if row["classification"] == "implicit_on_notice")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "exchange": "bithumb",
        "definition": (
            "Include Bithumb notices that function as notice-posted immediate suspensions. "
            "This includes explicit same-minute/near-immediate stop timestamps and implicit "
            "cases where the official notice itself is the first public suspension signal with "
            "no separate future stop timestamp."
        ),
        "diagnostics": diagnostics,
        "summary": {
            "total_rows": len(rows),
            "explicit_near_immediate": explicit,
            "implicit_on_notice": implicit,
        },
        "rows": rows,
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Bithumb Notice-Posted Immediate Suspensions",
        "",
        f"- Generated at: {payload['generated_at']}",
        "- Exchange: BITHUMB",
        f"- Total rows: {payload['summary']['total_rows']}",
        f"- Explicit near-immediate: {payload['summary']['explicit_near_immediate']}",
        f"- Implicit on-notice: {payload['summary']['implicit_on_notice']}",
        f"- List pages scanned: {payload['diagnostics']['pages_scanned']}",
        f"- Candidate notices reviewed: {payload['diagnostics']['candidate_notices']}",
        "",
        "| Notice | Published (KST) | Classification | Trigger | Stop (KST) | Delta | Confidence |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in payload["rows"]:
        stop_at = row["stated_stop_at_kst"] or "-"
        delta = row["delta_label"] or "-"
        lines.append(
            f"| [{row['notice_id']}]({row['official_url']}) | {row['published_at_kst']} | "
            f"{row['classification']} | {row['trigger_type']} | {stop_at} | {delta} | {row['confidence']} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `explicit_near_immediate`: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내로 붙어 있는 케이스",
            "- `implicit_on_notice`: 별도 미래 중지 시각 없이 공지 본문 자체가 첫 중단 신호로 읽히는 케이스",
            "",
            "## Case Notes",
            "",
        ]
    )

    for row in payload["rows"]:
        stop_at = row["stated_stop_at_kst"] or "-"
        delta = row["delta_label"] or "-"
        lines.extend(
            [
                f"### {row['notice_id']} {row['title']}",
                "",
                f"- Published: {row['published_at_kst']}",
                f"- Classification: `{row['classification']}`",
                f"- Trigger: `{row['trigger_type']}`",
                f"- Stop at: `{stop_at}`",
                f"- Delta: `{delta}`",
                f"- Confidence: `{row['confidence']}`",
                f"- Inclusion reason: {row['inclusion_reason']}",
                f"- Evidence phrase: {row['implicit_phrase'] or row['excerpt']}",
                f"- Official: {row['official_url']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    candidates, pages_scanned = crawl_candidates(MAX_PAGES)
    print(f"[review] candidates={len(candidates)}", flush=True)

    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(build_row, row): row for row in candidates}
        reviewed = 0
        for future in as_completed(futures):
            source = futures[future]
            reviewed += 1
            try:
                row = future.result()
            except Exception as exc:
                print(f"[warn] notice={source['notice_id']} error={exc}", flush=True)
                continue
            if row is not None:
                rows.append(row)
                print(
                    f"[match] notice={row['notice_id']} class={row['classification']} total={len(rows)}",
                    flush=True,
                )
            elif reviewed % 25 == 0:
                print(f"[reviewed] {reviewed}/{len(candidates)}", flush=True)

    row_by_notice_id = {row["notice_id"]: row for row in rows}
    for recovery_row in MANUAL_RECOVERY_ROWS:
        row_by_notice_id[recovery_row["notice_id"]] = recovery_row
    rows = list(row_by_notice_id.values())
    rows.sort(key=lambda row: (row["published_at_kst"], row["notice_id"]), reverse=True)
    diagnostics = {
        "pages_scanned": pages_scanned,
        "candidate_notices": len(candidates),
        "matched_rows": len(rows),
        "manual_recovery_rows": len(MANUAL_RECOVERY_ROWS),
    }
    payload = build_payload(rows, diagnostics)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUTPUT_MD.write_text(build_markdown(payload))
    print(f"[done] rows={len(rows)} -> {OUTPUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
