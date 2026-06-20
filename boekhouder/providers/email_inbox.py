"""Factuur-mailbox via IMAP.

Geef een apart e-mailadres op waar alleen facturen binnenkomen; deze provider haalt de
ongelezen berichten op, pakt de bijlagen (pdf/afbeelding) eruit en geeft ze door aan de
OCR/Boekhoud-flow. Inert zonder IMAP-configuratie. ``parse_message`` is statisch en
zonder netwerk testbaar.
"""
from __future__ import annotations

import email
import imaplib
import logging
from email.message import Message

from boekhouder.config import get_settings

log = logging.getLogger("boekhouder.email")

_ATTACH_EXT = (".pdf", ".png", ".jpg", ".jpeg", ".gif", ".tiff", ".webp")


class EmailInbox:
    name = "imap"

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return self.settings.has_email

    @staticmethod
    def parse_message(raw: bytes) -> dict:
        """Haal onderwerp + bijlagen (filename, bytes) uit een rauwe e-mail."""
        msg: Message = email.message_from_bytes(raw)
        subject = str(email.header.make_header(email.header.decode_header(msg.get("Subject", ""))))
        attachments: list[tuple[str, bytes]] = []
        for part in msg.walk():
            if part.get_content_maintype() == "multipart":
                continue
            filename = part.get_filename()
            disp = (part.get("Content-Disposition") or "").lower()
            is_attach = filename and ("attachment" in disp or filename.lower().endswith(_ATTACH_EXT))
            if is_attach:
                payload = part.get_payload(decode=True)
                if payload:
                    attachments.append((filename, payload))
        return {"subject": subject, "attachments": attachments}

    def fetch_unseen(self, *, mark_seen: bool = True, limit: int = 50) -> list[dict]:
        """Haal ongelezen berichten met bijlagen op (en markeer ze als gelezen)."""
        if not self.enabled:
            return []
        s = self.settings
        out: list[dict] = []
        try:
            cls = imaplib.IMAP4_SSL if s.imap_ssl else imaplib.IMAP4
            with cls(s.imap_host) as imap:
                imap.login(s.imap_user, s.imap_password)
                imap.select(s.imap_folder)
                _, data = imap.search(None, "UNSEEN")
                ids = data[0].split()[:limit]
                for mid in ids:
                    _, msg_data = imap.fetch(mid, "(RFC822)")
                    raw = msg_data[0][1]
                    parsed = self.parse_message(raw)
                    if parsed["attachments"]:
                        out.append(parsed)
                    if mark_seen:
                        imap.store(mid, "+FLAGS", "\\Seen")
        except Exception as exc:  # noqa: BLE001 - never crash the poller
            log.warning("IMAP ophalen mislukt: %s", exc)
        return out
