"""Entrypoint: haal facturen uit de factuur-mailbox en zet ze als conceptboeking klaar.

Draai periodiek via cron, bijvoorbeeld elk kwartier (op de server):

    */15 * * * *  cd /root/tradebot && docker compose exec -T app python -m boekhouder.mail_fetch

Elke bijlage (pdf/afbeelding) gaat door de OCR/Boekhoud-flow (concept; niets wordt
definitief geboekt zonder bevestiging). Werkt op de standaard 'local' tenant.
"""
from __future__ import annotations

import logging

from boekhouder.config import get_settings
from boekhouder.engine.router import Router
from boekhouder.providers.email_inbox import EmailInbox
from boekhouder.store import LOCAL_TENANT


def run() -> dict:
    logging.basicConfig(level=get_settings().log_level)
    inbox = EmailInbox()
    if not inbox.enabled:
        print("IMAP niet geconfigureerd (BOEKHOUDER_IMAP_* ontbreekt).")
        return {"verwerkt": 0}
    router = Router()
    verwerkt = 0
    for msg in inbox.fetch_unseen():
        for filename, content in msg["attachments"]:
            hint = f"bonnetje {msg['subject'][:60]}"
            router.handle(hint, session_id="mail", tenant_id=LOCAL_TENANT, image_bytes=content)
            verwerkt += 1
    print(f"{verwerkt} factuurbijlage(n) verwerkt en als concept klaargezet.")
    return {"verwerkt": verwerkt}


if __name__ == "__main__":
    run()
