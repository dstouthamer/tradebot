"""Document dataclasses: receipts, invoices, quotes, bank transactions, bookings.

These are plain data holders. Business logic (btw computation, risk scoring, matching)
lives in the agents/engine so the documents stay easy to serialise and test.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from boekhouder.domain.enums import BtwTarief, DocumentType, EvidenceQuality, RiskZone
from boekhouder.domain.money import BtwSplit, Money, btw_from_excl


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# --------------------------------------------------------------------------- #
#  Incoming documents (receipts / purchase invoices)
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class ExtractedDocument:
    """Result of the OCR agent — what we read off a bon/inkoopfactuur."""

    doc_type: DocumentType = DocumentType.ONBEKEND
    supplier: str | None = None
    supplier_kvk: str | None = None
    supplier_btw_id: str | None = None
    invoice_number: str | None = None
    doc_date: date | None = None
    total_incl: Money | None = None
    btw_amount: Money | None = None
    total_excl: Money | None = None
    btw_tarief: BtwTarief | None = None
    payment_method: str | None = None
    iban: str | None = None
    description: str | None = None
    category: str | None = None
    project: str | None = None
    evidence_quality: EvidenceQuality = EvidenceQuality.LAAG
    raw_text: str = ""
    source_ref: str | None = None       # filename / message id


# --------------------------------------------------------------------------- #
#  Bank
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class BankTransaction:
    date: date
    amount: Money                       # negative = outgoing (af), positive = incoming (bij)
    counterparty: str = ""
    counterparty_iban: str = ""
    description: str = ""
    reference: str = ""
    source: str = ""                    # camt053 | mt940 | csv | moneybird
    txn_id: str = ""


# --------------------------------------------------------------------------- #
#  Sales invoice & quote line items
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class LineItem:
    description: str
    quantity: float
    unit_price_excl: Money
    btw_tarief: BtwTarief = BtwTarief.HOOG

    @property
    def line_excl(self) -> Money:
        return self.unit_price_excl * self.quantity

    @property
    def split(self) -> BtwSplit:
        return btw_from_excl(self.line_excl, self.btw_tarief)


@dataclass(slots=True)
class SalesInvoice:
    customer_name: str
    lines: list[LineItem] = field(default_factory=list)
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    customer_address: str | None = None
    project_ref: str | None = None
    iban: str | None = None
    is_concept: bool = True             # never definitief until confirmed

    @property
    def total_excl(self) -> Money:
        out = Money(0)
        for line in self.lines:
            out += line.line_excl
        return out

    @property
    def total_btw(self) -> Money:
        out = Money(0)
        for line in self.lines:
            out += line.split.btw
        return out

    @property
    def total_incl(self) -> Money:
        return self.total_excl + self.total_btw


@dataclass(slots=True)
class Quote:
    customer_name: str
    lines: list[LineItem] = field(default_factory=list)
    quote_number: str | None = None
    quote_date: date | None = None
    valid_until: date | None = None
    project_description: str | None = None
    assumptions: list[str] = field(default_factory=list)     # aannames / stelposten
    exclusions: list[str] = field(default_factory=list)
    is_concept: bool = True

    @property
    def total_excl(self) -> Money:
        out = Money(0)
        for line in self.lines:
            out += line.line_excl
        return out

    @property
    def total_btw(self) -> Money:
        out = Money(0)
        for line in self.lines:
            out += line.split.btw
        return out

    @property
    def total_incl(self) -> Money:
        return self.total_excl + self.total_btw


# --------------------------------------------------------------------------- #
#  Bookkeeping entry (concept)
# --------------------------------------------------------------------------- #
@dataclass(slots=True)
class Boeking:
    """A concept journal entry (masterprompt agent D)."""

    supplier: str
    doc_date: date | None
    total_incl: Money
    btw: Money
    total_excl: Money
    btw_tarief: BtwTarief
    category: str
    project: str | None = None
    payment_status: str = "onbekend"
    bank_match_id: str | None = None
    match_confidence: int = 0
    risk_zone: RiskZone = RiskZone.ORANJE
    note: str | None = None
    attachment_ref: str | None = None
    is_definitief: bool = False         # only after explicit confirmation
    created_at: str = field(default_factory=_now)
