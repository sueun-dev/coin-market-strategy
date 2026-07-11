#!/usr/bin/env python3
"""Build a focused watchlist for high-predictability Bithumb cases."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_JSON = ROOT / "config" / "bithumb_immediate_suspensions_master.json"
OUTPUT_JSON = ROOT / "config" / "bithumb_high_predictability_watchlist.json"
OUTPUT_MD = ROOT / "BITHUMB_HIGH_PREDICTABILITY_WATCHLIST.md"


COMMON_PATTERNS = {
    "block_generation_stop": {
        "signal": "explorer 최신 블록 시간 정지, 블록 높이 증가 멈춤, validator/RPC 채널 장애 언급",
        "action": "블록 생성 멈춤과 공식 incident 언급이 동시에 보이면 즉시 `빗썸 입출금 중단 가능성 높음`으로 승격",
    },
    "network_issue": {
        "signal": "explorer 지연, RPC 에러율 증가, tx fail 증가, 공식 status/X/Discord incident 공지",
        "action": "RPC health 악화와 공식 incident 신호가 붙는 순간 바로 경보",
    },
}


def load_payload() -> dict:
    return json.loads(SOURCE_JSON.read_text())


def build_payload() -> dict:
    source = load_payload()
    rows = [case for case in source["cases"] if case["predictability"] == "high"]
    trigger_counts = Counter(row["trigger_type"] for row in rows)
    source_counts = Counter(row["source_coverage"] for row in rows)

    grouped_assets: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        grouped_assets[row["trigger_type"]].append(row["asset_scope"])

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": SOURCE_JSON.relative_to(ROOT).as_posix(),
        "summary": {
            "total_cases": len(rows),
            "trigger_counts": dict(trigger_counts),
            "source_coverage": dict(source_counts),
        },
        "common_patterns": COMMON_PATTERNS,
        "cases": rows,
    }


def build_markdown(payload: dict) -> str:
    lines = [
        "# Bithumb High Predictability Watchlist",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Source file: [`{payload['source_file']}`]({payload['source_file']})",
        f"- Total high cases: {payload['summary']['total_cases']}",
        (
            "- Trigger counts: "
            + ", ".join(
                f"{trigger} {count}"
                for trigger, count in sorted(
                    payload["summary"]["trigger_counts"].items()
                )
            )
        ),
        "",
        "## How To Catch",
        "",
    ]

    for trigger, info in payload["common_patterns"].items():
        lines.extend(
            [
                f"### {trigger}",
                "",
                f"- First signal: {info['signal']}",
                f"- Action rule: {info['action']}",
                "",
            ]
        )

    lines.extend(
        [
            "## High Cases",
            "",
            "| Notice | Published (KST) | Assets | Trigger | Delta | How To Catch | Official |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in payload["cases"]:
        lines.append(
            f"| {row['notice_id']} | {row['published_at_kst']} | {row['asset_scope']} | "
            f"{row['trigger_type']} | {row['delta_label'] or '-'} | "
            f"{row['practical_prewarning_rule']} | [link]({row['official_url']}) |"
        )

    lines.extend(["", "## Case Notes", ""])
    for row in payload["cases"]:
        lines.extend(
            [
                f"### {row['notice_id']} {row['asset_scope']}",
                "",
                f"- Official: {row['official_url']}",
                f"- Published: {row['published_at_kst']}",
                f"- Trigger: `{row['trigger_type']}`",
                f"- Scope: `{row['scope']}`",
                f"- Source coverage: `{row['source_coverage']}`",
                f"- Classification: `{row['classification']}`",
                f"- Delta: `{row['delta_label'] or '-'}`",
                f"- Expected lead time: {row['lead_time_expectation']}",
                f"- Context: {row['context']}",
                f"- Watch channels: {'; '.join(row['watch_channels'])}",
                f"- How to catch: {row['practical_prewarning_rule']}",
                f"- Why high: {row['case_note']}",
                f"- Hard limit: {row['hard_limit']}",
                "",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    OUTPUT_MD.write_text(build_markdown(payload))
    print(f"[done] high_cases={payload['summary']['total_cases']} -> {OUTPUT_MD}")


if __name__ == "__main__":
    main()
