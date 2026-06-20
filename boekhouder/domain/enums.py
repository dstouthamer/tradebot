"""Shared enumerations — the vocabulary every agent speaks.

The ``RiskZone`` traffic-light is the accounting analog of Apex's BUY/SELL ``Action``:
it is the single directional verdict each agent returns for a cost/booking/advice.
"""
from __future__ import annotations

from enum import Enum


class RiskZone(str, Enum):
    """Fiscaal/boekhoudkundig risico (masterprompt sections 5 & D)."""

    GROEN = "GROEN"      # direct verdedigbaar
    ORANJE = "ORANJE"    # scherp maar mogelijk verdedigbaar; extra bewijs/boekhouder
    ROOD = "ROOD"        # niet doen / niet zo boeken

    @property
    def label(self) -> str:
        return {
            RiskZone.GROEN: "groen — direct verdedigbaar",
            RiskZone.ORANJE: "oranje — mogelijk verdedigbaar, extra bewijs nodig",
            RiskZone.ROOD: "rood — niet boeken als zakelijke kosten",
        }[self]


class BtwTarief(str, Enum):
    """Nederlandse btw-tarieven (masterprompt section 1)."""

    HOOG = "21"
    LAAG = "9"
    NUL = "0"
    VERLEGD = "verlegd"
    VRIJGESTELD = "vrijgesteld"

    @property
    def rate(self) -> float:
        """Numeric rate as a fraction; verlegd/vrijgesteld carry no own btw (0.0)."""
        return {"21": 0.21, "9": 0.09, "0": 0.0, "verlegd": 0.0, "vrijgesteld": 0.0}[self.value]

    @classmethod
    def from_input(cls, value: str | float | int | None) -> "BtwTarief":
        if value is None:
            return cls.HOOG
        s = str(value).strip().lower().replace("%", "")
        mapping = {
            "21": cls.HOOG, "0.21": cls.HOOG, "21.0": cls.HOOG,
            "9": cls.LAAG, "0.09": cls.LAAG, "6": cls.LAAG,
            "0": cls.NUL, "0.0": cls.NUL,
            "verlegd": cls.VERLEGD, "btw verlegd": cls.VERLEGD,
            "vrijgesteld": cls.VRIJGESTELD, "vrij": cls.VRIJGESTELD,
        }
        return mapping.get(s, cls.HOOG)


class DocumentType(str, Enum):
    """Documenttype (masterprompt OCR agent B)."""

    BON = "bon"
    INKOOPFACTUUR = "inkoopfactuur"
    VERKOOPFACTUUR = "verkoopfactuur"
    BETAALBEWIJS = "betaalbewijs"
    OFFERTE = "offerte"
    CONTRACT = "contract"
    ONBEKEND = "onbekend"


class EvidenceQuality(str, Enum):
    """Bewijskwaliteit van een document (masterprompt OCR agent B)."""

    HOOG = "hoog"
    MIDDEL = "middel"
    LAAG = "laag"


class IntentType(str, Enum):
    """What the user wants — decided by the Intake agent (masterprompt agent A)."""

    UPLOAD_BON = "upload_bon"
    MAAK_FACTUUR = "maak_factuur"
    MAAK_OFFERTE = "maak_offerte"
    FISCAAL_ADVIES = "fiscaal_advies"
    CFO_ADVIES = "cfo_advies"
    BANK_IMPORT = "bank_import"
    BEVESTIG = "bevestig"          # user confirms a pending concept
    ONBEKEND = "onbekend"
