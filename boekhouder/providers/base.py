"""Provider interfaces. Concrete providers override the methods they support.

Mirrors ``apex/data/base.py``: each method raises ``NotImplementedError`` by default,
so a partial provider is fine.
"""
from __future__ import annotations

from boekhouder.domain.documents import BankTransaction, ExtractedDocument, SalesInvoice


class OcrProvider:
    """Extract structured fields from a receipt/invoice image, PDF or raw text."""

    name: str = "base"

    def extract(self, *, text: str | None = None, image_bytes: bytes | None = None,
                source_ref: str | None = None) -> ExtractedDocument:
        raise NotImplementedError(f"{self.name} cannot extract documents")


class BankImporter:
    """Parse a bank export file into transactions (offline, no keys)."""

    name: str = "base"

    def parse(self, content: str | bytes, *, fmt: str = "auto") -> list[BankTransaction]:
        raise NotImplementedError(f"{self.name} cannot parse bank files")


class BookkeepingProvider:
    """Read/write to a bookkeeping package (Moneybird, …). Concept-only by default."""

    name: str = "base"

    def list_bank_transactions(self) -> list[BankTransaction]:
        raise NotImplementedError(f"{self.name} cannot list bank transactions")

    def create_concept_sales_invoice(self, invoice: SalesInvoice) -> dict:
        raise NotImplementedError(f"{self.name} cannot create invoices")


class ChatChannel:
    """An inbound/outbound chat channel (Telegram, …)."""

    name: str = "base"

    def send(self, chat_id: str, text: str) -> None:
        raise NotImplementedError(f"{self.name} cannot send messages")
