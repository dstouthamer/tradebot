"""WhatsApp-intakekanaal via de Meta WhatsApp Cloud API.

Officieel kan WhatsApp alleen via de WhatsApp Business API. Deze klasse praat met de
gratis-tier **Meta Cloud API**: berichten versturen, inkomende webhooks verifiëren en
media (foto's van bonnen) ophalen. De klasse is inert zonder configuratie, dus importeren
is altijd veilig.

Activeren (zie docs/INTEGRATIONS.md):
  BOEKHOUDER_WHATSAPP_TOKEN          (permanent access token van je Meta-app)
  BOEKHOUDER_WHATSAPP_PHONE_ID       (phone number id)
  BOEKHOUDER_WHATSAPP_VERIFY_TOKEN   (zelfgekozen string voor webhook-verificatie)
"""
from __future__ import annotations

import logging

import httpx

from boekhouder.config import get_settings

log = logging.getLogger("boekhouder.whatsapp")

_GRAPH = "https://graph.facebook.com/v20.0"


class WhatsAppChannel:
    name = "whatsapp"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.token = self.settings.whatsapp_token
        self.phone_id = self.settings.whatsapp_phone_id

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.phone_id)

    def send(self, to: str, text: str) -> None:
        if not self.enabled:
            log.info("WhatsApp uit; zou naar %s sturen: %s", to, text[:80])
            return
        try:
            httpx.post(
                f"{_GRAPH}/{self.phone_id}/messages",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"messaging_product": "whatsapp", "to": to,
                      "type": "text", "text": {"body": text[:4096]}},
                timeout=20)
        except Exception as exc:  # noqa: BLE001
            log.warning("WhatsApp send mislukt: %s", exc)

    def download_media(self, media_id: str) -> bytes | None:
        if not self.enabled:
            return None
        try:
            info = httpx.get(f"{_GRAPH}/{media_id}",
                             headers={"Authorization": f"Bearer {self.token}"}, timeout=20).json()
            url = info.get("url")
            if not url:
                return None
            return httpx.get(url, headers={"Authorization": f"Bearer {self.token}"},
                             timeout=30).content
        except Exception as exc:  # noqa: BLE001
            log.warning("WhatsApp media-download mislukt: %s", exc)
            return None

    @staticmethod
    def parse_incoming(payload: dict) -> list[dict]:
        """Haal berichten uit een Cloud API-webhook payload.

        Geeft een lijst van {from, text, image_id} terug (image_id kan None zijn).
        """
        out: list[dict] = []
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    item = {"from": msg.get("from", ""), "text": "", "image_id": None}
                    if msg.get("type") == "text":
                        item["text"] = msg.get("text", {}).get("body", "")
                    elif msg.get("type") == "image":
                        item["image_id"] = msg.get("image", {}).get("id")
                        item["text"] = msg.get("image", {}).get("caption", "") or "bonnetje"
                    else:
                        item["text"] = "(niet-ondersteund berichttype)"
                    out.append(item)
        return out
