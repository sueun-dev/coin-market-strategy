#!/usr/bin/env python3
"""Build per-asset full-cage requirements and priority rankings for Upbit/Bithumb."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MODULE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = MODULE_DIR / "config" / "exchange_asset_networks.json"
DEFAULT_REQUIREMENTS_OUTPUT = (
    MODULE_DIR / "config" / "exchange_asset_cage_requirements.json"
)
DEFAULT_RANKINGS_OUTPUT = MODULE_DIR / "config" / "exchange_cage_priority_rankings.json"
DEFAULT_MARKDOWN_OUTPUT = MODULE_DIR / "EXCHANGE_CAGE_REQUIREMENTS.md"

CHAIN_TICKER_ALIASES = {
    "KATANA": "KAT",
    "VAULTA": "A",
    "WLD_ETH": "WLDCHAIN",
}


# These are not meant to be a perfect full-archive reconstruction.
# They are the currently confirmed official notice examples that were directly
# observable from official Upbit/Bithumb notice pages or official-domain search
# results during this build window.
KNOWN_OFFICIAL_NOTICE_ASSET_URLS = {
    "upbit": {
        "AKT": [
            "https://upbit.com/service_center/notice?id=4936",
            "https://upbit.com/service_center/notice?id=5286",
        ],
        "APT": [
            "https://upbit.com/service_center/notice?id=3788",
            "https://upbit.com/service_center/notice?id=5357",
        ],
        "AHT": ["https://upbit.com/service_center/notice?id=3842"],
        "BTC": ["https://upbit.com/service_center/notice?id=720"],
        "BTG": ["https://upbit.com/service_center/notice?id=720"],
        "BTT": ["https://upbit.com/service_center/notice?id=1603"],
        "DOT": ["https://upbit.com/service_center/notice?id=4242"],
        "INJ": [
            "https://upbit.com/service_center/notice?id=4866",
            "https://upbit.com/service_center/notice?id=4925",
        ],
        "IP": ["https://upbit.com/service_center/notice?id=5457"],
        "JST": ["https://upbit.com/service_center/notice?id=1603"],
        "JUV": ["https://upbit.com/service_center/notice?id=2150"],
        "LTC": ["https://upbit.com/service_center/notice?id=720"],
        "MLK": ["https://upbit.com/service_center/notice?id=3842"],
        "MOC": ["https://upbit.com/service_center/notice?id=3842"],
        "NEAR": ["https://upbit.com/service_center/notice?id=4242"],
        "PSG": ["https://upbit.com/service_center/notice?id=2150"],
        "SC": ["https://upbit.com/service_center/notice?id=4242"],
        "SEI": [
            "https://upbit.com/service_center/notice?id=4837",
            "https://upbit.com/service_center/notice?id=5660",
        ],
        "SUI": ["https://upbit.com/service_center/notice?id=3924"],
        "SUN": ["https://upbit.com/service_center/notice?id=1603"],
        "TRX": ["https://upbit.com/service_center/notice?id=1603"],
        "WIN": ["https://upbit.com/service_center/notice?id=1603"],
        "XEC": ["https://upbit.com/service_center/notice?id=5286"],
        "XRP": ["https://upbit.com/service_center/notice?id=720"],
    },
    "bithumb": {
        "ADA": [
            "https://feed.bithumb.com/notice",
            "https://feed.bithumb.com/notice/1650802",
            "https://feed.bithumb.com/notice/1646838",
        ],
        "ATOM": [
            "https://feed.bithumb.com/notice",
            "https://feed.bithumb.com/notice/1648132",
        ],
        "BERA": ["https://feed.bithumb.com/notice"],
        "BSV": ["https://feed.bithumb.com/notice"],
        "DRIFT": ["https://feed.bithumb.com/notice"],
        "INJ": [
            "https://feed.bithumb.com/notice",
            "https://feed.bithumb.com/notice/1652019",
        ],
        "POL": ["https://feed.bithumb.com/notice"],
        "POKT": ["https://feed.bithumb.com/notice"],
        "PUNDIAI": ["https://feed.bithumb.com/notice/1649237"],
        "STX": ["https://feed.bithumb.com/notice"],
        "TAIKO": ["https://feed.bithumb.com/notice"],
        "WAXP": ["https://feed.bithumb.com/notice/1652352"],
        "WLD": ["https://feed.bithumb.com/notice/1647090"],
    },
}

KNOWN_OFFICIAL_NOTICE_CHAIN_URLS = {
    "upbit": {
        "KAIA": [
            "https://upbit.com/service_center/notice?id=5308",
            "https://upbit.com/service_center/notice?id=5410",
        ],
    },
    "bithumb": {
        "KAIA": ["https://feed.bithumb.com/notice"],
    },
}


def load_json(path: Path) -> Any:
    with open(path) as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        handle.write(content)


def sorted_unique(values: list[str] | set[str]) -> list[str]:
    return sorted(set(values))


def canonical_chain_ticker(value: str) -> str:
    return CHAIN_TICKER_ALIASES.get(value, value)


def build_recent_notice_summary(
    exchange: str, ticker: str, chain_tickers: list[str]
) -> dict[str, Any]:
    asset_urls = set(KNOWN_OFFICIAL_NOTICE_ASSET_URLS.get(exchange, {}).get(ticker, []))
    chain_hits: dict[str, list[str]] = {}
    for chain_ticker in chain_tickers:
        urls = KNOWN_OFFICIAL_NOTICE_CHAIN_URLS.get(exchange, {}).get(chain_ticker, [])
        if urls:
            chain_hits[chain_ticker] = sorted(set(urls))

    chain_urls = {url for urls in chain_hits.values() for url in urls}
    urls = sorted(asset_urls | chain_urls)
    reasons = [f"asset:{ticker}" for _ in sorted(asset_urls)]
    reasons.extend(f"chain:{chain}" for chain in sorted(chain_hits))

    return {
        "asset_hit_count": len(asset_urls),
        "chain_hit_count": sum(len(urls) for urls in chain_hits.values()),
        "total_hit_count": len(urls),
        "asset_urls": sorted(asset_urls),
        "chain_hits": chain_hits,
        "urls": urls,
        "reason_labels": reasons,
    }


def build_exchange_requirements(
    assets: list[dict[str, Any]], exchange: str
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    index: dict[str, dict[str, Any]] = {}

    for asset in sorted(assets, key=lambda item: item["ticker"]):
        chain_tickers = sorted_unique(
            canonical_chain_ticker(chain) for chain in asset["supported_chain_tickers"]
        )
        notice_summary = build_recent_notice_summary(
            exchange, asset["ticker"], chain_tickers
        )
        record = {
            "exchange": exchange,
            "ticker": asset["ticker"],
            "english_names": asset["english_names"],
            "markets": asset["markets"],
            "required_closed_chains": chain_tickers,
            "required_closed_chain_count": len(chain_tickers),
            "single_chain": len(chain_tickers) == 1,
            "supported_networks": asset["supported_networks"],
            "recent_official_notice_hits": notice_summary,
        }
        records.append(record)
        index[asset["ticker"]] = record

    return records, index


def build_combined_requirements(
    upbit_index: dict[str, dict[str, Any]],
    bithumb_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    combined: list[dict[str, Any]] = []

    all_tickers = sorted(set(upbit_index) | set(bithumb_index))
    for ticker in all_tickers:
        upbit = upbit_index.get(ticker)
        bithumb = bithumb_index.get(ticker)
        listed_on = [
            name for name, record in [("upbit", upbit), ("bithumb", bithumb)] if record
        ]
        combined_chains = sorted_unique(
            (upbit["required_closed_chains"] if upbit else [])
            + (bithumb["required_closed_chains"] if bithumb else [])
        )

        urls = set()
        recent_reason_labels: list[str] = []
        recent_hits_by_exchange = {}
        for name, record in [("upbit", upbit), ("bithumb", bithumb)]:
            if not record:
                continue
            recent = record["recent_official_notice_hits"]
            recent_hits_by_exchange[name] = recent
            urls.update(recent["urls"])
            recent_reason_labels.extend(
                f"{name}:{label}" for label in recent["reason_labels"]
            )

        exchange_single_chain_count = sum(
            1 for record in [upbit, bithumb] if record and record["single_chain"]
        )

        all_names = []
        for record in [upbit, bithumb]:
            if record:
                all_names.extend(record["english_names"])

        combined.append(
            {
                "ticker": ticker,
                "english_names": sorted_unique(all_names),
                "listed_on": listed_on,
                "listed_exchange_count": len(listed_on),
                "per_exchange": {
                    "upbit": {
                        "required_closed_chains": upbit["required_closed_chains"],
                        "required_closed_chain_count": upbit[
                            "required_closed_chain_count"
                        ],
                        "single_chain": upbit["single_chain"],
                        "markets": upbit["markets"],
                    }
                    if upbit
                    else None,
                    "bithumb": {
                        "required_closed_chains": bithumb["required_closed_chains"],
                        "required_closed_chain_count": bithumb[
                            "required_closed_chain_count"
                        ],
                        "single_chain": bithumb["single_chain"],
                        "markets": bithumb["markets"],
                    }
                    if bithumb
                    else None,
                },
                "domestic_full_cage_required_chains": combined_chains,
                "domestic_full_cage_chain_count": len(combined_chains),
                "exchange_single_chain_count": exchange_single_chain_count,
                "domestic_single_chain": len(combined_chains) == 1,
                "recent_official_notice_hits": {
                    "by_exchange": recent_hits_by_exchange,
                    "total_unique_url_count": len(urls),
                    "urls": sorted(urls),
                    "reason_labels": sorted(set(recent_reason_labels)),
                },
            }
        )

    return combined


def assign_structural_ranks(combined: list[dict[str, Any]]) -> list[dict[str, Any]]:
    structural_sorted = sorted(
        combined,
        key=lambda item: (
            item["domestic_full_cage_chain_count"],
            -item["exchange_single_chain_count"],
            -item["listed_exchange_count"],
            item["ticker"],
        ),
    )

    recent_weighted_sorted = sorted(
        combined,
        key=lambda item: (
            item["domestic_full_cage_chain_count"],
            -item["recent_official_notice_hits"]["total_unique_url_count"],
            -item["exchange_single_chain_count"],
            -item["listed_exchange_count"],
            item["ticker"],
        ),
    )

    structural_rank_by_ticker = {
        item["ticker"]: index + 1 for index, item in enumerate(structural_sorted)
    }
    recent_rank_by_ticker = {
        item["ticker"]: index + 1 for index, item in enumerate(recent_weighted_sorted)
    }

    ranked = []
    for item in combined:
        structural_rank = structural_rank_by_ticker[item["ticker"]]
        recent_rank = recent_rank_by_ticker[item["ticker"]]
        bucket = (
            "single-chain"
            if item["domestic_full_cage_chain_count"] == 1
            else "dual-chain"
            if item["domestic_full_cage_chain_count"] == 2
            else "multi-chain"
        )
        ranked.append(
            {
                **item,
                "structural_priority_rank": structural_rank,
                "recent_notice_weighted_rank": recent_rank,
                "priority_bucket": bucket,
            }
        )

    return sorted(ranked, key=lambda item: item["structural_priority_rank"])


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def render_chain_list(chains: list[str]) -> str:
    return ", ".join(chains) if chains else "-"


def build_markdown(
    exchange_requirements: dict[str, list[dict[str, Any]]],
    combined_ranked: list[dict[str, Any]],
) -> str:
    generated_at = datetime.now(timezone.utc).isoformat()
    single_chain_count = sum(
        1 for item in combined_ranked if item["domestic_single_chain"]
    )
    dual_chain_count = sum(
        1 for item in combined_ranked if item["domestic_full_cage_chain_count"] == 2
    )
    multi_chain_count = sum(
        1 for item in combined_ranked if item["domestic_full_cage_chain_count"] >= 3
    )

    lines = [
        "# Exchange Cage Requirements",
        "",
        f"- Generated at: {generated_at}",
        "- Meaning: a coin becomes a full exchange-level cage only when every currently supported withdrawal chain on that exchange is closed at the same time.",
        "- Domestic full cage means Upbit and Bithumb combined. If the same asset is listed on both exchanges, every supported chain across both exchanges must be closed.",
        "- Structural ranking is complete and deterministic from the live network mapping.",
        "- Recent notice weighted ranking uses only the official notice examples that were directly confirmable during this build window. It is a useful tiebreaker, not a full historical archive count.",
        "",
        "## Summary",
        "",
        f"- Combined unique assets: {len(combined_ranked)}",
        f"- Domestic single-chain assets: {single_chain_count}",
        f"- Domestic dual-chain assets: {dual_chain_count}",
        f"- Domestic 3+-chain assets: {multi_chain_count}",
        f"- Upbit assets: {len(exchange_requirements['upbit'])}",
        f"- Bithumb assets: {len(exchange_requirements['bithumb'])}",
        "",
        "## Domestic Priority Ranking",
        "",
        "| Rank(structural) | Rank(recent) | Ticker | Listed On | Required Chains | Chain Count | Known Notice Hits | Notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    for item in sorted(
        combined_ranked, key=lambda entry: entry["structural_priority_rank"]
    ):
        notes = []
        if item["domestic_single_chain"]:
            notes.append("single-chain")
        if item["exchange_single_chain_count"] == item["listed_exchange_count"]:
            notes.append("single on every listed exchange")
        if item["recent_official_notice_hits"]["total_unique_url_count"] > 0:
            notes.append("known official notice examples")
        lines.append(
            "| {structural} | {recent} | {ticker} | {listed_on} | {chains} | {count} | {hits} | {notes} |".format(
                structural=item["structural_priority_rank"],
                recent=item["recent_notice_weighted_rank"],
                ticker=item["ticker"],
                listed_on=", ".join(item["listed_on"]),
                chains=render_chain_list(item["domestic_full_cage_required_chains"]),
                count=item["domestic_full_cage_chain_count"],
                hits=item["recent_official_notice_hits"]["total_unique_url_count"],
                notes=", ".join(notes) if notes else "-",
            )
        )

    for exchange in ["upbit", "bithumb"]:
        records = exchange_requirements[exchange]
        lines.extend(
            [
                "",
                f"## {exchange.upper()} Per-Asset Full Cage Requirements",
                "",
                "| Ticker | Required Closed Chains | Chain Count | Single Chain | Known Notice Hits |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for record in records:
            lines.append(
                "| {ticker} | {chains} | {count} | {single} | {hits} |".format(
                    ticker=record["ticker"],
                    chains=render_chain_list(record["required_closed_chains"]),
                    count=record["required_closed_chain_count"],
                    single="Y" if record["single_chain"] else "N",
                    hits=record["recent_official_notice_hits"]["total_hit_count"],
                )
            )

        lines.extend(
            [
                "",
                f"### {exchange.upper()} Single-Chain Assets",
                "",
            ]
        )
        single_chain_assets = [
            record["ticker"] for record in records if record["single_chain"]
        ]
        for group in chunked(single_chain_assets, 20):
            lines.append(", ".join(group))

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument(
        "--requirements-output", type=Path, default=DEFAULT_REQUIREMENTS_OUTPUT
    )
    parser.add_argument("--rankings-output", type=Path, default=DEFAULT_RANKINGS_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    args = parser.parse_args()

    payload = load_json(args.input)
    upbit_assets = payload["exchanges"]["upbit"]["assets"]
    bithumb_assets = payload["exchanges"]["bithumb"]["assets"]

    upbit_requirements, upbit_index = build_exchange_requirements(upbit_assets, "upbit")
    bithumb_requirements, bithumb_index = build_exchange_requirements(
        bithumb_assets, "bithumb"
    )
    combined_ranked = assign_structural_ranks(
        build_combined_requirements(upbit_index, bithumb_index)
    )

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "asset_network_mapping": Path(
                os.path.relpath(args.input.resolve(), MODULE_DIR.resolve())
            ).as_posix(),
            "upbit_markets": "https://api.upbit.com/v1/market/all?isDetails=false",
            "upbit_network_status": "https://ccx.upbit.com/api/v1/status/network/wallet",
            "upbit_notice_base": "https://upbit.com/service_center/notice",
            "upbit_notice_api": "https://api-manager.upbit.com/api/v1",
            "bithumb_markets": "https://api.bithumb.com/v1/market/all?isDetails=false",
            "bithumb_multichain_status_template": "https://api.bithumb.com/public/assetsstatus/multichain/{currency}",
            "bithumb_notice_base": "https://feed.bithumb.com/notice",
            "bithumb_react_sitemap": "https://www.bithumb.com/react/sitemap.xml",
        },
        "notes": [
            "Per-exchange full cage means all currently supported withdrawal chains on that exchange must be closed at the same time.",
            "Domestic full cage means the union of Upbit/Bithumb supported chains for the same asset must be closed at the same time.",
            "Structural ranking is complete from the live exchange network mapping.",
            "Known official notice hits are intentionally conservative and incomplete. They are derived only from directly confirmable official notice pages or official-domain search results observed during this build window.",
        ],
    }

    requirements_payload = {
        **meta,
        "exchanges": {
            "upbit": {
                "asset_count": len(upbit_requirements),
                "single_chain_asset_count": sum(
                    1 for item in upbit_requirements if item["single_chain"]
                ),
                "multi_chain_asset_count": sum(
                    1 for item in upbit_requirements if not item["single_chain"]
                ),
                "assets": upbit_requirements,
            },
            "bithumb": {
                "asset_count": len(bithumb_requirements),
                "single_chain_asset_count": sum(
                    1 for item in bithumb_requirements if item["single_chain"]
                ),
                "multi_chain_asset_count": sum(
                    1 for item in bithumb_requirements if not item["single_chain"]
                ),
                "assets": bithumb_requirements,
            },
        },
        "combined": {
            "asset_count": len(combined_ranked),
            "single_chain_asset_count": sum(
                1 for item in combined_ranked if item["domestic_single_chain"]
            ),
            "dual_chain_asset_count": sum(
                1
                for item in combined_ranked
                if item["domestic_full_cage_chain_count"] == 2
            ),
            "multi_chain_asset_count": sum(
                1
                for item in combined_ranked
                if item["domestic_full_cage_chain_count"] >= 3
            ),
            "assets": combined_ranked,
        },
    }

    rankings_payload = {
        **meta,
        "methodology": {
            "structural_sort": [
                "domestic_full_cage_chain_count ascending",
                "exchange_single_chain_count descending",
                "listed_exchange_count descending",
                "ticker ascending",
            ],
            "recent_notice_weighted_sort": [
                "domestic_full_cage_chain_count ascending",
                "recent_official_notice_hits.total_unique_url_count descending",
                "exchange_single_chain_count descending",
                "listed_exchange_count descending",
                "ticker ascending",
            ],
        },
        "ranked_assets": combined_ranked,
    }

    markdown = build_markdown(
        exchange_requirements={
            "upbit": upbit_requirements,
            "bithumb": bithumb_requirements,
        },
        combined_ranked=combined_ranked,
    )

    write_json(args.requirements_output, requirements_payload)
    write_json(args.rankings_output, rankings_payload)
    write_text(args.markdown_output, markdown)

    summary = {
        "requirements_output": str(args.requirements_output),
        "rankings_output": str(args.rankings_output),
        "markdown_output": str(args.markdown_output),
        "combined_asset_count": len(combined_ranked),
        "combined_single_chain_asset_count": sum(
            1 for item in combined_ranked if item["domestic_single_chain"]
        ),
        "upbit_single_chain_asset_count": sum(
            1 for item in upbit_requirements if item["single_chain"]
        ),
        "bithumb_single_chain_asset_count": sum(
            1 for item in bithumb_requirements if item["single_chain"]
        ),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
