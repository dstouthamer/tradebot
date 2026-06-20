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
    def from_dict(cls, data: dict) -> "CompanyProfile":
        """Bouw een profiel uit een tenant-record (multi-tenant)."""
        return cls(
            name=data.get("name", "Mijn Bedrijf"),
            legal_form=data.get("legal_form", "EENMANSZAAK"),
            kvk=data.get("kvk", ""),
            btw_id=data.get("btw_id", ""),
            iban=data.get("iban", ""),
            sector=data.get("sector", "INSTALLATIE"),
            vat_period=data.get("vat_period", "KWARTAAL"),
            payment_term_days=int(data.get("payment_term_days", 14)),
            quote_validity_days=int(data.get("quote_validity_days", 30)),
            accountant_contact=data.get("accountant_contact", ""),
        )

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
