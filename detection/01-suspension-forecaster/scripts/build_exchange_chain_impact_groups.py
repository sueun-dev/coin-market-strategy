#!/usr/bin/env python3
"""Build per-exchange chain impact groups from live Upbit and Bithumb network data."""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


MODULE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ASSET_OUTPUT = MODULE_DIR / "config" / "exchange_asset_networks.json"
DEFAULT_GROUP_OUTPUT = MODULE_DIR / "config" / "exchange_chain_impact_groups.json"
DEFAULT_MARKDOWN_OUTPUT = MODULE_DIR / "EXCHANGE_CHAIN_IMPACT_GROUPS.md"

UPBIT_MARKETS_URL = "https://api.upbit.com/v1/market/all?isDetails=false"
UPBIT_NETWORK_STATUS_URL = "https://ccx.upbit.com/api/v1/status/network/wallet"
BITHUMB_MARKETS_URL = "https://api.bithumb.com/v1/market/all?isDetails=false"
BITHUMB_MULTICHAIN_URL = (
    "https://api.bithumb.com/public/assetsstatus/multichain/{currency}"
)

HTTP_HEADERS = {"accept": "application/json", "user-agent": "Mozilla/5.0"}
UPBIT_HTTP_HEADERS = {
    **HTTP_HEADERS,
    "origin": "https://upbit.com",
    "referer": "https://upbit.com/",
}

CHAIN_ALIASES = {
    "ADA": ("ADA", "Cardano"),
    "ALGO": ("ALGO", "Algorand"),
    "APT": ("APT", "Aptos"),
    "APTOS": ("APT", "Aptos"),
    "ARB": ("ARB", "Arbitrum One"),
    "ARBITRUM": ("ARB", "Arbitrum One"),
    "ARBITRUM ONE": ("ARB", "Arbitrum One"),
    "ARB_ETH": ("ARB", "Arbitrum One"),
    "ASTR": ("ASTR", "Astar"),
    "ATOM": ("ATOM", "Cosmos Hub"),
    "AVAIL": ("AVAIL", "Avail"),
    "AVAX": ("AVAX", "Avalanche"),
    "AVALANCHE": ("AVAX", "Avalanche"),
    "AXL": ("AXL", "Axelar"),
    "BASE": ("BASE", "Base"),
    "BASENET": ("BASE", "Base"),
    "BASE_ETH": ("BASE", "Base"),
    "BCH": ("BCH", "Bitcoin Cash"),
    "BERA": ("BERA", "Berachain"),
    "BLAST": ("BLAST", "Blast"),
    "BNB": ("BNB", "BNB Smart Chain"),
    "BNB SMART CHAIN": ("BNB", "BNB Smart Chain"),
    "BSC": ("BNB", "BNB Smart Chain"),
    "BTC": ("BTC", "Bitcoin"),
    "BITCOIN": ("BTC", "Bitcoin"),
    "CELO": ("CELO", "Celo"),
    "CFX": ("CFX", "Conflux"),
    "CHILIZ CHAIN": ("CHZ", "Chiliz Chain"),
    "CHILIZ-CHAIN": ("CHZ", "Chiliz Chain"),
    "CHZ": ("CHZ", "Chiliz Chain"),
    "CKB": ("CKB", "Nervos CKB"),
    "CORE": ("CORE", "Core"),
    "CRO": ("CRO", "Cronos"),
    "CSPR": ("CSPR", "Casper"),
    "DOGE": ("DOGE", "Dogecoin"),
    "DOT": ("DOT", "Polkadot"),
    "EGLD": ("EGLD", "MultiversX"),
    "ELF": ("ELF", "aelf"),
    "ERC-20": ("ETH", "Ethereum"),
    "ETC": ("ETC", "Ethereum Classic"),
    "ETH": ("ETH", "Ethereum"),
    "ETHEREUM": ("ETH", "Ethereum"),
    "ETHEREUM CLASSIC": ("ETC", "Ethereum Classic"),
    "FIL": ("FIL", "Filecoin"),
    "FLR": ("FLR", "Flare"),
    "GAS": ("GAS", "Neo Gas"),
    "HBAR": ("HBAR", "Hedera"),
    "HIVE": ("HIVE", "Hive"),
    "ICP": ("ICP", "Internet Computer"),
    "ICON": ("ICX", "ICON"),
    "ICX": ("ICX", "ICON"),
    "INJ": ("INJ", "Injective"),
    "IOTA": ("IOTA", "IOTA"),
    "IOTX": ("IOTX", "IoTeX"),
    "KAIA": ("KAIA", "Kaia"),
    "KCT": ("KAIA", "Kaia"),
    "KAVA": ("KAVA", "Kava"),
    "KLAYTN": ("KAIA", "Kaia"),
    "KSM": ("KSM", "Kusama"),
    "LINEA": ("LINEA", "Linea"),
    "METIS": ("METIS", "Metis"),
    "MINA": ("MINA", "Mina"),
    "MNT": ("MNT", "Mantle"),
    "NEAR": ("NEAR", "NEAR"),
    "NEO": ("NEO", "Neo"),
    "ONT": ("ONT", "Ontology"),
    "ONTOLOGY": ("ONT", "Ontology"),
    "OP": ("OP", "Optimism"),
    "OP_ETH": ("OP", "Optimism"),
    "OPTIMISM": ("OP", "Optimism"),
    "OSMO": ("OSMO", "Osmosis"),
    "PLA": ("PLA", "PlayDapp"),
    "PLASMA": ("XPL", "Plasma"),
    "POL": ("POL", "Polygon"),
    "POLYGON": ("POL", "Polygon"),
    "QTUM": ("QTUM", "Qtum"),
    "SCROLL": ("SCR", "Scroll"),
    "SCR": ("SCR", "Scroll"),
    "SEI": ("SEI", "Sei"),
    "SOL": ("SOL", "Solana"),
    "SOLANA": ("SOL", "Solana"),
    "SONIC": ("SONIC", "Sonic"),
    "SPL": ("SOL", "Solana"),
    "STX": ("STX", "Stacks"),
    "SUI": ("SUI", "Sui"),
    "TAIKO": ("TAIKO", "Taiko"),
    "THETA": ("THETA", "Theta Network"),
    "TON": ("TON", "TON"),
    "TRC20": ("TRX", "TRON"),
    "TRON": ("TRX", "TRON"),
    "TRX": ("TRX", "TRON"),
    "VET": ("VET", "VeChain"),
    "WAVES": ("WAVES", "Waves"),
    "XLM": ("XLM", "Stellar"),
    "XPLA": ("XPLA", "XPLA"),
    "XRP": ("XRP", "XRP Ledger"),
    "XTZ": ("XTZ", "Tezos"),
    "ZETA": ("ZETA", "ZetaChain"),
    "ZIL": ("ZIL", "Zilliqa"),
    "ZKSYNC": ("ZK", "ZKsync"),
    "ZK": ("ZK", "ZKsync"),
}


@dataclass(frozen=True)
class ExchangeMeta:
    name: str
    markets_url: str


UPBIT = ExchangeMeta(name="upbit", markets_url=UPBIT_MARKETS_URL)
BITHUMB = ExchangeMeta(name="bithumb", markets_url=BITHUMB_MARKETS_URL)


def get_json(url: str, headers: dict[str, str] | None = None, retries: int = 3) -> Any:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            request = Request(url, headers=headers or HTTP_HEADERS)
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except (HTTPError, URLError) as exc:
            last_error = exc
            if attempt == retries - 1:
                raise
            time.sleep(0.2 * (attempt + 1))
    raise RuntimeError(last_error)


def normalize_key(value: str | None) -> str:
    return (value or "").strip().upper().replace("-", " ")


def normalize_chain(raw_type: str | None, raw_name: str | None) -> tuple[str, str]:
    for candidate in [raw_name, raw_type]:
        key = normalize_key(candidate)
        if key in CHAIN_ALIASES:
            return CHAIN_ALIASES[key]

    raw_type_key = normalize_key(raw_type)
    if raw_type_key.endswith("_ETH"):
        prefix = raw_type_key[: -len("_ETH")]
        if prefix in CHAIN_ALIASES:
            return CHAIN_ALIASES[prefix]

    if raw_type_key in CHAIN_ALIASES:
        return CHAIN_ALIASES[raw_type_key]

    display = (raw_name or raw_type or "UNKNOWN").strip()
    return raw_type_key or display.upper(), display


def load_market_rows(exchange: ExchangeMeta) -> list[dict[str, Any]]:
    return get_json(exchange.markets_url)


def build_market_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    assets: dict[str, dict[str, Any]] = {}
    for row in rows:
        _, base = row["market"].split("-")
        item = assets.setdefault(
            base.upper(),
            {
                "ticker": base.upper(),
                "english_names": set(),
                "markets": [],
            },
        )
        item["english_names"].add(row["english_name"])
        item["markets"].append(row["market"])
    return assets


def fetch_upbit_network_rows() -> list[dict[str, Any]]:
    rows = get_json(UPBIT_NETWORK_STATUS_URL, headers=UPBIT_HTTP_HEADERS)
    return rows if isinstance(rows, list) else []


def fetch_bithumb_asset_networks(
    currency: str,
) -> tuple[str, list[dict[str, Any]], str | None]:
    url = BITHUMB_MULTICHAIN_URL.format(currency=currency)
    try:
        payload = get_json(url)
        rows = payload.get("data", [])
        if isinstance(rows, dict):
            rows = [rows]
        normalized_rows = []
        for row in rows:
            normalized_rows.append(
                {
                    "currency": row.get("currency", currency),
                    "wallet_state": "working"
                    if row.get("deposit_status") == 1
                    or row.get("withdrawal_status") == 1
                    else "stopped",
                    "block_state": None,
                    "block_height": None,
                    "block_updated_at": None,
                    "block_elapsed_minutes": None,
                    "message": "",
                    "net_type": row.get("net_type"),
                    "network_name": None,
                    "deposit_status": row.get("deposit_status"),
                    "withdrawal_status": row.get("withdrawal_status"),
                }
            )
        return currency, normalized_rows, None
    except HTTPError as exc:
        return currency, [], f"HTTP {exc.code}"
    except URLError as exc:
        return currency, [], f"URL {exc.reason}"


def fetch_bithumb_network_rows(
    currencies: list[str], max_workers: int = 10
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_bithumb_asset_networks, currency): currency
            for currency in currencies
        }
        for future in as_completed(futures):
            currency, rows, error = future.result()
            if error is not None:
                errors.append({"ticker": currency, "reason": error})
            elif rows:
                results[currency] = rows
            else:
                errors.append({"ticker": currency, "reason": "empty_response"})
    return results, sorted(errors, key=lambda item: item["ticker"])


def build_asset_records(
    exchange: ExchangeMeta,
    market_assets: dict[str, dict[str, Any]],
    network_rows_by_currency: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    asset_records: list[dict[str, Any]] = []
    unresolved_assets: list[dict[str, Any]] = []

    for ticker in sorted(market_assets):
        market_info = market_assets[ticker]
        rows = network_rows_by_currency.get(ticker, [])
        if not rows:
            unresolved_assets.append(
                {
                    "ticker": ticker,
                    "english_names": sorted(market_info["english_names"]),
                    "markets": sorted(market_info["markets"]),
                    "reason": "missing_network_status",
                }
            )
            continue

        supported_networks = []
        chain_keys = set()
        for row in rows:
            chain_ticker, chain_name = normalize_chain(
                row.get("net_type"), row.get("network_name")
            )
            chain_keys.add(chain_ticker)
            supported_networks.append(
                {
                    "chain_ticker": chain_ticker,
                    "chain_name": chain_name,
                    "net_type": row.get("net_type"),
                    "network_name": row.get("network_name"),
                    "wallet_state": row.get("wallet_state"),
                    "block_state": row.get("block_state"),
                    "block_height": row.get("block_height"),
                    "block_updated_at": row.get("block_updated_at"),
                    "block_elapsed_minutes": row.get("block_elapsed_minutes"),
                    "message": row.get("message") or "",
                    "deposit_status": row.get("deposit_status"),
                    "withdrawal_status": row.get("withdrawal_status"),
                }
            )

        asset_records.append(
            {
                "exchange": exchange.name,
                "ticker": ticker,
                "english_names": sorted(market_info["english_names"]),
                "markets": sorted(market_info["markets"]),
                "supported_networks": sorted(
                    supported_networks,
                    key=lambda item: (
                        item["chain_ticker"],
                        item["net_type"] or "",
                        item["network_name"] or "",
                    ),
                ),
                "supported_chain_tickers": sorted(chain_keys),
                "is_multi_chain": len(supported_networks) > 1,
            }
        )

    return asset_records, unresolved_assets


def build_chain_groups(
    exchange: ExchangeMeta, asset_records: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    chains: dict[str, dict[str, Any]] = {}
    for asset in asset_records:
        for network in asset["supported_networks"]:
            chain = chains.setdefault(
                network["chain_ticker"],
                {
                    "exchange": exchange.name,
                    "chain_ticker": network["chain_ticker"],
                    "chain_name": network["chain_name"],
                    "net_types": set(),
                    "network_names": set(),
                    "affected_assets": [],
                },
            )
            if network.get("net_type"):
                chain["net_types"].add(network["net_type"])
            if network.get("network_name"):
                chain["network_names"].add(network["network_name"])
            chain["affected_assets"].append(
                {
                    "ticker": asset["ticker"],
                    "english_names": asset["english_names"],
                    "markets": asset["markets"],
                    "is_multi_chain": asset["is_multi_chain"],
                    "all_supported_chain_tickers": asset["supported_chain_tickers"],
                    "all_supported_networks": [
                        {
                            "chain_ticker": item["chain_ticker"],
                            "chain_name": item["chain_name"],
                            "net_type": item["net_type"],
                            "network_name": item["network_name"],
                        }
                        for item in asset["supported_networks"]
                    ],
                    "matched_network": {
                        "chain_ticker": network["chain_ticker"],
                        "chain_name": network["chain_name"],
                        "net_type": network["net_type"],
                        "network_name": network["network_name"],
                    },
                }
            )

    groups = []
    for chain_ticker in sorted(chains):
        chain = chains[chain_ticker]
        chain["affected_assets"].sort(key=lambda item: item["ticker"])
        groups.append(
            {
                "exchange": exchange.name,
                "chain_ticker": chain_ticker,
                "chain_name": chain["chain_name"],
                "net_types": sorted(chain["net_types"]),
                "network_names": sorted(chain["network_names"]),
                "affected_asset_count": len(chain["affected_assets"]),
                "multi_chain_asset_count": sum(
                    1 for item in chain["affected_assets"] if item["is_multi_chain"]
                ),
                "affected_assets": chain["affected_assets"],
            }
        )
    return groups


def build_exchange_payload(
    exchange: ExchangeMeta,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    market_rows = load_market_rows(exchange)
    market_assets = build_market_index(market_rows)

    if exchange.name == "upbit":
        raw_network_rows = fetch_upbit_network_rows()
        network_rows_by_currency: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in raw_network_rows:
            currency = str(row.get("currency", "")).upper()
            if currency in market_assets:
                network_rows_by_currency[currency].append(row)
        source_note = {
            "markets_endpoint": UPBIT_MARKETS_URL,
            "network_status_endpoint": UPBIT_NETWORK_STATUS_URL,
        }
        fetch_errors: list[dict[str, Any]] = []
    else:
        currencies = sorted(market_assets)
        network_rows_by_currency, fetch_errors = fetch_bithumb_network_rows(currencies)
        source_note = {
            "markets_endpoint": BITHUMB_MARKETS_URL,
            "network_status_endpoint_template": BITHUMB_MULTICHAIN_URL,
        }

    asset_records, unresolved_assets = build_asset_records(
        exchange, market_assets, network_rows_by_currency
    )
    chain_groups = build_chain_groups(exchange, asset_records)

    payload = {
        "exchange": exchange.name,
        "source": source_note,
        "stats": {
            "listed_pair_count": len(market_rows),
            "listed_asset_count": len(market_assets),
            "resolved_asset_count": len(asset_records),
            "unresolved_asset_count": len(unresolved_assets),
            "chain_group_count": len(chain_groups),
            "multi_chain_asset_count": sum(
                1 for item in asset_records if item["is_multi_chain"]
            ),
            "network_row_count": sum(
                len(item["supported_networks"]) for item in asset_records
            ),
            "fetch_error_count": len(fetch_errors),
        },
        "assets": asset_records,
        "chains": chain_groups,
        "unresolved_assets": unresolved_assets,
        "fetch_errors": fetch_errors,
    }
    return payload, asset_records, chain_groups


def chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def render_asset_label(asset: dict[str, Any]) -> str:
    ticker = asset["ticker"]
    supported = sorted(
        {network["chain_ticker"] for network in asset["all_supported_networks"]}
    )
    if len(supported) <= 1:
        return ticker
    return f"{ticker}{{{','.join(supported)}}}"


def build_markdown(exchanges: list[dict[str, Any]]) -> str:
    lines = [
        "# Exchange Chain Impact Groups",
        "",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        "- Meaning: if a chain/network is suspended or upgraded on that exchange, the assets listed under that chain are the ones most likely to face deposit/withdrawal restrictions on that exchange.",
        "- Multi-chain assets appear under every supported chain bucket on that exchange.",
        "",
    ]

    for exchange in exchanges:
        stats = exchange["stats"]
        lines.extend(
            [
                f"## {exchange['exchange'].upper()}",
                "",
                f"- Listed pairs: {stats['listed_pair_count']}",
                f"- Listed assets: {stats['listed_asset_count']}",
                f"- Resolved assets: {stats['resolved_asset_count']}",
                f"- Multi-chain assets: {stats['multi_chain_asset_count']}",
                f"- Chain groups: {stats['chain_group_count']}",
                f"- Unresolved assets: {stats['unresolved_asset_count']}",
                "",
            ]
        )

        for chain in exchange["chains"]:
            lines.append(f"### {chain['chain_ticker']} · {chain['chain_name']}")
            lines.append(
                f"- Net types: {', '.join(chain['net_types']) if chain['net_types'] else '(none)'}"
            )
            if chain["network_names"]:
                lines.append(f"- Network names: {', '.join(chain['network_names'])}")
            lines.append(f"- Affected assets: {chain['affected_asset_count']}")
            lines.append(
                f"- Multi-chain assets in bucket: {chain['multi_chain_asset_count']}"
            )
            lines.append("- Assets:")

            labels = [render_asset_label(asset) for asset in chain["affected_assets"]]
            for group in chunked(labels, 16):
                lines.append(f"  {', '.join(group)}")
            lines.append("")

        if exchange["unresolved_assets"]:
            lines.append("### Unresolved Assets")
            lines.append("")
            for asset in exchange["unresolved_assets"]:
                names = ", ".join(asset["english_names"])
                markets = ", ".join(asset["markets"])
                lines.append(
                    f"- {asset['ticker']} ({names}) | reason={asset['reason']} | markets={markets}"
                )
            lines.append("")

        if exchange["fetch_errors"]:
            lines.append("### Fetch Errors")
            lines.append("")
            for error in exchange["fetch_errors"]:
                lines.append(f"- {error['ticker']} | reason={error['reason']}")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as handle:
        handle.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-output", type=Path, default=DEFAULT_ASSET_OUTPUT)
    parser.add_argument("--group-output", type=Path, default=DEFAULT_GROUP_OUTPUT)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_OUTPUT)
    args = parser.parse_args()

    upbit_payload, upbit_assets, upbit_chains = build_exchange_payload(UPBIT)
    bithumb_payload, bithumb_assets, bithumb_chains = build_exchange_payload(BITHUMB)

    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {
            "upbit_support_article": "https://support.upbit.com/hc/ko/articles/14459102537881-%EB%94%94%EC%A7%80%ED%84%B8-%EC%9E%90%EC%82%B0-%EB%84%A4%ED%8A%B8%EC%9B%8C%ED%81%AC-%EC%95%8C%EC%95%84%EB%B3%B4%EA%B8%B0",
            "upbit_markets": UPBIT_MARKETS_URL,
            "upbit_network_status": UPBIT_NETWORK_STATUS_URL,
            "bithumb_markets": BITHUMB_MARKETS_URL,
            "bithumb_multichain_status_template": BITHUMB_MULTICHAIN_URL,
        },
        "notes": [
            "Upbit network rows are fetched from the public wallet status endpoint used by the official Upbit web application.",
            "Bithumb network rows are fetched per listed asset from the public multichain status endpoint.",
            "Multi-chain assets are intentionally duplicated into every supported chain bucket for exchange impact analysis.",
        ],
    }

    asset_payload = {
        **meta,
        "exchanges": {
            "upbit": {
                "stats": upbit_payload["stats"],
                "assets": upbit_assets,
                "unresolved_assets": upbit_payload["unresolved_assets"],
                "fetch_errors": upbit_payload["fetch_errors"],
            },
            "bithumb": {
                "stats": bithumb_payload["stats"],
                "assets": bithumb_assets,
                "unresolved_assets": bithumb_payload["unresolved_assets"],
                "fetch_errors": bithumb_payload["fetch_errors"],
            },
        },
    }

    group_payload = {
        **meta,
        "exchanges": {
            "upbit": {
                "stats": upbit_payload["stats"],
                "chains": upbit_chains,
                "unresolved_assets": upbit_payload["unresolved_assets"],
                "fetch_errors": upbit_payload["fetch_errors"],
            },
            "bithumb": {
                "stats": bithumb_payload["stats"],
                "chains": bithumb_chains,
                "unresolved_assets": bithumb_payload["unresolved_assets"],
                "fetch_errors": bithumb_payload["fetch_errors"],
            },
        },
    }

    markdown = build_markdown([upbit_payload, bithumb_payload])

    write_json(args.asset_output, asset_payload)
    write_json(args.group_output, group_payload)
    write_text(args.markdown_output, markdown)

    summary = {
        "asset_output": str(args.asset_output),
        "group_output": str(args.group_output),
        "markdown_output": str(args.markdown_output),
        "upbit": upbit_payload["stats"],
        "bithumb": bithumb_payload["stats"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
