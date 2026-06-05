"""Realtime Telegram source using TDLib via a lightweight relay process."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty, Queue

from .env_loader import MODULE_DIR, load_env_settings
from .telegram_realtime_client import RealtimeTelegramChannelClient

logger = logging.getLogger(__name__)

DEFAULT_RELAY_PATH = MODULE_DIR / "bin" / "tdlib_json_relay"
DEFAULT_DB_DIR = MODULE_DIR / "data" / "tdlib_source_db"


class _TdlibEvent:
    def __init__(self, received_monotonic_ns: int, payload: dict):
        self.received_monotonic_ns = received_monotonic_ns
        self.payload = payload


class _TdlibRelay:
    def __init__(self, relay_path: Path):
        self.relay_path = relay_path
        self.proc: subprocess.Popen[str] | None = None
        self.queue: Queue[_TdlibEvent] = Queue()
        self.clock_queue: Queue[int] = Queue()
        self._reader: threading.Thread | None = None
        self._async_loop: asyncio.AbstractEventLoop | None = None
        self._async_queue: asyncio.Queue[_TdlibEvent] | None = None

    def start(self):
        if not self.relay_path.exists():
            raise RuntimeError(f"TDLib relay binary not found: {self.relay_path}")
        self.proc = subprocess.Popen(
            [str(self.relay_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert self.proc.stdout is not None
        line = self.proc.stdout.readline().strip()
        if line != "__relay_ready__":
            raise RuntimeError(f"TDLib relay failed to start: {line}")
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self):
        assert self.proc is not None
        assert self.proc.stdout is not None
        for raw_line in self.proc.stdout:
            line = raw_line.strip()
            if line.startswith("__clock__\t"):
                try:
                    _, value = line.split("\t", 1)
                    self.clock_queue.put(int(value))
                except ValueError:
                    pass
                continue
            if not line or "\t" not in line:
                continue
            prefix, payload = line.split("\t", 1)
            try:
                event = _TdlibEvent(
                    received_monotonic_ns=int(prefix),
                    payload=json.loads(payload),
                )
            except (ValueError, json.JSONDecodeError):
                continue
            self.queue.put(event)
            if self._async_loop is not None and self._async_queue is not None:
                self._async_loop.call_soon_threadsafe(
                    self._async_queue.put_nowait,
                    event,
                )

    def attach_async_loop(self, loop: asyncio.AbstractEventLoop):
        self._async_loop = loop
        self._async_queue = asyncio.Queue()

    def send(self, obj: dict):
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("TDLib relay not started")
        self.proc.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def send_raw(self, line: str):
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("TDLib relay not started")
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def wait_for(self, predicate, timeout: float) -> _TdlibEvent:
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("TDLib relay timed out")
            try:
                event = self.queue.get(timeout=remaining)
            except Empty as exc:
                raise TimeoutError("TDLib relay timed out") from exc
            if predicate(event):
                return event

    def send_request(self, obj: dict, timeout: float = 10.0) -> dict:
        extra = f"req-{uuid.uuid4().hex}"
        payload = dict(obj)
        payload["@extra"] = extra
        self.send(payload)
        event = self.wait_for(lambda event: event.payload.get("@extra") == extra, timeout=timeout)
        return event.payload

    async def async_wait_for(self, predicate, timeout: float) -> _TdlibEvent:
        if self._async_queue is None:
            raise RuntimeError("TDLib relay async queue not attached")
        while True:
            event = await asyncio.wait_for(self._async_queue.get(), timeout=timeout)
            if predicate(event):
                return event

    def measure_clock_offset_ns(self, attempts: int = 7) -> int:
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("TDLib relay not started")
        samples: list[tuple[int, int]] = []
        for _ in range(attempts):
            start_ns = time.monotonic_ns()
            self.proc.stdin.write("__clock__\n")
            self.proc.stdin.flush()
            relay_ns = self.clock_queue.get(timeout=5)
            end_ns = time.monotonic_ns()
            midpoint_ns = (start_ns + end_ns) // 2
            samples.append((end_ns - start_ns, relay_ns - midpoint_ns))
        samples.sort(key=lambda item: item[0])
        return samples[0][1]

    def close(self):
        if self.proc is not None and self.proc.stdin is not None:
            try:
                self.proc.stdin.write("__quit__\n")
                self.proc.stdin.flush()
            except BrokenPipeError:
                pass
        if self.proc is not None:
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()


class TdlibRealtimeChannelClient:
    """Listen to new Telegram messages from target channels in realtime via TDLib."""

    def __init__(
        self,
        api_id: int | None = None,
        api_hash: str | None = None,
        phone: str | None = None,
        relay_path: str | Path | None = None,
        database_dir: str | Path | None = None,
    ):
        settings = load_env_settings(
            {
                "LISTING_SOURCE_TELEGRAM_API_ID",
                "LISTING_SOURCE_TELEGRAM_API_HASH",
                "LISTING_SOURCE_TELEGRAM_PHONE",
            }
        )
        self.api_id = int(api_id or settings.get("LISTING_SOURCE_TELEGRAM_API_ID") or 0)
        self.api_hash = api_hash or settings.get("LISTING_SOURCE_TELEGRAM_API_HASH", "")
        self.phone = phone or settings.get("LISTING_SOURCE_TELEGRAM_PHONE", "")
        self.relay_path = Path(relay_path or DEFAULT_RELAY_PATH)
        self.database_dir = Path(database_dir or DEFAULT_DB_DIR)
        self.database_dir.mkdir(parents=True, exist_ok=True)

    def is_configured(self) -> bool:
        return bool(self.api_id and self.api_hash and self.phone)

    def has_session_file(self) -> bool:
        return self.database_dir.exists() and any(self.database_dir.iterdir())

    def _tdlib_parameter_fields(self) -> dict:
        return {
            "database_directory": str(self.database_dir),
            "files_directory": str(self.database_dir / "files"),
            "database_encryption_key": "",
            "use_message_database": True,
            "use_secret_chats": False,
            "use_chat_info_database": True,
            "use_file_database": False,
            "use_test_dc": False,
            "api_id": int(self.api_id),
            "api_hash": self.api_hash,
            "system_language_code": "en",
            "device_model": "Codex TDLib Source",
            "system_version": "macOS",
            "application_version": "11.7",
            "enable_storage_optimizer": False,
            "ignore_file_names": True,
        }

    def _tdlib_send_auth_parameters(self, relay: _TdlibRelay, *, legacy: bool = False):
        fields = self._tdlib_parameter_fields()
        if legacy:
            fields.pop("database_encryption_key", None)
            relay.send(
                {
                    "@type": "setTdlibParameters",
                    "parameters": {
                        "@type": "tdlibParameters",
                        **fields,
                    },
                }
            )
            return
        relay.send({"@type": "setTdlibParameters", **fields})

    @staticmethod
    def _is_auth_state(payload: dict, name: str) -> bool:
        if payload.get("@type") == name:
            return True
        if payload.get("@type") != "updateAuthorizationState":
            return False
        state = payload.get("authorization_state", {})
        return state.get("@type") == name

    def _ensure_ready(self, relay: _TdlibRelay, interactive: bool):
        sent_parameters = False
        sent_legacy_parameters = False
        sent_phone_number = False
        sent_encryption_key = False

        relay.send({"@type": "getAuthorizationState"})
        while True:
            event = relay.wait_for(lambda _: True, timeout=60)
            payload = event.payload
            if self._is_auth_state(payload, "authorizationStateWaitTdlibParameters"):
                if not sent_parameters:
                    self._tdlib_send_auth_parameters(relay)
                    sent_parameters = True
                continue
            if self._is_auth_state(payload, "authorizationStateWaitEncryptionKey"):
                if not sent_encryption_key:
                    relay.send({"@type": "checkDatabaseEncryptionKey", "encryption_key": ""})
                    sent_encryption_key = True
                continue
            if self._is_auth_state(payload, "authorizationStateWaitPhoneNumber"):
                if not sent_phone_number:
                    relay.send(
                        {
                            "@type": "setAuthenticationPhoneNumber",
                            "phone_number": self.phone,
                        }
                    )
                    sent_phone_number = True
                continue
            if self._is_auth_state(payload, "authorizationStateWaitCode"):
                if not interactive:
                    raise RuntimeError(
                        "TDLib authorization code required. Run `python main.py --login-source-telegram --realtime-backend tdlib` first."
                    )
                code = input(f"TDLib Telegram code for {self.phone}: ").strip()
                relay.send({"@type": "checkAuthenticationCode", "code": code})
                continue
            if self._is_auth_state(payload, "authorizationStateWaitPassword"):
                if not interactive:
                    raise RuntimeError(
                        "TDLib 2FA password required. Run `python main.py --login-source-telegram --realtime-backend tdlib` first."
                    )
                password = input("TDLib Telegram 2FA password: ").strip()
                relay.send({"@type": "checkAuthenticationPassword", "password": password})
                continue
            if self._is_auth_state(payload, "authorizationStateReady"):
                return
            if self._is_auth_state(payload, "authorizationStateClosed"):
                raise RuntimeError("TDLib authorization closed unexpectedly")
            if payload.get("@type") == "error":
                message = str(payload.get("message", ""))
                if "Parameters" in message and "specified" in message and not sent_parameters:
                    self._tdlib_send_auth_parameters(relay)
                    sent_parameters = True
                    continue
                if (
                    "Parameters" in message
                    and "specified" in message
                    and sent_parameters
                    and not sent_legacy_parameters
                ):
                    self._tdlib_send_auth_parameters(relay, legacy=True)
                    sent_legacy_parameters = True
                    continue
                raise RuntimeError(f"TDLib error during auth: {payload.get('message', payload)}")

    async def login_interactive(self) -> bool:
        if not self.is_configured():
            raise RuntimeError("LISTING_SOURCE_TELEGRAM_API_ID/API_HASH/PHONE 설정이 필요합니다.")
        relay = _TdlibRelay(self.relay_path)
        await asyncio.to_thread(relay.start)
        try:
            await asyncio.to_thread(self._ensure_ready, relay, True)
            return True
        finally:
            await asyncio.to_thread(relay.close)

    @staticmethod
    def _extract_text(payload: dict) -> str:
        if payload.get("@type") != "updateNewMessage":
            return ""
        message = payload.get("message", {})
        content = message.get("content", {})
        if content.get("@type") != "messageText":
            return ""
        return (content.get("text", {}) or {}).get("text", "") or ""

    async def run(
        self,
        channel_handles: list[str],
        on_post,
        minimal_post: bool = False,
        trade_post: bool = False,
    ):
        if not self.is_configured():
            raise RuntimeError("LISTING_SOURCE_TELEGRAM_API_ID/API_HASH/PHONE 설정이 필요합니다.")

        relay = _TdlibRelay(self.relay_path)
        await asyncio.to_thread(relay.start)
        try:
            await asyncio.to_thread(self._ensure_ready, relay, False)
            clock_offset_ns = await asyncio.to_thread(relay.measure_clock_offset_ns)

            chat_id_to_handle: dict[int, str] = {}
            for handle in channel_handles:
                username = handle.lstrip("@")
                response = await asyncio.to_thread(
                    relay.send_request,
                    {"@type": "searchPublicChat", "username": username},
                    20,
                )
                if response.get("@type") != "chat":
                    raise RuntimeError(f"TDLib failed to resolve chat {username}: {response}")
                chat_id_to_handle[int(response["id"])] = username

            relay.attach_async_loop(asyncio.get_running_loop())

            native_listing_mode = bool(trade_post)
            if native_listing_mode:
                watch_spec = ",".join(
                    f"{chat_id}:{handle}"
                    for chat_id, handle in chat_id_to_handle.items()
                )
                await asyncio.to_thread(relay.send_raw, f"__watch_chats__\t{watch_spec}")
                await asyncio.to_thread(relay.send_raw, "__native_listing_on__")

            logger.info(
                "실시간 텔레그램 감시 시작 (TDLib) — %s",
                ", ".join(channel_handles),
            )

            while True:
                event = await relay.async_wait_for(
                    lambda event: event.payload.get("@type") in {"updateNewMessage", "listingMatched"},
                    3600,
                )
                payload = event.payload
                if payload.get("@type") == "listingMatched":
                    received_monotonic_ns = int(event.received_monotonic_ns) - clock_offset_ns
                    published_at = datetime.fromtimestamp(
                        int(payload.get("published_at_unix", 0)),
                        tz=timezone.utc,
                    )
                    post = {
                        "channel_handle": payload["channel_handle"],
                        "message_id": int(payload["message_id"]),
                        "published_at": published_at.isoformat(),
                        "received_monotonic_ns": received_monotonic_ns,
                        "title": payload.get("title", ""),
                        "text": payload.get("title", ""),
                        "post_url": f"https://t.me/{payload['channel_handle']}/{int(payload['message_id'])}",
                        "native_listing": {
                            "exchange": payload.get("exchange", ""),
                            "signal_type": payload.get("signal_type", ""),
                            "ticker": payload.get("ticker", ""),
                            "asset_name": payload.get("asset_name", ""),
                            "markets": list(payload.get("markets", [])),
                        },
                    }
                    maybe_result = on_post(post)
                    if hasattr(maybe_result, "__await__"):
                        await maybe_result
                    continue
                message = payload.get("message", {})
                chat_id = int(message.get("chat_id", 0))
                handle = chat_id_to_handle.get(chat_id)
                if handle is None:
                    continue
                text = self._extract_text(payload)
                if not text:
                    continue

                published_at = datetime.fromtimestamp(
                    int(message.get("date", 0)),
                    tz=timezone.utc,
                )
                received_monotonic_ns = int(event.received_monotonic_ns) - clock_offset_ns
                if trade_post:
                    title = RealtimeTelegramChannelClient.extract_title(text)
                    if not title:
                        continue
                    post = RealtimeTelegramChannelClient.build_trade_post(
                        channel_handle=handle,
                        message_id=int(message["id"]),
                        text=text,
                        published_at=published_at,
                        received_monotonic_ns=received_monotonic_ns,
                        title=title,
                    )
                elif minimal_post:
                    if not RealtimeTelegramChannelClient.has_nonspace(text):
                        continue
                    received_at = datetime.now(timezone.utc)
                    post = RealtimeTelegramChannelClient.build_minimal_post(
                        channel_handle=handle,
                        message_id=int(message["id"]),
                        text=text,
                        published_at=published_at,
                        received_at=received_at,
                        received_monotonic_ns=received_monotonic_ns,
                    )
                else:
                    if not RealtimeTelegramChannelClient.has_nonspace(text):
                        continue
                    received_at = datetime.now(timezone.utc)
                    post = RealtimeTelegramChannelClient.build_post(
                        channel_handle=handle,
                        message_id=int(message["id"]),
                        text=text,
                        published_at=published_at,
                        received_at=received_at,
                        received_monotonic_ns=received_monotonic_ns,
                    )

                maybe_result = on_post(post)
                if hasattr(maybe_result, "__await__"):
                    await maybe_result
        finally:
            await asyncio.to_thread(relay.close)
