"""Login-methoden (provider-seam).

E-mail+wachtwoord werkt altijd en gratis. Google/Microsoft (OAuth) en iDIN (banklogin)
zijn kant-en-klare stekkers: ze verschijnen automatisch zodra de bijbehorende sleutels
in de config staan. iDIN vereist een betaald broker-contract — zonder contract blijft
de knop verborgen.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode

from boekhouder.config import get_settings


@dataclass(slots=True)
class LoginMethod:
    id: str
    label: str
    available: bool
    note: str = ""


def available_methods() -> list[LoginMethod]:
    s = get_settings()
    return [
        LoginMethod("password", "E-mail + wachtwoord", True),
        LoginMethod("google", "Inloggen met Google", s.has_google_oauth,
                    "" if s.has_google_oauth else "Zet GOOGLE_CLIENT_ID/SECRET om te activeren."),
        LoginMethod("microsoft", "Inloggen met Microsoft", s.has_microsoft_oauth,
                    "" if s.has_microsoft_oauth else "Zet MICROSOFT_CLIENT_ID/SECRET om te activeren."),
        LoginMethod("idin", "Inloggen met je bank (iDIN)", s.has_idin,
                    "" if s.has_idin else "Vereist een betaald iDIN-broker-contract (Signicat/CM.com/bank)."),
    ]


def google_authorize_url(state: str) -> str | None:
    s = get_settings()
    if not s.has_google_oauth:
        return None
    params = {
        "client_id": s.google_client_id,
        "redirect_uri": f"{s.oauth_redirect_base}/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "online",
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)


def microsoft_authorize_url(state: str) -> str | None:
    s = get_settings()
    if not s.has_microsoft_oauth:
        return None
    params = {
        "client_id": s.microsoft_client_id,
        "redirect_uri": f"{s.oauth_redirect_base}/auth/microsoft/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
    }
    return "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?" + urlencode(params)
