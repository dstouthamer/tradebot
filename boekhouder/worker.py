"""Telegram long-poll worker — the real intake channel.

Run:  python -m boekhouder.worker   (needs BOEKHOUDER_TELEGRAM_TOKEN)

Receives text and photo messages, routes them through the same ``Router`` as every
other surface, and replies in the chat. Inert/exits cleanly if no token is configured.
"""
from __future__ import annotations

import logging
import time

from boekhouder.config import get_settings
from boekhouder.engine.router import Router
from boekhouder.providers.telegram import TelegramChannel

log = logging.getLogger("boekhouder.worker")


def run() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    channel = TelegramChannel()
    if not channel.enabled:
        log.warning("BOEKHOUDER_TELEGRAM_TOKEN niet gezet — worker stopt.")
        return
    router = Router()
    log.info("Telegram-worker gestart voor %s.", settings.company_name)
    offset: int | None = None
    while True:
        for update in channel.get_updates(offset=offset, timeout=30):
            offset = update["update_id"] + 1
            msg = update.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = msg.get("text") or msg.get("caption") or ""
            image_bytes = None
            if msg.get("photo"):
                image_bytes = channel.download_photo(msg["photo"][-1]["file_id"])
                text = text or "bonnetje"
            if not chat_id or (not text and not image_bytes):
                continue
            try:
                reply = router.handle(text, session_id=chat_id, image_bytes=image_bytes)
                channel.send(chat_id, reply.text)
            except Exception as exc:  # noqa: BLE001 - keep the worker alive
                log.exception("Verwerking mislukt: %s", exc)
                channel.send(chat_id, "Er ging iets mis bij het verwerken. Probeer opnieuw.")
        time.sleep(1)


if __name__ == "__main__":
    run()
