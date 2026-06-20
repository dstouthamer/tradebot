"""OCR & Bonnetjes agent (masterprompt agent B).

Wraps the configured OCR provider, then judges evidence quality and a first fiscal
risk. On a poor scan it asks for a better photo instead of booking blind.
"""
from __future__ import annotations

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.documents import ExtractedDocument
from boekhouder.domain.enums import EvidenceQuality, RiskZone
from boekhouder.providers.registry import get_ocr


class OcrAgent(BaseAgent):
    name = "ocr"

    def __init__(self) -> None:
        super().__init__()
        self.provider = get_ocr()

    def extract(self, *, text: str | None = None, image_bytes: bytes | None = None,
                source_ref: str | None = None, supplier_hint: str | None = None,
                project: str | None = None) -> ExtractedDocument:
        doc = self.provider.extract(text=text, image_bytes=image_bytes, source_ref=source_ref)
        if supplier_hint and not doc.supplier:
            doc.supplier = supplier_hint
        if project:
            doc.project = project
        return doc

    def run(self, *, text=None, image_bytes=None, source_ref=None,
            supplier_hint=None, project=None) -> AgentResult:
        doc = self.extract(text=text, image_bytes=image_bytes, source_ref=source_ref,
                           supplier_hint=supplier_hint, project=project)
        missing: list[str] = []
        if doc.total_incl is None:
            missing.append("totaalbedrag")
        if doc.supplier is None:
            missing.append("leverancier")
        if doc.doc_date is None:
            missing.append("datum")

        if doc.evidence_quality == EvidenceQuality.LAAG or len(missing) >= 2:
            return self.result(
                RiskZone.ROOD, 0.3,
                summary="Bon onvoldoende leesbaar — stuur a.u.b. een duidelijkere foto.",
                reasons=["Lage bewijskwaliteit of te veel ontbrekende velden."],
                bewijs_nodig=missing or ["scherpe foto van de volledige bon"],
                actie_nodig="controleren",
                payload=doc,
            )
        zone = RiskZone.GROEN if doc.evidence_quality == EvidenceQuality.HOOG else RiskZone.ORANJE
        conf = 0.9 if zone == RiskZone.GROEN else 0.7
        amount = doc.total_incl
        return self.result(
            zone, conf,
            summary=(f"Bon herkend: {doc.supplier or 'onbekend'}"
                     + (f", {amount}" if amount else "")
                     + (f", datum {doc.doc_date.strftime('%d-%m-%Y')}" if doc.doc_date else "")),
            reasons=[f"Bewijskwaliteit: {doc.evidence_quality.value}"],
            bewijs_nodig=missing,
            payload=doc,
        )
