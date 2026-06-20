"""Intake agent (masterprompt agent A).

Turns a short WhatsApp/Telegram message into a structured ``Intent``: what the user
wants, the entities we could extract, and which minimal fields are still missing. The
logic is deterministic regex/keyword parsing (testable offline); an LLM may refine it
later via the ``providers.llm`` seam, but it never invents numbers.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from boekhouder.agents.base import AgentResult, BaseAgent
from boekhouder.domain.enums import BtwTarief, IntentType, RiskZone
from boekhouder.domain.money import Money

# Amount like "1850", "1.850,00", "€3200", "6500 incl btw".
_AMOUNT_RE = re.compile(r"(?:€\s*)?(\d{1,3}(?:\.\d{3})+|\d+)(?:,(\d{2}))?")
_QTY_RE = re.compile(r"\b(\d+)\s*(?:x|stuks?|airco'?s?|warmtepompen?)\b", re.IGNORECASE)

_CONFIRM_WORDS = {"ja", "bevestig", "akkoord", "definitief", "verstuur", "verstu. ", "ok", "oké", "prima"}
_FACTUUR_WORDS = ("factuur", "factureer", "reken af")
_OFFERTE_WORDS = ("offerte", "offreer", "prijsopgave")
_BON_WORDS = ("bonnetje", "bon ", "kassabon", "inkoopfactuur", "kwitantie", "receipt")
_BANK_WORDS = ("bankafschrift", "bank import", "importeer bank", "camt", "mt940", "afschrift")
_FISCAAL_WORDS = ("btw", "aftrek", "aftrekbaar", "fiscaal", "belasting", "investeren",
                  "afschrijv", "kosten mis", "gereedschap kopen", "kopen")
_OPTIMALISATIE_WORDS = ("bespaar belasting", "belasting besparen", "minder belasting",
                        "optimaliseer", "optimalisatie", "aftrekposten", "fiscaal voordeel",
                        "trucs", "trucjes", "wat kan ik aftrekken", "belasting drukken",
                        "minder betalen", "eia", "mia", "vamil")
# Investeringen met een bedrag -> concrete voordeel-berekening.
_INVEST_WORDS = ("investeer", "investering", "investeren", "zonnepanel", "warmtepomp",
                 "laadpaal", "aanschaf", "aanschaffen", "bedrijfsmiddel", "machine")
_BTW_BUITENLAND_WORDS = ("btw buitenland", "btw in het buitenland", "btw andere land",
                         "btw in andere land", "intracommunautair", "leveren aan duitsland",
                         "verkopen in het buitenland", "oss-regeling", "oss regeling",
                         "export btw", "btw buiten nederland", "btw europa", "minder btw")
_CFO_WORDS = ("cashflow", "marge", "winst", "omzet", "debiteuren", "liquiditeit",
              "hoeveel btw moet ik betalen", "reservering", "prognose", "prognoses",
              "voorspel", "verwacht", "komende", "vooruit", "forecast",
              "hoe staat mijn bedrijf", "hoe staat het bedrijf")


@dataclass(slots=True)
class Intent:
    type: IntentType
    raw: str
    customer: str | None = None
    supplier: str | None = None
    project: str | None = None
    location: str | None = None
    description: str | None = None
    amount: Money | None = None
    amount_basis: str = "excl"            # "excl" | "incl"
    btw_tarief: BtwTarief = BtwTarief.HOOG
    quantity: float = 1.0
    missing: list[str] = field(default_factory=list)


def _parse_amount(text: str) -> tuple[Money | None, str]:
    m = _AMOUNT_RE.search(text.replace(" ", " "))
    if not m:
        return None, "excl"
    whole = m.group(1).replace(".", "")
    frac = m.group(2) or "00"
    amount = Money.euro(f"{whole}.{frac}")
    low = text.lower()
    basis = "incl" if ("incl" in low or "inclusief" in low) else "excl"
    return amount, basis


def _after_keyword(text: str, keywords: tuple[str, ...]) -> str | None:
    low = text.lower()
    for kw in keywords:
        idx = low.find(kw)
        if idx >= 0:
            rest = text[idx + len(kw):].strip(" :,-")
            return rest or None
    return None


# Command verbs that look like names but never are.
_COMMAND_WORDS = {"maak", "factuur", "factureer", "offerte", "offreer", "bonnetje",
                  "reken", "prijsopgave", "stuur", "voor"}


def _capitalised_name(text: str) -> str | None:
    """Best-effort proper-name pick: e.g. 'voor De Vries airco' -> 'De Vries'.

    Prefers an explicit 'voor <Naam>'; otherwise the first capitalised token that is
    not a command verb. Returns None when no plausible name is present.
    """
    m = re.search(r"\bvoor\s+([A-Z][\wÀ-ÿ]+(?:\s+[A-Z][\wÀ-ÿ]+)?)", text)
    if m:
        return m.group(1).strip()
    for m in re.finditer(r"\b([A-Z][\wÀ-ÿ]+(?:\s+[A-Z][\wÀ-ÿ]+)?)", text):
        if m.group(1).split()[0].lower() not in _COMMAND_WORDS:
            return m.group(1).strip()
    return None


class IntakeAgent(BaseAgent):
    name = "intake"

    def classify(self, message: str) -> Intent:
        low = message.lower().strip()
        amount, basis = _parse_amount(message)
        tarief = BtwTarief.from_input(self._btw_hint(low))
        project = _after_keyword(message, ("project",))
        if project:
            project = project.split()[0]

        if low in _CONFIRM_WORDS or low.startswith(("ja ", "maak definitief", "verstuur")):
            return Intent(IntentType.BEVESTIG, message)
        if any(w in low for w in _BON_WORDS):
            supplier = self._supplier_hint(message)
            return Intent(IntentType.UPLOAD_BON, message, supplier=supplier, project=project,
                          amount=amount, amount_basis=basis, btw_tarief=tarief)
        if any(w in low for w in _BANK_WORDS):
            return Intent(IntentType.BANK_IMPORT, message)
        if any(w in low for w in _FACTUUR_WORDS):
            return self._sales(IntentType.MAAK_FACTUUR, message, amount, basis, tarief, project)
        if any(w in low for w in _OFFERTE_WORDS):
            return self._sales(IntentType.MAAK_OFFERTE, message, amount, basis, tarief, project)
        if any(w in low for w in _BTW_BUITENLAND_WORDS):
            return Intent(IntentType.BTW_BUITENLAND, message)
        if any(w in low for w in _OPTIMALISATIE_WORDS) or \
                (amount is not None and any(w in low for w in _INVEST_WORDS)):
            return Intent(IntentType.OPTIMALISATIE, message, amount=amount, amount_basis=basis)
        if any(w in low for w in _CFO_WORDS):
            return Intent(IntentType.CFO_ADVIES, message)
        if any(w in low for w in _FISCAAL_WORDS):
            return Intent(IntentType.FISCAAL_ADVIES, message)
        return Intent(IntentType.ONBEKEND, message)

    def _sales(self, itype, message, amount, basis, tarief, project) -> Intent:
        qty_m = _QTY_RE.search(message)
        qty = float(qty_m.group(1)) if qty_m else 1.0
        location = self._location(message)
        customer = _capitalised_name(message)
        if customer and location and customer == location:
            customer = None         # a place name is not a customer
        description = self._description(message, customer)
        intent = Intent(itype, message, customer=customer, project=project,
                        description=description, amount=amount, amount_basis=basis,
                        btw_tarief=tarief, quantity=qty, location=location)
        if itype == IntentType.MAAK_FACTUUR:
            intent.customer = customer
            if not customer:
                intent.missing.append("klantnaam")
            if amount is None:
                intent.missing.append("bedrag")
        return intent

    @staticmethod
    def _btw_hint(low: str) -> str | None:
        m = re.search(r"(\d{1,2})\s*%\s*btw|btw\s*(\d{1,2})\s*%", low)
        if m:
            return m.group(1) or m.group(2)
        if "verlegd" in low:
            return "verlegd"
        return None

    @staticmethod
    def _supplier_hint(message: str) -> str | None:
        rest = _after_keyword(message, ("bonnetje", "inkoopfactuur", "kassabon", "bon"))
        if not rest:
            return None
        return rest.split(" project")[0].strip().split()[0].title() if rest.split() else None

    @staticmethod
    def _description(message: str, customer: str | None) -> str | None:
        text = message
        for kw in _FACTUUR_WORDS + _OFFERTE_WORDS + ("maak", "factureer", "offreer"):
            text = re.sub(rf"\b{kw}\b", "", text, flags=re.IGNORECASE)
        if customer:
            text = text.replace(customer, "")
        text = re.sub(r"\bvoor\b", "", text, flags=re.IGNORECASE)
        text = _AMOUNT_RE.sub("", text)
        text = re.sub(r"\b(ex|excl|incl|inclusief|exclusief|btw|%)\b", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\bproject\s+\w+", "", text, flags=re.IGNORECASE)
        cleaned = " ".join(text.split()).strip(" :,-")
        return cleaned or None

    @staticmethod
    def _location(message: str) -> str | None:
        # crude: a trailing capitalised word that is a known-ish place pattern
        m = re.search(r"\b(Apeldoorn|Amsterdam|Utrecht|Rotterdam|Den Haag|[A-Z][a-zà-ÿ]+)\b\s*\d", message)
        return m.group(1) if m else None

    def run(self, message: str) -> AgentResult:
        intent = self.classify(message)
        conf = 0.9 if intent.type != IntentType.ONBEKEND else 0.2
        return self.result(
            RiskZone.GROEN, conf,
            summary=f"Intentie: {intent.type.value}",
            payload=intent,
            requires_confirmation=False,
        )
