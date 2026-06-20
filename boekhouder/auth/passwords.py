"""Wachtwoord-hashing met de standaardbibliotheek (PBKDF2-HMAC-SHA256).

Geen externe dependency nodig. Het opgeslagen formaat is
``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>`` en wordt in constante tijd
vergeleken om timing-aanvallen te beperken.
"""
from __future__ import annotations

import hashlib
import hmac
import os

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 240_000
_SALT_BYTES = 16


def hash_password(password: str, *, iterations: int = _ITERATIONS) -> str:
    if not password or len(password) < 8:
        raise ValueError("Wachtwoord moet minimaal 8 tekens zijn.")
    salt = os.urandom(_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"{_ALGO}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        expected = bytes.fromhex(hash_hex)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iters))
    except (ValueError, AttributeError):
        return False
    return hmac.compare_digest(digest, expected)
