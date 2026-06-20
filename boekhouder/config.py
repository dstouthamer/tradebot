"""Central configuration & compliance switches for the AI Boekhouder.

All knobs live here so they can be audited in one place (pattern borrowed from Apex's
``apex/config.py``). Anything that touches real risk — sending invoices, posting
definitive bookings, filing returns — is intentionally conservative by default:
``require_confirmation`` is on and ``allow_auto_send`` is off.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BOEKHOUDER_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ---- Company profile (masterprompt section 1) ------------------------
    company_name: str = Field(default="Mijn Bedrijf")
    legal_form: str = Field(default="EENMANSZAAK")      # EENMANSZAAK / BV / VOF / ANDERS
    kvk: str = Field(default="")
    btw_id: str = Field(default="")
    iban: str = Field(default="")
    sector: str = Field(default="INSTALLATIE")
    vat_period: str = Field(default="KWARTAAL")         # MAAND / KWARTAAL / JAAR
    payment_term_days: int = Field(default=14)
    quote_validity_days: int = Field(default=30)
    accountant_contact: str = Field(default="")

    # ====================================================================
    #  COMPLIANCE & SAFETY  — change with extreme care
    # ====================================================================
    # Nothing is booked/sent/filed definitively without an explicit user OK.
    require_confirmation: bool = Field(default=True)
    # Master switch for any outbound send (e-mail/Moneybird/Telegram replies that
    # would push a document live). OFF = drafts/concepts only.
    allow_auto_send: bool = Field(default=False)

    # ---- Integrations (blank = keyless fallback) -------------------------
    telegram_token: str = Field(default="")
    moneybird_token: str = Field(default="")
    moneybird_admin_id: str = Field(default="")
    moneybird_base_url: str = Field(default="https://moneybird.com/api/v2")
    ocr_provider: str = Field(default="auto")           # auto | tesseract | stub
    anthropic_api_key: str = Field(default="")
    anthropic_model: str = Field(default="claude-opus-4-8")

    # ---- Persistence -----------------------------------------------------
    db_path: str = Field(default="boekhouder.db")

    # ---- Auth & multi-tenant --------------------------------------------
    # Zet in productie een lange, willekeurige waarde (tekent sessietokens).
    secret_key: str = Field(default="")
    allow_signup: bool = Field(default=True)         # open registratie aan/uit
    # OAuth (gratis): vul client id/secret om Google/Microsoft-login te activeren.
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    microsoft_client_id: str = Field(default="")
    microsoft_client_secret: str = Field(default="")
    oauth_redirect_base: str = Field(default="http://localhost:8000")
    # iDIN (banklogin, betaald): vul de gegevens van je iDIN-broker om te activeren.
    idin_broker: str = Field(default="")            # bv. signicat | cm | bank
    idin_client_id: str = Field(default="")
    idin_client_secret: str = Field(default="")

    log_level: str = Field(default="INFO")

    # ---- Convenience -----------------------------------------------------
    @property
    def has_telegram(self) -> bool:
        return bool(self.telegram_token)

    @property
    def has_moneybird(self) -> bool:
        return bool(self.moneybird_token and self.moneybird_admin_id)

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_google_oauth(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def has_microsoft_oauth(self) -> bool:
        return bool(self.microsoft_client_id and self.microsoft_client_secret)

    @property
    def has_idin(self) -> bool:
        return bool(self.idin_broker and self.idin_client_id and self.idin_client_secret)


@lru_cache
def get_settings() -> Settings:
    return Settings()
