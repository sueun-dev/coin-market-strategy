from __future__ import annotations

"""Race Telethon, TDLib, and Pyrogram; accept the first arrival for each Telegram post."""

import asyncio
import logging

from .tdlib_realtime_client import TdlibRealtimeChannelClient
from .telegram_realtime_client import RealtimeTelegramChannelClient

logger = logging.getLogger(__name__)

# Lazy import: Pyrogram may not be installed on all environments.
_pyrogram_client_class = None


def _get_pyrogram_client_class():
    global _pyrogram_client_class
    if _pyrogram_client_class is not None:
        return _pyrogram_client_class
    try:
        from .pyrogram_realtime_client import PyrogramRealtimeChannelClient

        _pyrogram_client_class = PyrogramRealtimeChannelClient
    except ImportError:
        _pyrogram_client_class = None
    return _pyrogram_client_class


class _FirstArrivalGate:
    def __init__(self, max_entries: int = 8192):
        self._last_message_id_by_channel: dict[str, int] = {}

    def claim(self, channel_handle: str, message_id: int) -> bool:
        message_id = int(message_id)
        last_message_id = self._last_message_id_by_channel.get(channel_handle, 0)
        if message_id <= last_message_id:
            return False
        self._last_message_id_by_channel[channel_handle] = message_id
        return True


class RaceRealtimeChannelClient:
    """Run all available realtime backends and forward only the earliest event per post."""

    _UNSET = object()

    def __init__(
        self,
        telethon_client: RealtimeTelegramChannelClient | None = None,
        tdlib_client: TdlibRealtimeChannelClient | None = None,
        pyrogram_client=_UNSET,
        gate_max_entries: int = 8192,
    ):
        self.telethon = telethon_client or RealtimeTelegramChannelClient()
        self.tdlib = tdlib_client or TdlibRealtimeChannelClient()
        self._gate = _FirstArrivalGate(max_entries=gate_max_entries)

        # Auto-create Pyrogram client only when not explicitly passed
        if pyrogram_client is not self._UNSET:
            # Caller explicitly set pyrogram_client (including None = disable)
            self.pyrogram = pyrogram_client
        else:
            cls = _get_pyrogram_client_class()
            if cls is not None:
                try:
                    self.pyrogram = cls()
                except Exception:
                    self.pyrogram = None
            else:
                self.pyrogram = None

    def _configured_backends(self) -> list[tuple[str, object]]:
        backends: list[tuple[str, object]] = []
        if self.telethon.is_configured():
            backends.append(("telethon", self.telethon))
        if self.tdlib.is_configured():
            backends.append(("tdlib", self.tdlib))
        if self.pyrogram is not None and self.pyrogram.is_configured():
            backends.append(("pyrogram", self.pyrogram))
        return backends

    def _session_ready_backends(self) -> list[tuple[str, object]]:
        return [
            (name, client)
            for name, client in self._configured_backends()
            if client.has_session_file()
        ]

    def is_configured(self) -> bool:
        return bool(self._configured_backends())

    def has_session_file(self) -> bool:
        return bool(self._session_ready_backends())

    async def login_interactive(self) -> bool:
        successes = 0
        for name, client in self._configured_backends():
            try:
                if await client.login_interactive():
                    successes += 1
            except Exception as exc:
                logger.warning("%s login failed (non-fatal): %s", name, exc)
        return successes > 0

    async def run(
        self,
        channel_handles: list[str],
        on_post,
        minimal_post: bool = False,
        trade_post: bool = False,
    ):
        async def _first_wins(post: dict):
            claimed = self._gate.claim(
                post["channel_handle"],
                int(post["message_id"]),
            )
            if not claimed:
                return None
            maybe_result = on_post(post)
            if hasattr(maybe_result, "__await__"):
                return await maybe_result
            return maybe_result

        async def _run_backend(name: str, client):
            try:
                await client.run(
                    channel_handles=channel_handles,
                    on_post=_first_wins,
                    minimal_post=minimal_post,
                    trade_post=trade_post,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("%s realtime backend dropped out: %s", name, exc)

        active_backends = self._session_ready_backends()
        if not active_backends:
            raise RuntimeError(
                "race realtime 백엔드에 로그인된 세션이 없습니다. "
                "Telethon/TDLib/Pyrogram 중 하나 이상 로그인하세요."
            )

        backend_names = [name for name, _ in active_backends]
        logger.info("%d-way race 활성: %s", len(backend_names), " + ".join(name.title() for name in backend_names))
        tasks = [
            asyncio.create_task(
                _run_backend(name, client),
                name=f"{name}-race-listener",
            )
            for name, client in active_backends
        ]

        try:
            await asyncio.gather(*tasks)
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
