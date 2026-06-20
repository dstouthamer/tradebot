"""AuthService — registratie, inloggen en token-afhandeling.

Bedrijfsregistratie maakt in één keer een tenant (bedrijf) + een owner-gebruiker. Alle
verdere administratiedata hangt aan ``tenant_id``. OAuth-gebruikers (Google/Microsoft)
worden op e-mailadres gekoppeld of aangemaakt met een eigen tenant.
"""
from __future__ import annotations

from dataclasses import dataclass

from boekhouder.auth import tokens
from boekhouder.auth.passwords import hash_password, verify_password
from boekhouder.config import get_settings
from boekhouder.store import Store, get_store


class AuthError(Exception):
    """Nette, gebruikersgerichte authenticatiefout."""


@dataclass(slots=True)
class Session:
    user_id: str
    tenant_id: str
    email: str
    token: str


class AuthService:
    def __init__(self, store: Store | None = None) -> None:
        self.store = store or get_store()
        self.settings = get_settings()

    # ---- registratie & login (e-mail/wachtwoord) -------------------------
    def register(self, email: str, password: str, company_name: str) -> Session:
        if not self.settings.allow_signup:
            raise AuthError("Registratie staat uit.")
        email = email.strip().lower()
        if "@" not in email:
            raise AuthError("Ongeldig e-mailadres.")
        if self.store.get_user_by_email(email):
            raise AuthError("Er bestaat al een account met dit e-mailadres.")
        try:
            pw_hash = hash_password(password)
        except ValueError as exc:
            raise AuthError(str(exc)) from exc
        tenant_id = self.store.create_tenant(self._default_profile(company_name))
        user_id = self.store.create_user(email, pw_hash, tenant_id)
        return self._session(user_id, tenant_id, email)

    def login(self, email: str, password: str) -> Session:
        user = self.store.get_user_by_email(email.strip().lower())
        if not user or not user.get("password_hash"):
            raise AuthError("Onjuiste inloggegevens.")
        if not verify_password(password, user["password_hash"]):
            raise AuthError("Onjuiste inloggegevens.")
        return self._session(user["id"], user["tenant_id"], user["email"])

    # ---- OAuth / iDIN koppeling (na succesvolle externe verificatie) -----
    def login_or_create_external(self, email: str, *, provider: str,
                                 company_name: str | None = None) -> Session:
        """Koppel een geverifieerd extern e-mailadres aan een account (maak indien nodig)."""
        email = email.strip().lower()
        user = self.store.get_user_by_email(email)
        if user:
            return self._session(user["id"], user["tenant_id"], email)
        tenant_id = self.store.create_tenant(
            self._default_profile(company_name or email.split("@")[0]))
        user_id = self.store.create_user(email, "", tenant_id, provider=provider)
        return self._session(user_id, tenant_id, email)

    # ---- token -----------------------------------------------------------
    def resolve(self, token: str) -> Session | None:
        payload = tokens.verify(token)
        if not payload:
            return None
        user = self.store.get_user(payload["uid"])
        if not user:
            return None
        return Session(user["id"], user["tenant_id"], user["email"], token)

    # ---- intern ----------------------------------------------------------
    def _session(self, user_id: str, tenant_id: str, email: str) -> Session:
        return Session(user_id, tenant_id, email, tokens.issue(user_id, tenant_id))

    def _default_profile(self, company_name: str) -> dict:
        s = self.settings
        return {
            "name": company_name, "legal_form": "EENMANSZAAK", "kvk": "", "btw_id": "",
            "iban": "", "sector": s.sector, "vat_period": "KWARTAAL",
            "payment_term_days": s.payment_term_days,
            "quote_validity_days": s.quote_validity_days, "accountant_contact": "",
        }
