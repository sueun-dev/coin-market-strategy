from __future__ import annotations

"""Bridge to the native C++ ultra engine for dedup/classify/buy."""

import ctypes
import logging
import os
import platform
from pathlib import Path

from .env_loader import MODULE_DIR, load_env_settings

logger = logging.getLogger(__name__)


def _is_truthy(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _library_suffix() -> str:
    system = platform.system().lower()
    if system == "darwin":
        return ".dylib"
    if system == "windows":
        return ".dll"
    return ".so"


class NativeUltraResultStruct(ctypes.Structure):
    _fields_ = [
        ("matched", ctypes.c_int),
        ("duplicate", ctypes.c_int),
        ("market_flags", ctypes.c_uint32),
        ("attempted", ctypes.c_int),
        ("executed", ctypes.c_int),
        ("ret_code", ctypes.c_int),
        ("ticker", ctypes.c_char * 16),
        ("asset_name", ctypes.c_char * 128),
        ("signal_type", ctypes.c_char * 16),
        ("symbol", ctypes.c_char * 24),
        ("order_id", ctypes.c_char * 64),
        ("order_link_id", ctypes.c_char * 40),
        ("transport", ctypes.c_char * 32),
        ("reason", ctypes.c_char * 128),
    ]


MARKET_FLAGS = (
    ("KRW", 1),
    ("BTC", 2),
    ("USDT", 4),
    ("ETH", 8),
)


def _decode_c_string(value: bytes) -> str:
    return value.split(b"\0", 1)[0].decode("utf-8", errors="ignore")


def _markets_from_flags(flags: int) -> list[str]:
    return [name for name, bit in MARKET_FLAGS if flags & bit]


def _payload_from_native_result(result: NativeUltraResultStruct) -> dict | None:
    if result.duplicate:
        return {
            "duplicate": True,
            "matched": False,
        }
    if not result.matched:
        return None
    return {
        "duplicate": False,
        "matched": True,
        "signal_type": _decode_c_string(result.signal_type),
        "ticker": _decode_c_string(result.ticker),
        "asset_name": _decode_c_string(result.asset_name),
        "markets": _markets_from_flags(int(result.market_flags)),
        "trade": {
            "enabled": True,
            "attempted": bool(result.attempted),
            "executed": bool(result.executed),
            "ret_code": int(result.ret_code),
            "symbol": _decode_c_string(result.symbol),
            "order_id": _decode_c_string(result.order_id),
            "order_link_id": _decode_c_string(result.order_link_id),
            "transport": _decode_c_string(result.transport),
            "reason": _decode_c_string(result.reason),
        },
    }


DEFAULT_LIBRARY = MODULE_DIR / "bin" / f"liblisting_ultra_engine{_library_suffix()}"


class CppUltraListingEngineBridge:
    """In-process bridge to the C++ ultra engine shared library."""

    def __init__(
        self,
        enabled: bool | None = None,
        library_path: str | Path | None = None,
    ):
        settings = load_env_settings(
            {
                "LISTING_CPP_ULTRA_ENGINE_ENABLED",
                "LISTING_CPP_ULTRA_ENGINE_PATH",
            }
        )
        self.enabled = (
            _is_truthy(settings.get("LISTING_CPP_ULTRA_ENGINE_ENABLED"))
            if enabled is None
            else bool(enabled)
        )
        self.library_path = Path(
            library_path
            or settings.get("LISTING_CPP_ULTRA_ENGINE_PATH")
            or DEFAULT_LIBRARY
        )
        self._prime_process_env()
        self._lib = None
        self._warmup = None
        self._handle = None
        self._load_error: str | None = None
        self._load()

    def is_enabled(self) -> bool:
        return self.enabled and self._handle is not None

    def warmup(self):
        if not self.is_enabled():
            return {"ok": False, "reason": self._load_error or "disabled"}
        status = self._warmup()
        return {"ok": status == 0, "status": int(status)}

    def handle_post(
        self,
        *,
        exchange: str,
        message_id: int,
        title: str,
    ) -> dict | None:
        return self.payload_from_raw(
            self.handle_post_raw(
                exchange=exchange,
                message_id=message_id,
                title=title,
            )
        )

    def handle_post_raw(
        self,
        *,
        exchange: str,
        message_id: int,
        title: str,
    ) -> NativeUltraResultStruct:
        if not self.is_enabled():
            return NativeUltraResultStruct()
        result = NativeUltraResultStruct()
        status = self._handle(
            exchange.encode("utf-8"),
            int(message_id),
            title.encode("utf-8"),
            ctypes.byref(result),
        )
        if status < 0:
            raise RuntimeError(f"cpp_ultra_engine_error:{status}")
        return result

    @staticmethod
    def payload_from_raw(result: NativeUltraResultStruct) -> dict | None:
        return _payload_from_native_result(result)

    def _load(self):
        if not self.enabled:
            return
        if not self.library_path.exists():
            self._load_error = f"library_missing:{self.library_path}"
            return
        try:
            self._lib = ctypes.CDLL(str(self.library_path))
            self._warmup = self._lib.listing_ultra_warmup
            self._warmup.argtypes = []
            self._warmup.restype = ctypes.c_int
            self._handle = self._lib.handle_listing_post
            self._handle.argtypes = [
                ctypes.c_char_p,
                ctypes.c_longlong,
                ctypes.c_char_p,
                ctypes.POINTER(NativeUltraResultStruct),
            ]
            self._handle.restype = ctypes.c_int
        except Exception as exc:
            self._handle = None
            self._warmup = None
            self._load_error = str(exc)
            logger.warning("Failed to load C++ ultra engine: %s", exc)

    @staticmethod
    def _prime_process_env():
        settings = load_env_settings(
            {
                "BYBIT_API_KEY",
                "BYBIT_API_SECRET",
                "BYBIT_API_BASE_URL",
                "BYBIT_RECV_WINDOW",
                "BYBIT_SPOT_BUY_ENABLED",
                "BYBIT_SPOT_BUY_USDT_AMOUNT",
                "BYBIT_PREFER_CACHED_SYMBOL_CHECK",
                "LISTING_CPP_ULTRA_ENGINE_ENABLED",
            }
        )
        for key, value in settings.items():
            if value and not os.environ.get(key):
                os.environ[key] = value
