#!/usr/bin/env python3
"""Build exchange-specific single-chain asset listings for Upbit and Bithumb."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = ROOT / "config" / "exchange_asset_cage_requirements.json"
DEFAULT_JSON_OUTPUT = ROOT / "config" / "exchange_single_chain_assets.json"
DEFAULT_MARKDOWN_OUTPUT = ROOT / "EXCHANGE_SINGLE_CHAIN_ASSETS.md"


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def normalize_single_chain_record(record: dict[str, Any]) -> dict[str, Any]:
    only_chain = record["required_closed_chains"][0]
    return {
        "ticker": record["ticker"],
        "english_names": record["english_names"],
        "markets": record["markets"],
        "only_chain": only_chain,
        "supported_networks": record["supported_networks"],
        "known_notice_hit_count": record["recent_official_notice_hits"][
            "total_hit_count"
        ],
    }


def build_exchange_section(records: list[dict[str, Any]]) -> dict[str, Any]:
    single_chain_assets = [
        normalize_single_chain_record(record)
        for record in sorted(records, key=lambda item: item["ticker"])
        if record["single_chain"]
    ]
    chain_counter = Counter(item["only_chain"] for item in single_chain_assets)
    return {
        "asset_count": len(single_chain_assets),
        "chain_count": len(chain_counter),
        "chain_counts": [
            {"chain": chain, "asset_count": asset_count}
            for chain, asset_count in sorted(
                chain_counter.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        "assets": single_chain_assets,
    }


def render_chain_counts(chain_counts: list[dict[str, Any]]) -> str:
    if not chain_counts:
        return "-"
    return ", ".join(
        f"{item['chain']}({item['asset_count']})" for item in chain_counts[:25]
    )


def build_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Exchange Single-Chain Assets",
        "",
        f"- Generated at: {payload['generated_at']}",
        "- Meaning: these are assets that require exactly one currently supported chain to close for a full exchange-level cage on that exchange.",
        "- Scope: separated by exchange. The same ticker can appear on both exchanges.",
        "",
        "## Summary",
        "",
    ]

    for exchange in ("upbit", "bithumb"):
        section = payload["exchanges"][exchange]
        lines.append(
            f"- {exchange.upper()}: {section['asset_count']} single-chain assets across {section['chain_count']} unique chains"
        )
        lines.append(
            f"- {exchange.upper()} top chain buckets: {render_chain_counts(section['chain_counts'])}"
        )

    for exchange in ("upbit", "bithumb"):
        section = payload["exchanges"][exchange]
        lines.extend(
            [
                "",
                f"## {exchange.upper()} Single-Chain Assets",
                "",
                "| Ticker | Only Chain | Markets | Known Notice Hits |",
                "| --- | --- | --- | --- |",
            ]
        )
        for asset in section["assets"]:
            lines.append(
                "| {ticker} | {chain} | {markets} | {hits} |".format(
                    ticker=asset["ticker"],
                    chain=asset["only_chain"],
                    markets=", ".join(asset["markets"]),
                    hits=asset["known_notice_hit_count"],
                )
            )

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    args = parser.parse_args()

    source_payload = load_json(args.input)
    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "generated_at": generated_at,
        "sources": {
            "exchange_asset_cage_requirements": Path(
                os.path.relpath(args.input.resolve(), ROOT.resolve())
            ).as_posix(),
        },
        "notes": [
            "single-chain means required_closed_chain_count == 1 on the specific exchange",
            "this output is exchange-scoped, not domestic-combined",
            "ordering is alphabetical by ticker",
        ],
        "exchanges": {
            exchange: build_exchange_section(
                source_payload["exchanges"][exchange]["assets"]
            )
            for exchange in ("upbit", "bithumb")
        },
    }

    dump_json(args.json_output, payload)
    args.markdown_output.write_text(build_markdown(payload), encoding="utf-8")

    print(
        json.dumps(
            {
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
                "upbit_single_chain_asset_count": payload["exchanges"]["upbit"][
                    "asset_count"
                ],
                "bithumb_single_chain_asset_count": payload["exchanges"]["bithumb"][
                    "asset_count"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
