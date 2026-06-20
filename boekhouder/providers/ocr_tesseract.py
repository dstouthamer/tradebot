"""OCR providers.

``TesseractOcr`` runs real OCR on an image when pytesseract + the tesseract binary are
available; otherwise we degrade to ``StubOcr`` which parses raw text (or a textual hint
typed in chat) with deterministic regexes. Both return the same ``ExtractedDocument``,
so the rest of the system is OCR-engine agnostic and unit-testable offline.
"""
from __future__ import annotations

import logging
import re
from datetime import date, datetime

from boekhouder.domain.documents import ExtractedDocument
from boekhouder.domain.enums import BtwTarief, DocumentType, EvidenceQuality
from boekhouder.domain.money import Money
from boekhouder.providers.base import OcrProvider

log = logging.getLogger("boekhouder.ocr")

_AMOUNT_RE = re.compile(r"(?:€\s*)?(\d{1,3}(?:[.\s]\d{3})*|\d+)[.,](\d{2})")
_DATE_RES = [
    (re.compile(r"\b(\d{2})[-/](\d{2})[-/](\d{4})\b"), "%d-%m-%Y"),
    (re.compile(r"\b(\d{4})[-/](\d{2})[-/](\d{2})\b"), "%Y-%m-%d"),
]
_BTW_RE = re.compile(r"\bbtw\b.*?(\d{1,2})\s*%", re.IGNORECASE)
_IBAN_RE = re.compile(r"\b([A-Z]{2}\d{2}[A-Z0-9]{10,30})\b")
_KVK_RE = re.compile(r"\bkvk[:\s]*([0-9]{8})\b", re.IGNORECASE)
_VAT_ID_RE = re.compile(r"\b(NL\d{9}B\d{2})\b", re.IGNORECASE)

# A few well-known NL suppliers help category suggestions even from a one-word hint.
_KNOWN_SUPPLIERS = {
    "gamma": "materialen/installatie",
    "hornbach": "materialen/installatie",
    "praxis": "materialen/installatie",
    "bol": "kantoor/diversen",
    "shell": "brandstof/auto",
    "bp": "brandstof/auto",
    "albert heijn": "representatie/diversen",
    "mediamarkt": "inventaris/elektronica",
    "coolblue": "inventaris/elektronica",
}


def _parse_amount(token_whole: str, token_frac: str) -> Money:
    whole = token_whole.replace(".", "").replace(" ", "")
    return Money.euro(f"{whole}.{token_frac}")


def _largest_amount(text: str) -> Money | None:
    amounts = [_parse_amount(w, f) for w, f in _AMOUNT_RE.findall(text)]
    return max(amounts, key=lambda m: m.cents) if amounts else None


def _find_date(text: str) -> date | None:
    for rx, fmt in _DATE_RES:
        m = rx.search(text)
        if m:
            try:
                return datetime.strptime(m.group(0), fmt).date()
            except ValueError:
                continue
    return None


def _find_supplier(text: str) -> tuple[str | None, str | None]:
    low = text.lower()
    for name, cat in _KNOWN_SUPPLIERS.items():
        if name in low:
            return name.title(), cat
    # else first non-empty line is a decent guess for a receipt header
    for line in text.splitlines():
        line = line.strip()
        if line and not _AMOUNT_RE.fullmatch(line):
            return line[:60], None
    return None, None


def parse_text(text: str, source_ref: str | None = None) -> ExtractedDocument:
    """Deterministic regex extraction — shared by both providers."""
    supplier, category = _find_supplier(text)
    total = _largest_amount(text)
    btw_m = _BTW_RE.search(text)
    tarief = BtwTarief.from_input(btw_m.group(1)) if btw_m else None
    iban_m = _IBAN_RE.search(text)
    kvk_m = _KVK_RE.search(text)
    vat_m = _VAT_ID_RE.search(text)

    # Evidence quality: more recognised fields -> higher confidence.
    fields_found = sum(x is not None for x in (supplier, total, tarief, iban_m))
    quality = (
        EvidenceQuality.HOOG if fields_found >= 3
        else EvidenceQuality.MIDDEL if fields_found == 2
        else EvidenceQuality.LAAG
    )

    doc = ExtractedDocument(
        doc_type=DocumentType.BON,
        supplier=supplier,
        supplier_kvk=kvk_m.group(1) if kvk_m else None,
        supplier_btw_id=vat_m.group(1).upper() if vat_m else None,
        doc_date=_find_date(text),
        total_incl=total,
        btw_tarief=tarief,
        iban=iban_m.group(1) if iban_m else None,
        category=category,
        evidence_quality=quality,
        raw_text=text,
        source_ref=source_ref,
    )
    if total is not None and tarief is not None:
        from boekhouder.domain.money import btw_from_incl

        split = btw_from_incl(total, tarief)
        doc.total_excl, doc.btw_amount = split.excl, split.btw
    return doc


class StubOcr(OcrProvider):
    name = "stub"

    def extract(self, *, text=None, image_bytes=None, source_ref=None) -> ExtractedDocument:
        if not text and image_bytes:
            # No real OCR available: record low evidence, ask for a better photo.
            doc = ExtractedDocument(source_ref=source_ref, evidence_quality=EvidenceQuality.LAAG)
            doc.description = "Afbeelding ontvangen maar geen OCR-engine actief."
            return doc
        return parse_text(text or "", source_ref)


class TesseractOcr(OcrProvider):
    name = "tesseract"

    def extract(self, *, text=None, image_bytes=None, source_ref=None) -> ExtractedDocument:
        if image_bytes:
            try:
                import io

                import pytesseract  # optional dependency
                from PIL import Image

                text = pytesseract.image_to_string(Image.open(io.BytesIO(image_bytes)), lang="nld+eng")
            except Exception as exc:  # noqa: BLE001 - degrade to stub behaviour
                log.warning("Tesseract OCR failed (%s); using provided text only", exc)
        return parse_text(text or "", source_ref)
