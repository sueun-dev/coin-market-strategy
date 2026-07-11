#!/usr/bin/env python3
"""Build per-case early-warning methods for Bithumb effective-immediate suspensions."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "config" / "bithumb_effective_immediate_suspensions.json"
JSON_OUTPUT = ROOT / "config" / "bithumb_effective_immediate_early_warning_methods.json"
MARKDOWN_OUTPUT = ROOT / "BITHUMB_EFFECTIVE_IMMEDIATE_EARLY_WARNING_METHODS.md"


TRIGGER_DEFAULTS = {
    "block_generation_stop": {
        "predictability": "high",
        "lead_time_expectation": "수초~수시간 전 선포착 가능",
        "watch_channels": [
            "메인넷 explorer의 최신 블록 시간, 블록 높이 증가 여부",
            "공식 status/X/Discord/Telegram의 장애 공지",
            "validator/RPC 운영자 채널과 빗썸 공지 피드, assetsstatus endpoint",
        ],
        "practical_rule_template": (
            "{context}에서 최신 블록 시간이 멈추거나 블록 간격이 비정상적으로 길어지고, "
            "공식 채널이나 validator 채널에서 장애 언급이 붙는 순간 `가두리 전조`로 승격했어야 한다."
        ),
        "hard_limit": (
            "정확한 빗썸 중지 시각까지는 못 맞춰도, 체인 halt 자체는 거래소 공지보다 먼저 보이는 경우가 많다."
        ),
    },
    "network_issue": {
        "predictability": "high",
        "lead_time_expectation": "수초~수시간 전 선포착 가능",
        "watch_channels": [
            "공식 explorer/RPC health, block lag, transaction failure rate",
            "공식 status/X/Discord/Telegram의 incident 공지",
            "빗썸 공지 피드와 assetsstatus endpoint",
        ],
        "practical_rule_template": (
            "{context}의 explorer 지연, RPC 오류, 공식 incident 공지가 동시에 나오면 "
            "`빗썸 입출금 중단 가능성 높음`으로 봤어야 한다."
        ),
        "hard_limit": (
            "네트워크 이슈는 잡기 쉽지만, 거래소가 실제로 몇 분 뒤에 막을지는 거래소 정책에 따라 달라진다."
        ),
    },
    "node_sync_issue": {
        "predictability": "high",
        "lead_time_expectation": "수분 전 선포착 가능",
        "watch_channels": [
            "공식 explorer와 공개 RPC의 sync lag",
            "노드 운영자/validator 공지",
            "빗썸 공지 피드와 assetsstatus endpoint",
        ],
        "practical_rule_template": (
            "{context} 노드 sync lag가 쌓이면 거래소 지갑도 곧 막힐 확률이 높으므로 "
            "공식 status와 explorer를 같이 봤어야 한다."
        ),
        "hard_limit": (
            "외부에서 노드 sync 문제를 볼 수 있어도, 거래소가 실제 중지 버튼을 누르는 시점은 별도다."
        ),
    },
    "security_issue": {
        "predictability": "medium",
        "lead_time_expectation": "수분~수시간 전 부분 선포착 가능",
        "watch_channels": [
            "프로젝트 공식 X/Discord/GitHub 보안 공지",
            "온체인 exploit alert, treasury/bridge 대량 이동 알림",
            "거래유의종목/유의촉구 공지와 빗썸 공지 피드",
        ],
        "practical_rule_template": (
            "{context} 보안 사고는 체인 halt보다 프로젝트/보안 채널이 먼저 반응하므로 "
            "exploit 알림과 공식 보안 공지를 가장 먼저 봤어야 한다."
        ),
        "hard_limit": (
            "보안 이슈는 거래소 내부 판단이 섞이므로 exact stop time을 미리 맞히는 것은 어렵다."
        ),
    },
    "wallet_system_check": {
        "predictability": "low",
        "lead_time_expectation": "사전 예고 거의 불가, 공지와 동시 포착",
        "watch_channels": [
            "빗썸 공지 피드",
            "빗썸 assetsstatus endpoint",
            "동일 자산의 반복 점검 패턴과 재개 공지 이력",
        ],
        "practical_rule_template": (
            "{context}는 체인 문제라기보다 거래소 내부 지갑 점검이어서 "
            "외부 체인 모니터링만으로는 미리 알기 어렵고, 빗썸 자체 신호를 가장 빠르게 읽어야 한다."
        ),
        "hard_limit": (
            "거래소 내부 월렛 점검은 공개 체인 데이터로 사전 포착하기 거의 불가능하다."
        ),
    },
}


CASE_OVERRIDES = {
    "1652530": {
        "context": "Drift 프로토콜과 Solana 생태계",
        "case_note": "체인 halt가 아니라 보안 이슈이므로 프로젝트 보안 채널과 exploit 알림이 핵심이다.",
    },
    "1652398": {
        "context": "peaq 메인넷",
        "case_note": "peaq 체인 블록 생성 정지 여부를 explorer와 validator 채널에서 먼저 잡았어야 한다.",
    },
    "1652352": {
        "context": "WAX 자산의 빗썸 지갑 경로",
        "case_note": "체인 문제보다 빗썸 내부 wallet system check 성격이 강해서 거래소 신호 의존도가 높다.",
    },
    "1652147": {
        "context": "0G 메인넷",
        "case_note": "explorer 최신 블록 시간과 공식 장애 공지를 보면 notice 이전에 이상 징후를 잡을 수 있는 유형이다.",
    },
    "1652079": {
        "context": "Flow 네트워크 출금 경로",
        "case_note": "입출금 전체가 아니라 출금만 막혔어도 근본 원인은 Flow 체인 측 문제라 chain-side 감시가 유효했다.",
    },
    "1652078": {
        "context": "Pocket Network",
        "case_note": "블록 생성 중단형이라 explorer halt와 validator 채널이 가장 중요한 선행 지표다.",
    },
    "1652002": {
        "context": "REI Network",
        "case_note": "REI explorer/RPC sync와 공식 X·Discord를 같이 봤어야 하는 전형적 halt 케이스다.",
    },
    "1651944": {
        "context": "Vana 메인넷",
        "case_note": "노드 sync lag가 핵심이므로 공개 RPC와 explorer의 head lag를 봤어야 한다.",
    },
    "1651736": {
        "context": "USDT의 Tron 출금 경로",
        "case_note": "TRON 전체 장애가 아니라 빗썸 지갑 점검 경로라 사실상 빗썸 notice/assetsstatus가 최초 신호다.",
    },
    "1651542": {
        "context": "USDT의 Tron 출금 경로",
        "case_note": "같은 유형의 재발 사례라 `USDT-Tron wallet check 반복` 자체는 패턴으로 학습할 수 있었지만 사전 확정은 어렵다.",
    },
    "1651445": {
        "context": "Starknet",
        "case_note": "Starknet sequencer/status와 explorer 최신 블록 시간을 같이 봤어야 했다.",
    },
    "1650998": {
        "context": "DIS 프로젝트 네트워크 경로",
        "case_note": "프로젝트 네트워크 halt 여부와 공식 채널 incident를 먼저 감시했어야 하는 유형이다.",
    },
    "1650802": {
        "context": "Cardano",
        "case_note": "Cardano tip lag, explorer head, stake pool 운영자 채널로 조기 감지가 가능했던 사례다.",
    },
    "1650517": {
        "context": "Berachain",
        "case_note": "Berachain explorer와 validator 채널을 동시에 보면 halt를 빠르게 볼 수 있는 유형이다.",
    },
    "1650288": {
        "context": "dYdX Chain",
        "case_note": "dYdX chain block halt는 체인 explorer와 validator 운영 채널에서 먼저 확인 가능한 편이다.",
    },
    "1650017": {
        "context": "ADD 자산의 빗썸 출금 지갑 경로",
        "case_note": "wallet system check라 외부 체인 모니터링보다 빗썸 자체 상태 감시가 핵심이다.",
    },
    "1649774": {
        "context": "Starknet",
        "case_note": "Starknet 재발 사례라 `동일 체인 반복 장애` 자체를 prior risk로 높게 잡았어야 했다.",
    },
    "1649671": {
        "context": "Zircuit",
        "case_note": "Zircuit explorer block lag와 status 채널을 보면 notice 전에 이상 징후를 잡을 수 있는 유형이다.",
    },
    "1649062": {
        "context": "Flare",
        "case_note": "Flare explorer, validator, status 계열 신호가 가장 중요한 선행 정보다.",
    },
    "1648710": {
        "context": "REI Network",
        "case_note": "REI 반복 장애 사례라 `재발 체인` 버킷에 올려두는 것이 맞았다.",
    },
    "1648132": {
        "context": "Cosmos Hub",
        "case_note": "Cosmos Hub는 explorer, Mintscan, validator 공지, forum까지 같이 봐야 선포착 확률이 높다.",
    },
    "1647038": {
        "context": "Flow",
        "case_note": "Flow 반복 사례라 network halt 재발 위험 체인으로 분류했어야 했다.",
    },
    "1646858": {
        "context": "IoTeX",
        "case_note": "IoTeX explorer, status, validator 채널이 조기 포착 포인트다.",
    },
    "1646423": {
        "context": "Zilliqa",
        "case_note": "Zilliqa explorer, official status, validator 채널에서 halt를 먼저 잡을 수 있었다.",
    },
    "1645260": {
        "context": "Stacks; ALEX는 STX 체인 의존",
        "case_note": "ALEX 자체보다 STX 메인넷 halt를 먼저 감시했어야 했다.",
    },
    "1645244": {
        "context": "Sui; LWA는 Sui 체인 의존",
        "case_note": "LWA 자체보다 Sui 네트워크 블록 생성 중단을 감시해야 했다.",
    },
    "1645183": {
        "context": "ZetaChain",
        "case_note": "네트워크 이슈형이라 ZetaScan, validator, status 공지가 선행 지표다.",
    },
    "1645123": {
        "context": "Terra 2.0",
        "case_note": "Terra Finder와 validator 운영 채널에서 네트워크 이상을 먼저 볼 수 있었다.",
    },
    "1645109": {
        "context": "Zilliqa",
        "case_note": "같은 체인 재발 사례라 ZIL은 반복 감시 우선순위가 높았어야 한다.",
    },
}


def build_case(row: dict) -> dict:
    notice_id = row["official_url"].rstrip("/").split("/")[-1]
    trigger = row["trigger_type"]
    defaults = TRIGGER_DEFAULTS[trigger]
    override = CASE_OVERRIDES[notice_id]
    return {
        "notice_id": notice_id,
        "official_url": row["official_url"],
        "notice_published_at_kst": row["notice_published_at_kst"],
        "asset_scope": row["asset_scope"],
        "scope": row["scope"],
        "trigger_type": trigger,
        "delta_label": row["delta_label"],
        "predictability": defaults["predictability"],
        "lead_time_expectation": defaults["lead_time_expectation"],
        "context": override["context"],
        "watch_channels": defaults["watch_channels"],
        "practical_prewarning_rule": defaults["practical_rule_template"].format(
            context=override["context"]
        ),
        "case_note": override["case_note"],
        "hard_limit": defaults["hard_limit"],
    }


def build_payload(input_rows: list[dict]) -> dict:
    cases = [build_case(row) for row in input_rows]
    counts = Counter(case["predictability"] for case in cases)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_file": INPUT_PATH.relative_to(ROOT).as_posix(),
        "summary": {
            "total_cases": len(cases),
            "high": counts["high"],
            "medium": counts["medium"],
            "low": counts["low"],
        },
        "legend": {
            "high": "체인/네트워크 외부 신호만으로도 notice 이전 또는 same-minute 선포착이 가능한 유형",
            "medium": "부분 선포착은 가능하지만 거래소 stop timing까지는 미리 확정하기 어려운 유형",
            "low": "거래소 내부 지갑/월렛 점검 성격이라 외부 체인 데이터만으로는 사실상 사전 불가 유형",
        },
        "cases": cases,
    }


def build_markdown(payload: dict) -> str:
    lines = [
        "# Bithumb Effective Immediate Early Warning Methods",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Source file: `{payload['source_file']}`",
        f"- Total cases: {payload['summary']['total_cases']}",
        f"- High pre-detectability: {payload['summary']['high']}",
        f"- Medium pre-detectability: {payload['summary']['medium']}",
        f"- Low pre-detectability: {payload['summary']['low']}",
        "",
        "## Reading Guide",
        "",
        f"- `high`: {payload['legend']['high']}",
        f"- `medium`: {payload['legend']['medium']}",
        f"- `low`: {payload['legend']['low']}",
        "",
        "## Case Table",
        "",
        "| Notice | Time (KST) | Asset Scope | Trigger | Pre-Knowability | Lead Time |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for case in payload["cases"]:
        lines.append(
            "| [{notice_id}]({url}) | {time} | {asset} | {trigger} | {predictability} | {lead} |".format(
                notice_id=case["notice_id"],
                url=case["official_url"],
                time=case["notice_published_at_kst"],
                asset=case["asset_scope"],
                trigger=case["trigger_type"],
                predictability=case["predictability"],
                lead=case["lead_time_expectation"],
            )
        )

    lines.extend(["", "## Case By Case", ""])

    for case in payload["cases"]:
        lines.extend(
            [
                f"### {case['notice_id']} {case['asset_scope']}",
                "",
                f"- 사전 인지 가능도: `{case['predictability']}`",
                f"- 실제 맥락: {case['context']}",
                f"- 왜 이렇게 봤는가: {case['case_note']}",
                f"- 기대 가능한 선행 시간: {case['lead_time_expectation']}",
                f"- 실전 룰: {case['practical_prewarning_rule']}",
                "- 미리 봤어야 할 채널:",
            ]
        )
        for item in case["watch_channels"]:
            lines.append(f"  - {item}")
        lines.extend(
            [
                f"- 한계: {case['hard_limit']}",
                f"- 원문: [{case['notice_id']}]({case['official_url']})",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    input_payload = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    payload = build_payload(input_payload["rows"])
    JSON_OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_OUTPUT.write_text(build_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "json_output": str(JSON_OUTPUT),
                "markdown_output": str(MARKDOWN_OUTPUT),
                "cases": payload["summary"]["total_cases"],
                "high": payload["summary"]["high"],
                "medium": payload["summary"]["medium"],
                "low": payload["summary"]["low"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
