#!/usr/bin/env python3
"""Build the full Upbit/Bithumb chain inventory used by 01."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


MODULE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = MODULE_DIR / "config" / "exchange_chain_inventory.json"
TARGETS_FILE = MODULE_DIR / "config" / "targets.json"

UPBIT_MARKETS_URL = "https://api.upbit.com/v1/market/all?isDetails=false"
BITHUMB_MARKETS_URL = "https://api.bithumb.com/v1/market/all?isDetails=false"
CMC_MAP_URLS = [
    "https://api.coinmarketcap.com/data-api/v3/map/all?listing_status=active&start=1&limit=5000&aux=platform,is_active,status",
    "https://api.coinmarketcap.com/data-api/v3/map/all?listing_status=active&start=5001&limit=5000&aux=platform,is_active,status",
]

KNOWN_NATIVE_CHAINS = {
    "A": "Vaulta",
    "ADA": "Cardano",
    "AERGO": "Aergo",
    "AIOZ": "AIOZ Network",
    "AKT": "Akash",
    "ALGO": "Algorand",
    "APT": "Aptos",
    "AR": "Arweave",
    "ARB": "Arbitrum One",
    "ARDR": "Ardor",
    "ARK": "Ark",
    "ASTR": "Astar",
    "ATOM": "Cosmos Hub",
    "AVAIL": "Avail",
    "AVAX": "Avalanche",
    "AXL": "Axelar",
    "BABY": "Babylon",
    "BAND": "Band Protocol",
    "BB": "BounceBit",
    "BEAM": "Beam",
    "BERA": "Berachain",
    "BCH": "Bitcoin Cash",
    "BLAST": "Blast",
    "BNB": "BNB Smart Chain",
    "BSV": "Bitcoin SV",
    "BTC": "Bitcoin",
    "BTR": "Bitlayer",
    "CELO": "Celo",
    "CFG": "Centrifuge",
    "CFX": "Conflux",
    "CHZ": "Chiliz Chain",
    "CKB": "Nervos CKB",
    "CORE": "Core",
    "COTI": "COTI",
    "CRO": "Crypto.org Chain",
    "CSPR": "Casper",
    "CTC": "Creditcoin",
    "CTK": "Shentu",
    "DGB": "DigiByte",
    "DOGE": "Dogecoin",
    "DOT": "Polkadot",
    "EGLD": "MultiversX",
    "ELF": "aelf",
    "ETC": "Ethereum Classic",
    "ETH": "Ethereum",
    "FIL": "Filecoin",
    "FLOW": "Flow",
    "FLR": "Flare",
    "FLUX": "Flux",
    "G": "Gravity",
    "GAS": "Neo Gas",
    "GLMR": "Moonbeam",
    "HBAR": "Hedera",
    "HIVE": "Hive",
    "ICP": "Internet Computer",
    "ICX": "ICON",
    "INIT": "Initia",
    "INJ": "Injective",
    "IOST": "IOST",
    "IOTA": "IOTA",
    "IOTX": "IoTeX",
    "IP": "Story",
    "IRIS": "IRISnet",
    "KAIA": "Kaia",
    "KAVA": "Kava",
    "KSM": "Kusama",
    "LINEA": "Linea",
    "LSK": "Lisk",
    "MANTRA": "MANTRA",
    "MAPO": "MAP Protocol",
    "MANTA": "Manta Network",
    "MED": "Panacea",
    "META": "Metadium",
    "METIS": "Metis",
    "MEV": "MEVerse",
    "MINA": "Mina",
    "MNT": "Mantle",
    "MON": "Monad",
    "NEAR": "NEAR",
    "NEO": "Neo",
    "NKN": "NKN",
    "ONT": "Ontology",
    "OP": "Optimism",
    "OSMO": "Osmosis",
    "PEAQ": "peaq",
    "PHA": "Phala Network",
    "PLUME": "Plume",
    "POKT": "Pocket Network",
    "POL": "Polygon",
    "POLYX": "Polymesh",
    "QTUM": "Qtum",
    "REI": "REI Network",
    "RON": "Ronin",
    "RVN": "Ravencoin",
    "SC": "Siacoin",
    "SCR": "Scroll",
    "SEI": "Sei",
    "SOL": "Solana",
    "SONIC": "Sonic",
    "STARS": "Stargaze",
    "STEEM": "Steem",
    "STX": "Stacks",
    "STRD": "Stride",
    "SUI": "Sui",
    "TAIKO": "Taiko",
    "TAO": "Bittensor",
    "THETA": "Theta Network",
    "TIA": "Celestia",
    "TON": "TON",
    "TRX": "TRON",
    "TT": "ThunderCore",
    "VET": "VeChain",
    "WAVES": "Waves",
    "WAXP": "WAX",
    "XEC": "eCash",
    "XLM": "Stellar",
    "XPLA": "XPLA",
    "XPR": "XPR Network",
    "XRP": "XRP Ledger",
    "XTZ": "Tezos",
    "ZETA": "ZetaChain",
    "ZIL": "Zilliqa",
}

PLATFORM_TO_CHAIN = {
    "algorand": ("ALGO", "Algorand"),
    "aptos": ("APT", "Aptos"),
    "arbitrum": ("ARB", "Arbitrum One"),
    "arbitrum one": ("ARB", "Arbitrum One"),
    "avalanche": ("AVAX", "Avalanche"),
    "avalanche c-chain": ("AVAX", "Avalanche"),
    "base": ("BASE", "Base"),
    "bitcoin": ("BTC", "Bitcoin"),
    "bitcoin cash": ("BCH", "Bitcoin Cash"),
    "bittensor": ("TAO", "Bittensor"),
    "blast": ("BLAST", "Blast"),
    "bnb": ("BNB", "BNB Smart Chain"),
    "bnb smart chain (bep20)": ("BNB", "BNB Smart Chain"),
    "cardano": ("ADA", "Cardano"),
    "casper": ("CSPR", "Casper"),
    "celo": ("CELO", "Celo"),
    "chiliz chain": ("CHZ", "Chiliz Chain"),
    "conflux": ("CFX", "Conflux"),
    "core": ("CORE", "Core"),
    "cosmos": ("ATOM", "Cosmos Hub"),
    "cosmos hub": ("ATOM", "Cosmos Hub"),
    "cronos": ("CRO", "Cronos"),
    "dogecoin": ("DOGE", "Dogecoin"),
    "elrond": ("EGLD", "MultiversX"),
    "ethereum": ("ETH", "Ethereum"),
    "ethereum classic": ("ETC", "Ethereum Classic"),
    "filecoin": ("FIL", "Filecoin"),
    "flare": ("FLR", "Flare"),
    "gas": ("GAS", "Neo Gas"),
    "hedera": ("HBAR", "Hedera"),
    "icon": ("ICX", "ICON"),
    "icp": ("ICP", "Internet Computer"),
    "injective": ("INJ", "Injective"),
    "internet computer": ("ICP", "Internet Computer"),
    "iotex": ("IOTX", "IoTeX"),
    "kaia": ("KAIA", "Kaia"),
    "kava": ("KAVA", "Kava"),
    "linea": ("LINEA", "Linea"),
    "mantle": ("MNT", "Mantle"),
    "manta network": ("MANTA", "Manta Network"),
    "mantra": ("MANTRA", "MANTRA"),
    "metis andromeda": ("METIS", "Metis"),
    "metal dao": ("MTL", "Metal DAO"),
    "mina": ("MINA", "Mina"),
    "multiversx": ("EGLD", "MultiversX"),
    "near": ("NEAR", "NEAR"),
    "near protocol": ("NEAR", "NEAR"),
    "neo": ("NEO", "Neo"),
    "ontology": ("ONT", "Ontology"),
    "optimism": ("OP", "Optimism"),
    "osmosis": ("OSMO", "Osmosis"),
    "plume": ("PLUME", "Plume"),
    "polygon": ("POL", "Polygon"),
    "polygon ecosystem token": ("POL", "Polygon"),
    "polygon zkevm": ("POL", "Polygon"),
    "qtum": ("QTUM", "Qtum"),
    "ripple": ("XRP", "XRP Ledger"),
    "scroll": ("SCR", "Scroll"),
    "sei": ("SEI", "Sei"),
    "sei network": ("SEI", "Sei"),
    "solana": ("SOL", "Solana"),
    "sonic": ("SONIC", "Sonic"),
    "stacks": ("STX", "Stacks"),
    "stellar": ("XLM", "Stellar"),
    "story": ("IP", "Story"),
    "sui": ("SUI", "Sui"),
    "sui network": ("SUI", "Sui"),
    "taiko": ("TAIKO", "Taiko"),
    "tezos": ("XTZ", "Tezos"),
    "the open network": ("TON", "TON"),
    "theta": ("THETA", "Theta Network"),
    "ton": ("TON", "TON"),
    "tron": ("TRX", "TRON"),
    "tron20": ("TRX", "TRON"),
    "vechain": ("VET", "VeChain"),
    "waves": ("WAVES", "Waves"),
    "wax": ("WAXP", "WAX"),
    "xpla": ("XPLA", "XPLA"),
    "xrp ledger": ("XRP", "XRP Ledger"),
    "zetachain": ("ZETA", "ZetaChain"),
    "zilliqa": ("ZIL", "Zilliqa"),
    "zksync": ("ZK", "ZKsync"),
}

ASSET_TO_CHAIN_OVERRIDE = {
    "ACM": ("CHZ", "Chiliz Chain"),
    "AFC": ("CHZ", "Chiliz Chain"),
    "ATM": ("CHZ", "Chiliz Chain"),
    "BAR": ("CHZ", "Chiliz Chain"),
    "CITY": ("CHZ", "Chiliz Chain"),
    "ENJ": ("ETH", "Ethereum"),
    "FCT2": ("FCT2", "FirmaChain"),
    "FET": ("ETH", "Ethereum"),
    "FORT": ("ETH", "Ethereum"),
    "FRAX": ("ETH", "Ethereum"),
    "HBD": ("HIVE", "Hive"),
    "INTER": ("CHZ", "Chiliz Chain"),
    "JUV": ("CHZ", "Chiliz Chain"),
    "MET2": ("SOL", "Solana"),
    "MTL": ("MTL", "Metal DAO"),
    "NAP": ("CHZ", "Chiliz Chain"),
    "PCI": ("ETH", "Ethereum"),
    "PSG": ("CHZ", "Chiliz Chain"),
    "RAD": ("ETH", "Ethereum"),
    "S": ("SONIC", "Sonic"),
    "SPURS": ("CHZ", "Chiliz Chain"),
    "TDROP": ("THETA", "Theta Network"),
    "TFUEL": ("THETA", "Theta Network"),
    "WAXL": ("AXL", "Axelar"),
    "XPL": ("XPL", "Plasma"),
}

MANUAL_MATCH_BY_SYMBOL = {
    "APE": 18876,
    "ASTER": 36341,
    "AVL": 35628,
    "BEAM": 3702,
    "BOB": 21882,
    "BRETT": 29743,
    "C": 37340,
    "DEEP": 33391,
    "DOGE": 74,
    "JUP": 29210,
    "MOODENG": 33093,
    "NEO": 1376,
    "PEPE": 24478,
    "SHIB": 5994,
    "SKY": 33038,
    "WLFI": 33251,
}


def get_json(url: str) -> Any:
    request = Request(
        url, headers={"accept": "application/json", "user-agent": "Mozilla/5.0"}
    )
    with urlopen(request, timeout=120) as response:
        return json.load(response)


def normalize(text: str | None) -> str:
    return "".join(ch for ch in (text or "").lower() if ch.isalnum())


def load_exchange_assets() -> tuple[dict[str, dict[str, Any]], dict[str, int]]:
    assets: dict[str, dict[str, Any]] = {}
    stats = {"bithumb_pairs": 0, "upbit_pairs": 0}
    for exchange, url, stat_key in [
        ("bithumb", BITHUMB_MARKETS_URL, "bithumb_pairs"),
        ("upbit", UPBIT_MARKETS_URL, "upbit_pairs"),
    ]:
        rows = get_json(url)
        stats[stat_key] = len(rows)
        for row in rows:
            _, base = row["market"].split("-")
            item = assets.setdefault(
                base.upper(),
                {
                    "english_names": set(),
                    "listed_on": set(),
                    "markets": defaultdict(list),
                },
            )
            item["english_names"].add(row["english_name"])
            item["listed_on"].add(exchange)
            item["markets"][exchange].append(row["market"])
    return assets, stats


def load_cmc_map() -> dict[str, list[dict[str, Any]]]:
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for url in CMC_MAP_URLS:
        data = get_json(url)
        for coin in data["data"]["cryptoCurrencyMap"]:
            by_symbol[coin["symbol"].upper()].append(coin)
    return by_symbol


def pick_cmc_coin(
    symbol: str,
    english_names: set[str],
    by_symbol: dict[str, list[dict[str, Any]]],
) -> dict[str, Any] | None:
    candidates = by_symbol.get(symbol, [])
    if len(candidates) == 1:
        return candidates[0]

    normalized_names = {normalize(name) for name in english_names}
    exact = [
        coin for coin in candidates if normalize(coin.get("name")) in normalized_names
    ]
    if len(exact) == 1:
        return exact[0]

    manual_id = MANUAL_MATCH_BY_SYMBOL.get(symbol)
    if manual_id is None:
        return None
    for coin in candidates:
        if coin["id"] == manual_id:
            return coin
    return None


def infer_chain(
    symbol: str,
    english_names: set[str],
    by_symbol: dict[str, list[dict[str, Any]]],
) -> tuple[tuple[str, str] | None, str | None, str]:
    if symbol in KNOWN_NATIVE_CHAINS:
        return (
            (symbol, KNOWN_NATIVE_CHAINS[symbol]),
            "native_asset",
            "known_native_ticker",
        )

    if symbol in ASSET_TO_CHAIN_OVERRIDE:
        return ASSET_TO_CHAIN_OVERRIDE[symbol], "host_chain", "asset_override"

    coin = pick_cmc_coin(symbol, english_names, by_symbol)
    if coin is None:
        return None, None, "unmatched_coin"

    platform = coin.get("platform")
    if not platform:
        return None, None, "no_platform"

    for key in [
        (platform.get("slug") or "").lower(),
        (platform.get("name") or "").lower(),
    ]:
        if key in PLATFORM_TO_CHAIN:
            return PLATFORM_TO_CHAIN[key], "host_chain", "platform_metadata"
    return None, None, "unknown_platform"


def load_current_targets() -> set[str]:
    if not TARGETS_FILE.exists():
        return set()
    with open(TARGETS_FILE, "r") as handle:
        config = json.load(handle)
    return {
        str(target.get("primary_ticker", "")).upper()
        for target in config.get("targets", [])
    }


def build_inventory() -> dict[str, Any]:
    assets, exchange_stats = load_exchange_assets()
    cmc_map = load_cmc_map()
    current_targets = load_current_targets()

    chains: dict[str, dict[str, Any]] = {}
    unresolved_assets: list[dict[str, Any]] = []

    for symbol, asset in sorted(assets.items()):
        chain, relation, method = infer_chain(symbol, asset["english_names"], cmc_map)
        if chain is None or relation is None:
            unresolved_assets.append(
                {
                    "ticker": symbol,
                    "english_names": sorted(asset["english_names"]),
                    "listed_on": sorted(asset["listed_on"]),
                    "markets": {
                        exchange: sorted(markets)
                        for exchange, markets in asset["markets"].items()
                    },
                    "reason": method,
                }
            )
            continue

        chain_ticker, chain_name = chain
        entry = chains.setdefault(
            chain_ticker,
            {
                "chain_ticker": chain_ticker,
                "chain_name": chain_name,
                "listed_on": set(),
                "native_assets": set(),
                "hosted_assets": set(),
                "detection_methods": set(),
                "current_01_target": chain_ticker in current_targets,
            },
        )
        entry["listed_on"].update(asset["listed_on"])
        entry["detection_methods"].add(method)
        if relation == "native_asset":
            entry["native_assets"].add(symbol)
        else:
            entry["hosted_assets"].add(symbol)

    serialized_chains = []
    for ticker in sorted(chains):
        item = chains[ticker]
        serialized_chains.append(
            {
                "chain_ticker": item["chain_ticker"],
                "chain_name": item["chain_name"],
                "listed_on": sorted(item["listed_on"]),
                "native_assets": sorted(item["native_assets"]),
                "hosted_assets": sorted(item["hosted_assets"]),
                "hosted_asset_count": len(item["hosted_assets"]),
                "detection_methods": sorted(item["detection_methods"]),
                "current_01_target": item["current_01_target"],
            }
        )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "as_of_date": date.today().isoformat(),
        "sources": {
            "bithumb_markets": BITHUMB_MARKETS_URL,
            "upbit_markets": UPBIT_MARKETS_URL,
            "coinmarketcap_map": CMC_MAP_URLS,
        },
        "stats": {
            **exchange_stats,
            "unique_base_assets": len(assets),
            "resolved_chain_count": len(serialized_chains),
            "unresolved_asset_count": len(unresolved_assets),
            "current_01_target_count": len(current_targets),
        },
        "chains": serialized_chains,
        "unresolved_assets": unresolved_assets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Where to write the inventory JSON",
    )
    args = parser.parse_args()

    inventory = build_inventory()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as handle:
        json.dump(inventory, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    print(f"Wrote {args.output}")
    print(json.dumps(inventory["stats"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
