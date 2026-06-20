"""Router — the orchestrator (analog of Apex's MasterDecisionAgent).

Pipeline: compliance pre-check → Intake classification → the right specialist agent →
approval gate (park concept) → formatter. Returns a ``Reply`` the surfaces (CLI, API,
Telegram) render as-is. Nothing is finalised here; confirmation flows through the gate.

Tenant-aware: every call carries a ``tenant_id`` so each company sees only its own
administratie. The CLI/dashboard use the default ``local`` tenant; the API derives the
tenant from the logged-in user.
"""
from __future__ import annotations

from dataclasses import dataclass

from boekhouder.agents.bank_matching import BankMatchingAgent
from boekhouder.agents.bookkeeping import BookkeepingAgent
from boekhouder.agents.cfo import CfoAgent
from boekhouder.agents.compliance import ComplianceAgent
from boekhouder.agents.fiscal import FiscalAgent
from boekhouder.agents.forecast import ForecastAgent
from boekhouder.agents.intake import IntakeAgent, Intent
from boekhouder.agents.invoice import InvoiceAgent
from boekhouder.agents.ocr import OcrAgent
from boekhouder.agents.optimization import OptimizationAgent
from boekhouder.agents.quote import QuoteAgent
from boekhouder.config import get_settings
from boekhouder.domain.company import CompanyProfile
from boekhouder.domain.enums import IntentType, RiskZone
from boekhouder.engine import formatters
from boekhouder.engine.audit import ApprovalGate, PendingAction
from boekhouder.providers.registry import get_bank_importer
from boekhouder.store import LOCAL_TENANT, get_store


@dataclass(slots=True)
class Reply:
    text: str
    agent: str
    risk_zone: RiskZone
    requires_confirmation: bool = False
    blocked: bool = False


class Router:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.store = get_store()
        self.gate = ApprovalGate(self.store)
        self._profiles: dict[str, CompanyProfile] = {}

        self.intake = IntakeAgent()
        self.compliance = ComplianceAgent()
        self.ocr = OcrAgent()
        self.matcher = BankMatchingAgent()
        self.bookkeeper = BookkeepingAgent()
        self.fiscal = FiscalAgent()
        self.optimization = OptimizationAgent()
        self.cfo = CfoAgent()
        self.forecast = ForecastAgent()
        self.bank_importer = get_bank_importer()

    # ------------------------------------------------------------------ #
    def profile(self, tenant_id: str) -> CompanyProfile:
        if tenant_id not in self._profiles:
            data = self.store.get_tenant(tenant_id)
            self._profiles[tenant_id] = (
                CompanyProfile.from_dict(data) if data
                else CompanyProfile.from_settings(self.settings))
        return self._profiles[tenant_id]

    def invalidate_profile(self, tenant_id: str) -> None:
        self._profiles.pop(tenant_id, None)

    def handle(self, message: str, *, session_id: str = "default",
               tenant_id: str = LOCAL_TENANT,
               image_bytes: bytes | None = None,
               file_content: str | bytes | None = None) -> Reply:
        # 1. Compliance pre-check — a hard stop overrides everything.
        comp = self.compliance.run(message)
        if comp.blocked:
            text = f"{comp.summary}\n\nWel mogelijk: {comp.advies}\n" \
                   f"Nodig: {', '.join(comp.bewijs_nodig)}"
            return Reply(text, "compliance", RiskZone.ROOD, blocked=True)

        intent = self.intake.classify(message)
        dispatch = {
            IntentType.BEVESTIG: self._confirm,
            IntentType.MAAK_FACTUUR: self._invoice,
            IntentType.MAAK_OFFERTE: self._quote,
            IntentType.UPLOAD_BON: self._bon,
            IntentType.BANK_IMPORT: self._bank,
            IntentType.FISCAAL_ADVIES: self._fiscal,
            IntentType.OPTIMALISATIE: self._optimize,
            IntentType.CFO_ADVIES: self._cfo,
        }
        handler = dispatch.get(intent.type, self._unknown)
        return handler(intent, session_id=session_id, tenant_id=tenant_id,
                       image_bytes=image_bytes, file_content=file_content)

    # ------------------------------------------------------------------ #
    def _confirm(self, intent: Intent, *, session_id: str, tenant_id: str, **_) -> Reply:
        outcome = self.gate.confirm(session_id, tenant_id=tenant_id)
        zone = RiskZone.GROEN if outcome["ok"] else RiskZone.ORANJE
        return Reply(outcome["message"], "audit", zone)

    def _invoice(self, intent: Intent, *, session_id: str, tenant_id: str, **_) -> Reply:
        profile = self.profile(tenant_id)
        res = InvoiceAgent(profile).run(intent)
        if res.payload is None:
            return Reply(f"{res.summary} Nog nodig: {', '.join(res.bewijs_nodig)}.",
                         "invoice", res.risk_zone, requires_confirmation=False)
        inv = res.payload
        from boekhouder.providers.registry import get_bookkeeping
        bk = get_bookkeeping()
        self.gate.propose(
            PendingAction(session_id, "factuur", res.summary, inv, tenant_id=tenant_id,
                          finalize=lambda inv=inv: bk.create_concept_sales_invoice(inv)),
            actor="gebruiker", confidence=res.confidence, proposed_action="maak_factuur")
        text = formatters.factuur(inv, profile.name, profile.iban) + f"\n\n{res.advies}"
        return Reply(text, "invoice", res.risk_zone, requires_confirmation=True)

    def _quote(self, intent: Intent, *, session_id: str, tenant_id: str, **_) -> Reply:
        profile = self.profile(tenant_id)
        res = QuoteAgent(profile).run(intent)
        if res.payload is None:
            return Reply(f"{res.summary} Nog nodig: {', '.join(res.bewijs_nodig)}.",
                         "quote", res.risk_zone)
        q = res.payload
        self.gate.propose(
            PendingAction(session_id, "offerte", res.summary, q, tenant_id=tenant_id),
            actor="gebruiker", confidence=res.confidence, proposed_action="maak_offerte")
        text = formatters.offerte(q, profile.name) + f"\n\n{res.advies}"
        return Reply(text, "quote", res.risk_zone, requires_confirmation=True)

    def _bon(self, intent: Intent, *, session_id: str, tenant_id: str,
             image_bytes=None, **_) -> Reply:
        text = None if image_bytes else intent.raw
        res = self.ocr.run(text=text, image_bytes=image_bytes,
                           supplier_hint=intent.supplier, project=intent.project)
        if res.risk_zone == RiskZone.ROOD:
            self.store.add_controlelijst("bon", res.summary, tenant_id=tenant_id)
            return Reply(f"{res.summary} Nodig: {', '.join(res.bewijs_nodig)}.",
                         "ocr", res.risk_zone)
        doc = res.payload
        match_res = self.matcher.run(doc, self.store.get_bank_txns(tenant_id))
        match = match_res.payload  # MatchCandidate | None
        book_res = self.bookkeeper.run(doc, match)
        boeking = book_res.payload
        bankmatch = (f"{match.transaction.amount} op {match.transaction.date:%d-%m-%Y}"
                     if match else "geen match")
        if book_res.risk_zone != RiskZone.GROEN:
            self.store.add_controlelijst("boeking", book_res.summary, tenant_id=tenant_id)
        self.gate.propose(
            PendingAction(session_id, "boeking", book_res.summary, boeking, tenant_id=tenant_id),
            actor="gebruiker", confidence=book_res.confidence, proposed_action="boeken")
        text_out = formatters.boekingsvoorstel(
            boeking, bankmatch=bankmatch, advies=book_res.advies,
            vraag="Wil je dit boeken?" if book_res.risk_zone == RiskZone.GROEN else
                  f"Aanvullen: {', '.join(book_res.bewijs_nodig)}" if book_res.bewijs_nodig else "")
        return Reply(text_out, "bookkeeping", book_res.risk_zone,
                     requires_confirmation=book_res.risk_zone == RiskZone.GROEN)

    def _bank(self, intent: Intent, *, tenant_id: str, file_content=None, **_) -> Reply:
        if not file_content:
            return Reply("Stuur een bankexport (CAMT.053 XML, MT940 of CSV) mee om te "
                         "importeren.", "bank", RiskZone.ORANJE)
        txns = self.bank_importer.parse(file_content)
        self.store.save_bank_txns(txns, tenant_id=tenant_id)
        total_in = sum(t.amount.cents for t in txns if t.amount.cents > 0)
        total_out = sum(-t.amount.cents for t in txns if t.amount.cents < 0)
        from boekhouder.domain.money import Money, format_eur
        return Reply(
            f"{len(txns)} banktransacties geïmporteerd "
            f"(bij {format_eur(Money(total_in))}, af {format_eur(Money(total_out))}). "
            f"Stuur nu bonnen om te koppelen of vraag een prognose.", "bank", RiskZone.GROEN)

    def _fiscal(self, intent: Intent, **_) -> Reply:
        res = self.fiscal.run(intent.raw)
        return Reply(formatters.fiscaal_advies(res.payload), "fiscal", res.risk_zone)

    _ENERGY_WORDS = ("zonnepanel", "warmtepomp", "laadpaal", "isolatie", "energie",
                     "led", "accu", "zonneboiler", "warmteterugwin")
    _MILIEU_WORDS = ("milieu", "elektrische", "elektrisch", "recycl", "circulair")

    def _optimize(self, intent: Intent, *, tenant_id: str, **_) -> Reply:
        profile = self.profile(tenant_id)
        totals = self.store.financial_totals(tenant_id)
        low = intent.raw.lower()
        # Concreet bedrag genoemd -> reken het investeringsvoordeel uit.
        if intent.amount and intent.amount.cents > 0 and \
                any(w in low for w in ("investe", "aanschaf", "kopen", "koop", "bedrijfsmiddel",
                                       "machine", "zonnepan", "warmtepomp", "laadpaal")):
            winst = max(0, totals.get("omzet_cents", 0) - totals.get("kosten_cents", 0)) / 100
            energy = any(w in low for w in self._ENERGY_WORDS)
            milieu = any(w in low for w in self._MILIEU_WORDS)
            benefit = self.optimization.investment_benefit(
                float(intent.amount.amount), winst, profile.legal_form,
                energy=energy, milieu=milieu)
            return Reply(formatters.investerings_voordeel(benefit), "optimization", RiskZone.GROEN)
        # Anders: de volledige scan + proactieve signalen.
        ops = self.optimization.scan(profile, totals)
        alerts = self.optimization.proactive_alerts(profile, totals)
        return Reply(formatters.optimalisatie_scan(ops, alerts), "optimization", RiskZone.GROEN)

    def _cfo(self, intent: Intent, *, tenant_id: str, **_) -> Reply:
        # Een prognose-vraag krijgt een vooruitblik; anders de actuele analyse.
        low = intent.raw.lower()
        if any(w in low for w in ("prognose", "prognoses", "voorspel", "verwacht",
                                  "komende", "vooruit", "forecast")):
            res = self.forecast.run(self.store.get_bank_txns(tenant_id),
                                    self.store.financial_totals(tenant_id),
                                    self.profile(tenant_id))
            tip = "\n\n💡 Tip: typ 'bespaar belasting' voor een legale optimalisatie-scan."
            return Reply(formatters.prognose(res.payload) + tip, "forecast", res.risk_zone)
        fin = self.cfo.financials_from_totals(self.store.financial_totals(tenant_id))
        res = self.cfo.run(fin)
        return Reply(formatters.financiele_analyse(res.payload), "cfo", res.risk_zone)

    def _unknown(self, intent: Intent, **_) -> Reply:
        return Reply(
            "Stuur mij je eerste bon, factuur, banktransactie, offerteverzoek of "
            "factuuropdracht. Ik verwerk hem, koppel hem waar mogelijk aan je "
            "administratie en geef direct aan of het fiscaal groen, oranje of rood is. "
            "Vraag ook gerust om een prognose, fiscaal advies of typ 'bespaar belasting' "
            "voor een legale optimalisatie-scan.",
            "intake", RiskZone.GROEN)
