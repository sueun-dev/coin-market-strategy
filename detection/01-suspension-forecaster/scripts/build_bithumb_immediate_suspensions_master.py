#!/usr/bin/env python3
"""Build one canonical Bithumb immediate-suspensions document."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
NOTICE_SCAN_JSON = ROOT / "config" / "bithumb_notice_posted_immediate_suspensions.json"
LEGACY_JSON = ROOT / "config" / "bithumb_effective_immediate_suspensions.json"
EARLY_WARNING_JSON = (
    ROOT / "config" / "bithumb_effective_immediate_early_warning_methods.json"
)
OUTPUT_JSON = ROOT / "config" / "bithumb_immediate_suspensions_master.json"
OUTPUT_MD = ROOT / "BITHUMB_IMMEDIATE_SUSPENSIONS_MASTER.md"

TICKER_PATTERN = re.compile(r"\(([A-Z0-9-]{1,15})\)")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def notice_id_from_url(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def derive_scope_from_title(title: str) -> str:
    has_deposit = "입금" in title or "입출금" in title
    has_withdraw = "출금" in title or "입출금" in title
    if has_deposit and has_withdraw:
        return "deposit_withdrawal"
    if has_withdraw:
        return "withdrawal_only"
    if has_deposit:
        return "deposit_only"
    return "unknown"


def derive_asset_scope(title: str) -> str:
    tickers = sorted(set(TICKER_PATTERN.findall(title)))
    if tickers:
        return ",".join(tickers)
    title = title.replace("[빗썸] ", "")
    for marker in ("입출금", "출금", "입금"):
        if marker in title:
            return normalize_spaces(title.split(marker, 1)[0])
    return normalize_spaces(title)


def default_early_warning(
    asset_scope: str, trigger_type: str, title: str
) -> dict[str, Any]:
    asset_label = asset_scope or derive_asset_scope(title)
    context = f"{asset_label} 관련 네트워크/프로젝트"
    if trigger_type in {"block_generation_stop", "network_issue", "node_sync_issue"}:
        return {
            "predictability": "high",
            "lead_time_expectation": "수초~수시간 전 선포착 가능",
            "context": context,
            "watch_channels": [
                "공식 explorer 최신 블록 시간, block lag, transaction failure",
                "공식 status/X/Discord/Telegram incident 공지",
                "빗썸 공지 피드와 assetsstatus endpoint",
            ],
            "practical_prewarning_rule": (
                f"{asset_label} 쪽 explorer 지연, 블록 생성 중단, 공식 incident 공지가 붙는 순간 "
                "`빗썸 입출금 중단 가능성 높음`으로 승격했어야 한다."
            ),
            "case_note": "체인/네트워크 자체 이상이 먼저 보이는 유형이라 외부 신호 선포착 가능성이 높다.",
            "hard_limit": "정확히 몇 분 뒤 빗썸이 막을지는 거래소 정책에 따라 달라진다.",
        }
    if trigger_type == "security_issue":
        return {
            "predictability": "medium",
            "lead_time_expectation": "수분~수시간 전 부분 선포착 가능",
            "context": context,
            "watch_channels": [
                "프로젝트 공식 X/Discord/GitHub 보안 공지",
                "on-chain exploit alert, treasury/bridge 대량 이동 알림",
                "빗썸 공지 피드와 거래유의/유의촉구 공지",
            ],
            "practical_prewarning_rule": (
                f"{asset_label} 관련 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하는 경우가 많아 "
                "exploit 알림과 공식 보안 채널을 먼저 봤어야 한다."
            ),
            "case_note": "보안 이슈는 외부 신호는 먼저 보일 수 있지만 거래소 stop timing까지 맞히긴 어렵다.",
            "hard_limit": "거래소 내부 리스크 판단이 개입돼 exact stop time 예측은 어렵다.",
        }
    if trigger_type == "wallet_system_check":
        return {
            "predictability": "low",
            "lead_time_expectation": "사전 예고 거의 불가, 공지와 동시 포착",
            "context": f"{asset_label}의 빗썸 지갑 경로",
            "watch_channels": [
                "빗썸 공지 피드",
                "빗썸 assetsstatus endpoint",
                "동일 자산의 반복 점검 패턴과 재개 공지 이력",
            ],
            "practical_prewarning_rule": (
                f"{asset_label} 쪽은 체인 외부 신호보다 거래소 내부 월렛 점검이 원인인 경우가 많아 "
                "빗썸 자체 신호를 가장 빠르게 읽어야 한다."
            ),
            "case_note": "외부 체인 데이터만으로는 사전 포착이 거의 불가능한 유형이다.",
            "hard_limit": "거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 어렵다.",
        }
    return {
        "predictability": "low",
        "lead_time_expectation": "공개 신호만으로는 제한적",
        "context": context,
        "watch_channels": [
            "빗썸 공지 피드",
            "빗썸 assetsstatus endpoint",
            "자산별 반복 중단 패턴과 프로젝트 공식 채널",
        ],
        "practical_prewarning_rule": (
            f"{asset_label} 케이스는 원인 정보가 제한적이어서 빗썸 자체 신호와 프로젝트 공식 채널을 같이 보는 보수적 접근이 필요하다."
        ),
        "case_note": "원인 정보가 덜 명확해 거래소 공지 의존도가 높은 유형이다.",
        "hard_limit": "원인 불명 케이스는 공지 이전 정밀 예측이 어렵다.",
    }


def build_master_rows() -> list[dict[str, Any]]:
    notice_scan = load_json(NOTICE_SCAN_JSON)
    legacy = load_json(LEGACY_JSON)
    early = load_json(EARLY_WARNING_JSON)

    notice_by_id = {row["notice_id"]: row for row in notice_scan["rows"]}
    legacy_by_id = {
        notice_id_from_url(row["official_url"]): row for row in legacy["rows"]
    }
    early_by_id = {case["notice_id"]: case for case in early["cases"]}

    all_ids = sorted(set(notice_by_id) | set(legacy_by_id))
    rows: list[dict[str, Any]] = []
    for notice_id in all_ids:
        notice_row = notice_by_id.get(notice_id)
        legacy_row = legacy_by_id.get(notice_id)
        early_row = early_by_id.get(notice_id)

        if notice_row and legacy_row:
            source_coverage = "both"
        elif notice_row:
            source_coverage = "notice_scan_only"
        else:
            source_coverage = "legacy_only"

        title = (
            notice_row["title"]
            if notice_row
            else legacy_row["title"].replace("[빗썸] ", "")
        )
        official_url = (
            notice_row["official_url"] if notice_row else legacy_row["official_url"]
        )
        published_at_kst = (
            notice_row["published_at_kst"]
            if notice_row
            else legacy_row["notice_published_at_kst"]
        )
        asset_scope = (
            early_row["asset_scope"]
            if early_row
            else legacy_row["asset_scope"]
            if legacy_row
            else derive_asset_scope(title)
        )
        scope = (
            early_row["scope"]
            if early_row
            else legacy_row["scope"]
            if legacy_row
            else derive_scope_from_title(title)
        )
        trigger_type = (
            notice_row["trigger_type"]
            if notice_row and notice_row.get("trigger_type")
            else legacy_row["trigger_type"]
            if legacy_row
            else "unknown"
        )
        classification = (
            notice_row["classification"] if notice_row else "legacy_effective_immediate"
        )
        stated_stop_at_kst = (
            notice_row["stated_stop_at_kst"]
            if notice_row
            else legacy_row["stated_stop_at_kst"]
        )
        delta_label = (
            notice_row["delta_label"] if notice_row else legacy_row["delta_label"]
        )
        inclusion_reason = (
            notice_row["inclusion_reason"]
            if notice_row
            else "기존 effective-immediate 작업본에서 공식 공지 원문 기준 same-minute/near-immediate로 수기 검증된 케이스"
        )
        evidence_phrase = (
            notice_row["implicit_phrase"] or notice_row["excerpt"]
            if notice_row
            else "기존 effective-immediate 작업본에 수기 검증된 원문 기반 케이스"
        )
        confidence = notice_row["confidence"] if notice_row else "medium"

        early_block = early_row or default_early_warning(
            asset_scope, trigger_type, title
        )
        rows.append(
            {
                "notice_id": notice_id,
                "official_url": official_url,
                "published_at_kst": published_at_kst,
                "title": title,
                "asset_scope": asset_scope,
                "scope": scope,
                "source_coverage": source_coverage,
                "classification": classification,
                "trigger_type": trigger_type,
                "stated_stop_at_kst": stated_stop_at_kst,
                "delta_label": delta_label,
                "confidence": confidence,
                "inclusion_reason": inclusion_reason,
                "evidence_phrase": evidence_phrase,
                "predictability": early_block["predictability"],
                "lead_time_expectation": early_block["lead_time_expectation"],
                "context": early_block["context"],
                "watch_channels": early_block["watch_channels"],
                "practical_prewarning_rule": early_block["practical_prewarning_rule"],
                "case_note": early_block["case_note"],
                "hard_limit": early_block["hard_limit"],
            }
        )

    rows.sort(key=lambda row: (row["published_at_kst"], row["notice_id"]), reverse=True)
    return rows


def build_payload(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_counts = Counter(row["source_coverage"] for row in rows)
    class_counts = Counter(row["classification"] for row in rows)
    predict_counts = Counter(row["predictability"] for row in rows)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "bithumb_immediate_suspensions_master",
        "methodology": {
            "merge_rule": "notice id 기준으로 dedupe 후 notice-scan 45건, legacy effective-immediate 29건, early-warning 메모를 단일 canonical set으로 병합",
            "official_list_reference": "https://feed.bithumb.com/notice",
            "source_files": [
                NOTICE_SCAN_JSON.relative_to(ROOT).as_posix(),
                LEGACY_JSON.relative_to(ROOT).as_posix(),
                EARLY_WARNING_JSON.relative_to(ROOT).as_posix(),
            ],
        },
        "summary": {
            "total_cases": len(rows),
            "source_coverage": dict(source_counts),
            "classification": dict(class_counts),
            "predictability": dict(predict_counts),
        },
        "cases": rows,
    }


def build_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Bithumb Immediate Suspensions Master",
        "",
        f"- Generated at: {payload['generated_at']}",
        "- Scope: 빗썸 `공지 직후 정지형` 관련 단일 기준 문서",
        f"- Total cases: {summary['total_cases']}",
        (
            "- Source coverage: "
            f"both {summary['source_coverage'].get('both', 0)}, "
            f"notice_scan_only {summary['source_coverage'].get('notice_scan_only', 0)}, "
            f"legacy_only {summary['source_coverage'].get('legacy_only', 0)}"
        ),
        (
            "- Classification: "
            f"explicit_near_immediate {summary['classification'].get('explicit_near_immediate', 0)}, "
            f"implicit_on_notice {summary['classification'].get('implicit_on_notice', 0)}, "
            f"legacy_effective_immediate {summary['classification'].get('legacy_effective_immediate', 0)}"
        ),
        (
            "- Predictability: "
            f"high {summary['predictability'].get('high', 0)}, "
            f"medium {summary['predictability'].get('medium', 0)}, "
            f"low {summary['predictability'].get('low', 0)}"
        ),
        "",
        "## Source Files",
        "",
        "- [bithumb_notice_posted_immediate_suspensions.json](config/bithumb_notice_posted_immediate_suspensions.json)",
        "- [bithumb_effective_immediate_suspensions.json](config/bithumb_effective_immediate_suspensions.json)",
        "- [bithumb_effective_immediate_early_warning_methods.json](config/bithumb_effective_immediate_early_warning_methods.json)",
        "",
        "## Reading Guide",
        "",
        "- `both`: 확장 notice-scan 세트와 기존 legacy 세트 양쪽에서 같이 잡힌 케이스",
        "- `notice_scan_only`: 공식 notice 목록 전수 스캔에서 새로 잡힌 케이스",
        "- `legacy_only`: 기존 수기 검증 세트에는 있었지만 현재 notice 목록 전수 스캔 범위 밖이라 legacy 근거로만 유지한 케이스",
        "- `explicit_near_immediate`: 공지 본문에 적힌 중지 시각이 공지 시각과 10분 이내",
        "- `implicit_on_notice`: 별도 중지 시각 없이 공지 자체가 첫 public stop 신호",
        "- `legacy_effective_immediate`: 기존 작업본에서 same-minute/near-immediate로 검증된 legacy 케이스",
        "",
        "## Master Table",
        "",
        "| Notice | Published (KST) | Assets | Scope | Source | Class | Trigger | Delta | Predictability | Official |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in payload["cases"]:
        lines.append(
            f"| {row['notice_id']} | {row['published_at_kst']} | {row['asset_scope']} | "
            f"{row['scope']} | {row['source_coverage']} | {row['classification']} | "
            f"{row['trigger_type']} | {row['delta_label'] or '-'} | {row['predictability']} | "
            f"[link]({row['official_url']}) |"
        )

    lines.extend(["", "## Case Notes", ""])
    for row in payload["cases"]:
        watch_channels = "; ".join(row["watch_channels"])
        lines.extend(
            [
                f"### {row['notice_id']} {row['title']}",
                "",
                f"- Official: {row['official_url']}",
                f"- Published: {row['published_at_kst']}",
                f"- Asset scope: `{row['asset_scope']}`",
                f"- Scope: `{row['scope']}`",
                f"- Source coverage: `{row['source_coverage']}`",
                f"- Classification: `{row['classification']}`",
                f"- Trigger: `{row['trigger_type']}`",
                f"- Stated stop: `{row['stated_stop_at_kst'] or '-'}`",
                f"- Delta: `{row['delta_label'] or '-'}`",
                f"- Confidence: `{row['confidence']}`",
                f"- Inclusion reason: {row['inclusion_reason']}",
                f"- Evidence phrase: {row['evidence_phrase']}",
                f"- Pre-detectability: `{row['predictability']}`",
                f"- Expected lead time: {row['lead_time_expectation']}",
                f"- Context: {row['context']}",
                f"- Watch channels: {watch_channels}",
                f"- Practical rule: {row['practical_prewarning_rule']}",
                f"- Case note: {row['case_note']}",
                f"- Hard limit: {row['hard_limit']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    rows = build_master_rows()
    payload = build_payload(rows)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUTPUT_MD.write_text(build_markdown(payload))
    print(f"[done] cases={len(rows)} -> {OUTPUT_MD}")


if __name__ == "__main__":
    main()
