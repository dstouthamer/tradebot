"""Stateless, ondertekende sessietokens (HMAC-SHA256, standaardbibliotheek).

Een token codeert ``user_id``, ``tenant_id`` en een vervaltijd, ondertekend met een
servergeheim. Geen serverstate nodig; manipulatie of verloop maakt het token ongeldig.
Formaat: ``base64url(payload).base64url(signature)``.
"""
from __future__ import annotations

import base64
import hmac
import json
import time
from hashlib import sha256

from boekhouder.config import get_settings

DEFAULT_TTL = 60 * 60 * 24 * 14         # 14 dagen


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + pad)


def _secret() -> bytes:
    s = get_settings()
    # SECRET_KEY hoort in productie gezet te zijn; lokaal valt het terug op db_path
    # zodat de app zonder config draait (maar dan niet voor productie geschikt is).
    return (getattr(s, "secret_key", "") or f"dev-{s.db_path}").encode()


def issue(user_id: str, tenant_id: str, *, ttl: int = DEFAULT_TTL) -> str:
    payload = {"uid": user_id, "tid": tenant_id, "exp": int(time.time()) + ttl}
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    sig = _b64e(hmac.new(_secret(), body.encode(), sha256).digest())
    return f"{body}.{sig}"


def verify(token: str) -> dict | None:
    try:
        body, sig = token.split(".")
        expected = _b64e(hmac.new(_secret(), body.encode(), sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(_b64d(body))
    except (ValueError, AttributeError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < int(time.time()):
        return None
    return payload
