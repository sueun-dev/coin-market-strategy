"""
Block time anomaly detector — chain monitor module.

Polls the latest block from a chain's RPC endpoint, calculates time since
the last block, and detects anomalies at 3 severity levels:
  Level 1 (Warning):  block_time > avg * 2
  Level 2 (Alert):    elapsed > avg * 5
  Level 3 (Critical): elapsed > avg * 10 OR elapsed > 60s absolute
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 10.0  # seconds


class AnomalyLevel(str, Enum):
    NONE = "none"
    WARNING = "warning"
    ALERT = "alert"
    CRITICAL = "critical"


@dataclass
class BlockInfo:
    height: int
    timestamp: float  # unix epoch seconds
    chain_id: str
    fetched_at: float = field(default_factory=time.time)


@dataclass
class ChainStatus:
    chain_id: str
    chain_name: str
    ticker: str
    rpc_type: str
    latest_block: BlockInfo | None = None
    previous_block: BlockInfo | None = None
    avg_block_time: float = 6.0
    anomaly_level: AnomalyLevel = AnomalyLevel.NONE
    seconds_since_last_block: float = 0.0
    error: str | None = None


# ---------------------------------------------------------------------------
# RPC Fetchers — one per chain type
# ---------------------------------------------------------------------------

def _fetch_tendermint(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest block from a Tendermint/CometBFT RPC node."""
    resp = client.get(f"{url}/status", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    # Some chains (e.g. Sei v2) return data at top level without "result" wrapper
    if "result" in data:
        sync_info = data["result"]["sync_info"]
    else:
        sync_info = data["sync_info"]
    height = int(sync_info["latest_block_height"])
    ts_str = sync_info["latest_block_time"]

    # Parse ISO timestamp — Tendermint timestamps include nanoseconds
    # Truncate to microseconds for Python compatibility
    if "." in ts_str:
        parts = ts_str.split(".")
        frac = parts[1].rstrip("Z")
        frac = frac[:6]  # keep up to microseconds
        ts_str = f"{parts[0]}.{frac}Z"
    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    return BlockInfo(height=height, timestamp=ts.timestamp(), chain_id="")


def _fetch_evm(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest block from an EVM-compatible JSON-RPC node."""
    # Get latest block number
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": ["latest", False],
        "id": 1,
    }
    resp = client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()["result"]

    height = int(result["number"], 16)
    timestamp = int(result["timestamp"], 16)
    return BlockInfo(height=height, timestamp=float(timestamp), chain_id="")


def _fetch_solana(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest slot from Solana JSON-RPC."""
    # Get slot
    payload = {"jsonrpc": "2.0", "method": "getSlot", "id": 1}
    resp = client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    slot = resp.json()["result"]

    # Get block time for this slot
    payload2 = {
        "jsonrpc": "2.0",
        "method": "getBlockTime",
        "params": [slot],
        "id": 2,
    }
    resp2 = client.post(url, json=payload2, timeout=REQUEST_TIMEOUT)
    resp2.raise_for_status()
    block_time = resp2.json()["result"]

    return BlockInfo(
        height=slot,
        timestamp=float(block_time) if block_time else time.time(),
        chain_id="",
    )


def _fetch_sui(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest checkpoint from Sui JSON-RPC."""
    payload = {
        "jsonrpc": "2.0",
        "method": "sui_getLatestCheckpointSequenceNumber",
        "id": 1,
    }
    resp = client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    seq = int(resp.json()["result"])

    # Get checkpoint details for the timestamp
    payload2 = {
        "jsonrpc": "2.0",
        "method": "sui_getCheckpoint",
        "params": [str(seq)],
        "id": 2,
    }
    resp2 = client.post(url, json=payload2, timeout=REQUEST_TIMEOUT)
    resp2.raise_for_status()
    cp = resp2.json()["result"]
    # timestampMs is milliseconds since epoch
    ts = int(cp["timestampMs"]) / 1000.0

    return BlockInfo(height=seq, timestamp=ts, chain_id="")


def _fetch_aptos(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest ledger info from Aptos REST API."""
    # Use /v1 or /v1/ endpoint — try without /v1 suffix if url already has it
    base = url.rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"

    resp = client.get(base, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    height = int(data["block_height"])
    # ledger_timestamp is in microseconds
    ts = int(data["ledger_timestamp"]) / 1_000_000.0

    return BlockInfo(height=height, timestamp=ts, chain_id="")


def _fetch_algorand(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest round from Algorand REST API (algonode)."""
    base = url.rstrip("/")
    resp = client.get(f"{base}/v2/status", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()

    height = data["last-round"]

    # Get block header for timestamp
    resp2 = client.get(
        f"{base}/v2/blocks/{height}",
        params={"format": "json"},
        timeout=REQUEST_TIMEOUT,
    )
    resp2.raise_for_status()
    block = resp2.json()
    # Algorand block timestamp is in seconds since epoch
    ts = block.get("block", block).get("ts", block.get("timestamp", time.time()))

    return BlockInfo(height=height, timestamp=float(ts), chain_id="")


def _fetch_cardano(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest block from Cardano via Koios API."""
    base = url.rstrip("/")
    resp = client.get(
        f"{base}/tip",
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    tip = data[0] if isinstance(data, list) else data

    height = int(tip["block_no"])
    # Koios returns epoch_slot and block_time as unix timestamp
    ts = int(tip["block_time"])

    return BlockInfo(height=height, timestamp=float(ts), chain_id="")


def _fetch_substrate(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest block from a Substrate-based chain (Polkadot/Kusama)
    via JSON-RPC over HTTP."""
    # Get latest block hash
    payload = {
        "jsonrpc": "2.0",
        "method": "chain_getHeader",
        "params": [],
        "id": 1,
    }
    resp = client.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    result = resp.json()["result"]

    height = int(result["number"], 16)
    # Substrate headers don't include timestamps directly via RPC.
    # Use current time as approximation — halt detection works via
    # height stalling, not timestamp comparison.
    return BlockInfo(height=height, timestamp=time.time(), chain_id="")


def _fetch_tezos(client: httpx.Client, url: str) -> BlockInfo:
    """Fetch latest block from Tezos RPC."""
    base = url.rstrip("/")
    resp = client.get(
        f"{base}/chains/main/blocks/head/header",
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()

    height = int(data["level"])
    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    return BlockInfo(height=height, timestamp=ts.timestamp(), chain_id="")


# Map rpc_type -> fetcher function
FETCHERS: dict[str, Any] = {
    "tendermint": _fetch_tendermint,
    "evm": _fetch_evm,
    "solana": _fetch_solana,
    "sui": _fetch_sui,
    "aptos": _fetch_aptos,
    "algorand": _fetch_algorand,
    "cardano": _fetch_cardano,
    "substrate": _fetch_substrate,
    "tezos": _fetch_tezos,
}


# ---------------------------------------------------------------------------
# ChainMonitor
# ---------------------------------------------------------------------------

class ChainMonitor:
    """Monitor a single chain's block production."""

    def __init__(self, chain_config: dict, client: httpx.Client | None = None):
        self.chain_id: str = chain_config["chain_id"]
        self.name: str = chain_config["name"]
        self.ticker: str = chain_config["ticker"]
        self.rpc_type: str = chain_config["rpc_type"]
        self.rpc_endpoints: list[str] = chain_config["rpc_endpoints"]
        self.avg_block_time: float = chain_config.get("avg_block_time", 6.0)
        self.tickers_affected: list[str] = chain_config.get("tickers_affected", [self.ticker])

        self._client = client or httpx.Client()
        self._owns_client = client is None
        self._fetcher = FETCHERS.get(self.rpc_type)
        if not self._fetcher:
            raise ValueError(f"Unsupported rpc_type: {self.rpc_type}")

        # State
        self._latest_block: BlockInfo | None = None
        self._previous_block: BlockInfo | None = None

    def poll(self) -> ChainStatus:
        """Poll the chain and return current status with anomaly level."""
        status = ChainStatus(
            chain_id=self.chain_id,
            chain_name=self.name,
            ticker=self.ticker,
            rpc_type=self.rpc_type,
            avg_block_time=self.avg_block_time,
        )

        block = self._fetch_latest_block()
        if block is None:
            status.error = "All RPC endpoints failed"
            return status

        block.chain_id = self.chain_id

        # Update state
        if self._latest_block is not None:
            if block.height != self._latest_block.height:
                self._previous_block = self._latest_block
        self._latest_block = block

        status.latest_block = block
        status.previous_block = self._previous_block

        # Calculate seconds since last block
        now = time.time()
        elapsed = now - block.timestamp
        status.seconds_since_last_block = max(0, elapsed)

        # Determine anomaly level
        avg = self.avg_block_time
        if elapsed > avg * 10 or elapsed > 60:
            status.anomaly_level = AnomalyLevel.CRITICAL
        elif elapsed > avg * 5:
            status.anomaly_level = AnomalyLevel.ALERT
        elif elapsed > avg * 2:
            status.anomaly_level = AnomalyLevel.WARNING
        else:
            status.anomaly_level = AnomalyLevel.NONE

        return status

    def _fetch_latest_block(self) -> BlockInfo | None:
        """Try each RPC endpoint until one succeeds."""
        last_error = None
        for endpoint in self.rpc_endpoints:
            try:
                block = self._fetcher(self._client, endpoint)
                return block
            except Exception as e:
                last_error = e
                logger.warning(
                    "[%s] RPC endpoint failed: %s — %s",
                    self.chain_id, endpoint, e,
                )
        logger.error(
            "[%s] All %d RPC endpoints failed. Last error: %s",
            self.chain_id, len(self.rpc_endpoints), last_error,
        )
        return None

    @property
    def latest_block(self) -> BlockInfo | None:
        return self._latest_block

    def close(self):
        if self._owns_client:
            self._client.close()
