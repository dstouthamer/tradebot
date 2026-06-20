"""Bedrijfsprofiel — the company facts an agent may need (masterprompt section 1)."""
from __future__ import annotations

from dataclasses import dataclass

from boekhouder.config import Settings, get_settings


@dataclass(slots=True)
class CompanyProfile:
    name: str
    legal_form: str
    kvk: str
    btw_id: str
    iban: str
    sector: str
    vat_period: str
    payment_term_days: int
    quote_validity_days: int
    accountant_contact: str

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "CompanyProfile":
        s = settings or get_settings()
        return cls(
            name=s.company_name,
            legal_form=s.legal_form,
            kvk=s.kvk,
            btw_id=s.btw_id,
            iban=s.iban,
            sector=s.sector,
            vat_period=s.vat_period,
            payment_term_days=s.payment_term_days,
            quote_validity_days=s.quote_validity_days,
            accountant_contact=s.accountant_contact,
        )
