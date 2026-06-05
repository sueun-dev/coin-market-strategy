"""Bridge to the latency-critical C++ Bybit fast path process."""

from __future__ import annotations

import json
import logging
import os
import struct
import subprocess
import threading
from pathlib import Path

from .env_loader import MODULE_DIR, load_env_settings

logger = logging.getLogger(__name__)

DEFAULT_BINARY = MODULE_DIR / "bin" / "bybit_fast_path"
DEFAULT_BUILD_SCRIPT = MODULE_DIR / "cpp" / "build_fast_path.sh"


def _encode_frame(payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + payload


def _is_truthy(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


class CppFastBuyerBridge:
    """Persistent subprocess bridge for the C++ fast order executor."""

    def __init__(
        self,
        enabled: bool | None = None,
        binary_path: str | Path | None = None,
        build_script: str | Path | None = None,
        auto_build: bool | None = None,
    ):
        settings = load_env_settings(
            {
                "BYBIT_FAST_EXECUTOR_ENABLED",
                "BYBIT_FAST_EXECUTOR_PATH",
                "BYBIT_FAST_EXECUTOR_BUILD_SCRIPT",
                "BYBIT_FAST_EXECUTOR_AUTO_BUILD",
            }
        )
        self.enabled = (
            _is_truthy(settings.get("BYBIT_FAST_EXECUTOR_ENABLED"))
            if enabled is None
            else bool(enabled)
        )
        self.binary_path = Path(
            binary_path
            or settings.get("BYBIT_FAST_EXECUTOR_PATH")
            or DEFAULT_BINARY
        )
        self.build_script = Path(
            build_script
            or settings.get("BYBIT_FAST_EXECUTOR_BUILD_SCRIPT")
            or DEFAULT_BUILD_SCRIPT
        )
        self.auto_build = (
            _is_truthy(settings.get("BYBIT_FAST_EXECUTOR_AUTO_BUILD"))
            if auto_build is None
            else bool(auto_build)
        )
        self._lock = threading.Lock()
        self._proc: subprocess.Popen[bytes] | None = None
        self._ping_frame = _encode_frame(b"PING")

    def is_enabled(self) -> bool:
        return self.enabled

    def warmup(self):
        if not self.enabled:
            return
        with self._lock:
            self._ensure_process()
            self._request_locked(self._ping_frame)

    def ping(self) -> dict:
        with self._lock:
            self._ensure_process()
            response = self._request_locked(self._ping_frame)
        return self._parse_ping_response(response)

    def buy_market(self, *, symbol: str, quote_amount: float, order_link_id: str) -> dict:
        with self._lock:
            self._ensure_process()
            response = self._request_locked(
                _encode_frame(
                    f"BUY\t{symbol}\t{quote_amount:g}\t{order_link_id}".encode("utf-8")
                )
            )
        payload = self._parse_buy_response(response)
        payload.setdefault("symbol", symbol)
        payload.setdefault("attempted", False)
        payload.setdefault("executed", False)
        payload["requested_usdt"] = float(quote_amount)
        payload["transport"] = payload.get("transport", "cpp_fast_path")
        return payload

    def close(self):
        with self._lock:
            if self._proc is None:
                return
            proc = self._proc
            self._proc = None
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except Exception:
                proc.kill()

    def _ensure_process(self):
        if self._proc is not None and self._proc.poll() is None:
            return

        if not self.binary_path.exists():
            if not self.auto_build:
                raise RuntimeError(
                    f"C++ fast executor not found: {self.binary_path}"
                )
            self._build_binary()

        env = os.environ.copy()
        env.update(
            load_env_settings(
                {
                    "BYBIT_API_KEY",
                    "BYBIT_API_SECRET",
                    "BYBIT_API_BASE_URL",
                    "BYBIT_RECV_WINDOW",
                    "BYBIT_SPOT_BUY_ENABLED",
                    "BYBIT_SPOT_BUY_USDT_AMOUNT",
                }
            )
        )
        self._proc = subprocess.Popen(
            [str(self.binary_path), "--server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            cwd=str(MODULE_DIR),
            env=env,
        )
        logger.info("C++ fast executor started: %s", self.binary_path)

    def _build_binary(self):
        if not self.build_script.exists():
            raise RuntimeError(f"Build script not found: {self.build_script}")
        subprocess.run(
            [str(self.build_script)],
            cwd=str(MODULE_DIR),
            check=True,
            text=True,
        )

    def _request_locked(self, frame: bytes) -> bytes:
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise RuntimeError("C++ fast executor is not running")
        self._proc.stdin.write(frame)
        self._proc.stdin.flush()
        header = self._read_exact_locked(4)
        if not header:
            stderr_text = ""
            if self._proc.poll() is not None and self._proc.stderr is not None:
                try:
                    stderr_text = self._proc.stderr.read().decode("utf-8", errors="ignore")
                except Exception:
                    stderr_text = ""
            raise RuntimeError(
                f"C++ fast executor returned no response. stderr={stderr_text}"
            )
        size = struct.unpack(">I", header)[0]
        if size == 0:
            return b""
        response = self._read_exact_locked(size)
        if len(response) != size:
            raise RuntimeError("C++ fast executor returned truncated response")
        return response

    def _read_exact_locked(self, size: int) -> bytes:
        if self._proc is None or self._proc.stdout is None:
            raise RuntimeError("C++ fast executor is not running")
        chunks: list[bytes] = []
        remaining = size
        while remaining > 0:
            chunk = self._proc.stdout.read(remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    @staticmethod
    def _parse_ping_response(response: bytes) -> dict:
        if response == b"PONG":
            return {"ok": True, "pong": True}
        return json.loads(response.decode("utf-8"))

    @staticmethod
    def _parse_buy_response(response: bytes) -> dict:
        if not response.startswith(b"BUY\t"):
            return json.loads(response.decode("utf-8"))

        parts = response.split(b"\t", 7)
        if len(parts) < 8:
            raise RuntimeError(
                f"Malformed C++ fast executor response: {response!r}"
            )

        _, executed, attempted, symbol, order_id, ret_code, transport, reason = parts
        payload = {
            "executed": executed == b"1",
            "attempted": attempted == b"1",
            "symbol": symbol.decode("utf-8", errors="ignore"),
            "order_id": order_id.decode("utf-8", errors="ignore"),
            "ret_code": int(ret_code or b"-1"),
            "transport": transport.decode("utf-8", errors="ignore") or "cpp_fast_path",
        }
        if reason:
            payload["reason"] = reason.decode("utf-8", errors="ignore")
        return payload
