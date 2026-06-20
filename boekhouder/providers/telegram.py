"""Telegram intake channel.

A real Bot API client used as the masterprompt's primary chat channel. ``poll`` long-
polls ``getUpdates`` for text and photo messages; ``send`` posts replies; ``download``
fetches an uploaded bonnetje so the OCR agent can read it. The whole class is inert
(no network) when ``BOEKHOUDER_TELEGRAM_TOKEN`` is unset, so importing it is always safe.
"""
from __future__ import annotations

import logging

import httpx

from boekhouder.config import get_settings
from boekhouder.providers.base import ChatChannel

log = logging.getLogger("boekhouder.telegram")


class TelegramChannel(ChatChannel):
    name = "telegram"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.token = self.settings.telegram_token
        self.api = f"https://api.telegram.org/bot{self.token}"
        self.file_api = f"https://api.telegram.org/file/bot{self.token}"

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    def send(self, chat_id: str, text: str) -> None:
        if not self.enabled:
            log.info("Telegram disabled; would send to %s: %s", chat_id, text[:80])
            return
        try:
            httpx.post(f"{self.api}/sendMessage",
                       json={"chat_id": chat_id, "text": text}, timeout=20)
        except Exception as exc:  # noqa: BLE001
            log.warning("Telegram send failed: %s", exc)

    def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[dict]:
        if not self.enabled:
            return []
        params = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        try:
            resp = httpx.get(f"{self.api}/getUpdates", params=params, timeout=timeout + 10)
            resp.raise_for_status()
            return resp.json().get("result", [])
        except Exception as exc:  # noqa: BLE001
            log.warning("Telegram getUpdates failed: %s", exc)
            return []

    def download_photo(self, file_id: str) -> bytes | None:
        if not self.enabled:
            return None
        try:
            info = httpx.get(f"{self.api}/getFile", params={"file_id": file_id}, timeout=20)
            path = info.json()["result"]["file_path"]
            return httpx.get(f"{self.file_api}/{path}", timeout=30).content
        except Exception as exc:  # noqa: BLE001
            log.warning("Telegram download failed: %s", exc)
            return None
