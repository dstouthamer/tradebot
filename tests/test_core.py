"""Deterministic unit tests — no network, no API keys required.

Run:  python -m pytest tests/ -q
  or: python tests/test_core.py
"""
from __future__ import annotations

import os
import tempfile
from datetime import date

from boekhouder.agents.bank_matching import BankMatchingAgent, score
from boekhouder.agents.compliance import ComplianceAgent
from boekhouder.agents.fiscal import FiscalAgent
from boekhouder.agents.intake import IntakeAgent
from boekhouder.agents.invoice import InvoiceAgent
from boekhouder.domain.documents import BankTransaction, ExtractedDocument
from boekhouder.domain.enums import BtwTarief, IntentType, RiskZone
from boekhouder.domain.money import Money, btw_from_excl, btw_from_incl, format_eur
from boekhouder.engine import rules
from boekhouder.providers.bank_import import FileBankImporter, parse_camt053, parse_mt940


# --------------------------------------------------------------------- money
def test_btw_from_excl():
    split = btw_from_excl(Money.euro(1850), BtwTarief.HOOG)
    assert split.btw == Money.euro("388.50")
    assert split.incl == Money.euro("2238.50")


def test_btw_from_incl_roundtrip():
    split = btw_from_incl(Money.euro(6500), BtwTarief.HOOG)
    assert split.excl + split.btw == Money.euro(6500)
    assert split.btw == Money.euro("1128.10")


def test_btw_low_and_verlegd():
    assert btw_from_excl(Money.euro(100), BtwTarief.LAAG).btw == Money.euro("9.00")
    assert btw_from_excl(Money.euro(100), BtwTarief.VERLEGD).btw == Money.euro(0)


def test_format_eur_dutch():
    assert format_eur(Money.euro("2238.50")) == "€2.238,50"
    assert format_eur(Money.euro("-86.45")) == "-€86,45"


# -------------------------------------------------------------------- intake
def test_intake_factuur():
    intent = IntakeAgent().classify("Maak factuur voor De Vries airco montage 1850 ex btw")
    assert intent.type == IntentType.MAAK_FACTUUR
    assert intent.customer == "De Vries"
    assert intent.amount == Money.euro(1850)
    assert intent.amount_basis == "excl"


def test_intake_offerte_incl():
    intent = IntakeAgent().classify("Maak offerte hybride warmtepomp Apeldoorn 6500 incl btw")
    assert intent.type == IntentType.MAAK_OFFERTE
    assert intent.amount == Money.euro(6500)
    assert intent.amount_basis == "incl"
    assert intent.customer is None       # 'Apeldoorn' is a place, not a customer


def test_intake_bon_and_confirm():
    ia = IntakeAgent()
    assert ia.classify("Bonnetje Gamma project Jansen").type == IntentType.UPLOAD_BON
    assert ia.classify("ja").type == IntentType.BEVESTIG


# ------------------------------------------------------------------- invoice
def test_invoice_totals():
    intent = IntakeAgent().classify("Maak factuur voor De Vries airco montage 1850 ex btw")
    res = InvoiceAgent().run(intent, invoice_number="F2026-0001")
    inv = res.payload
    assert inv.total_incl == Money.euro("2238.50")
    assert res.risk_zone == RiskZone.GROEN
    assert res.actie_nodig == "bevestigen"


# -------------------------------------------------------------- bank matching
def _doc():
    return ExtractedDocument(supplier="Gamma", doc_date=date(2026, 6, 12),
                             total_incl=Money.euro("124.80"))


def test_match_exact_high_confidence():
    txn = BankTransaction(date=date(2026, 6, 13), amount=Money.euro("-124.80"),
                          counterparty="Gamma Apeldoorn")
    c = score(_doc(), txn)
    assert c.confidence >= rules.MATCH_CONFIRM
    assert rules.match_action(c.confidence) in ("boeken", "bevestigen")


def test_match_poor_goes_to_controlelijst_band():
    txn = BankTransaction(date=date(2026, 6, 1), amount=Money.euro("-500.00"),
                          counterparty="Onbekend")
    c = score(_doc(), txn)
    assert c.confidence < rules.MATCH_CONFIRM


def test_match_banding():
    assert rules.match_action(96) == "boeken"
    assert rules.match_action(85) == "bevestigen"
    assert rules.match_action(60) == "controleren"
    assert rules.match_action(10) == "afwijzen"


# ---------------------------------------------------------------- compliance
def test_compliance_blocks_prive():
    res = ComplianceAgent().run("Boek deze prive aankoop als zakelijk")
    assert res.blocked and res.risk_zone == RiskZone.ROOD
    assert res.advies                     # legal alternative offered


def test_compliance_blocks_backdate_and_fake():
    ca = ComplianceAgent()
    assert ca.run("Kun je de factuur backdaten naar vorig jaar").blocked
    assert ca.run("Verzin een bon voor extra kosten").blocked


def test_compliance_allows_normal():
    assert not ComplianceAgent().run("Maak factuur voor Jansen 1000 ex btw").blocked


def test_compliance_blocks_underreporting_turnover():
    ca = ComplianceAgent()
    assert ca.run("hoe kan ik minder omzet opgeven").blocked
    assert ca.run("kan ik wat omzet zwart houden").blocked
    # legale vraag wordt NIET geblokkeerd
    assert not ca.run("hoe kan ik minder belasting betalen").blocked


def test_compliance_blocks_sham_constructions():
    ca = ComplianceAgent()
    assert ca.run("kan ik mijn omzet naar Bulgarije verplaatsen om minder btw").blocked
    assert ca.run("zet een brievenbusfirma in Dubai op").blocked
    # feitelijke EU-btw-vraag is geen fraude
    assert not ca.run("wat is de btw bij leveren aan Duitsland").blocked


def test_eu_btw_knowledge():
    from boekhouder.domain import eu_btw

    assert eu_btw.rate("NL") == 21
    low = dict(eu_btw.lowest(3))
    assert "LU" in low                      # Luxemburg laagste
    assert max(eu_btw.EU_BTW.values()) == eu_btw.EU_BTW["HU"]   # Hongarije hoogste


def test_knowledge_review_flags_outdated():
    import datetime

    from boekhouder import knowledge

    items = knowledge.review(datetime.date(2030, 6, 1))   # ver in de toekomst
    onderwerpen = " ".join(i["onderwerp"] for i in items)
    assert "Belastingtarieven" in onderwerpen and "btw" in onderwerpen.lower()


# ------------------------------------------------------------- optimization
def test_optimization_scan_is_sector_and_legal():
    from boekhouder.agents.optimization import OptimizationAgent
    from boekhouder.domain.company import CompanyProfile
    from boekhouder.domain.enums import RiskZone

    prof = CompanyProfile.from_dict({"name": "K", "sector": "VERDUURZAMING",
                                     "legal_form": "EENMANSZAAK"})
    ops = OptimizationAgent().scan(prof, {"omzet_cents": 8_000_000, "kosten_cents": 2_000_000})
    titels = " ".join(o.titel.lower() for o in ops)
    assert "eia" in titels and ("mia" in titels or "vamil" in titels)   # sector-relevant
    assert any(o.zone == RiskZone.GROEN for o in ops)                   # direct verdedigbaar
    # geen enkele "kans" verlaagt de omzet — uitsluitend belasting
    assert not any("omzet" in o.titel.lower() and "verlaag" in o.actie.lower() for o in ops)


def test_investment_benefit_energy():
    from boekhouder.agents.optimization import OptimizationAgent
    from boekhouder.domain import tax_rates

    b = OptimizationAgent().investment_benefit(20_000, winst=50_000,
                                               legal_form="EENMANSZAAK", energy=True)
    assert b.kia == round(20_000 * tax_rates.KIA_TARIEF, 2)      # 5.600
    assert b.eia == round(20_000 * tax_rates.EIA_TARIEF, 2)      # 8.000
    assert b.extra_aftrek == b.kia + b.eia
    assert b.btw_terug == round(20_000 * tax_rates.BTW_HOOG, 2)  # 4.200
    assert 0 < b.belastingbesparing < b.extra_aftrek            # besparing = aftrek * marginaal


def test_kia_tiers():
    from boekhouder.domain import tax_rates

    assert tax_rates.kia_deduction(1_000) == 0.0                 # onder drempel
    assert tax_rates.kia_deduction(10_000) == 2_800.0           # 28%
    assert tax_rates.kia_deduction(100_000) == tax_rates.KIA_FLAT  # middenband = vast
    assert tax_rates.kia_deduction(500_000) == 0.0              # boven max


def test_pdf_detection_graceful():
    from boekhouder.providers.ocr_tesseract import StubOcr, _is_pdf

    assert _is_pdf(b"%PDF-1.7 ...") and not _is_pdf(b"\x89PNG")
    # zonder OCR-libs mag het niet crashen op een PDF
    doc = StubOcr().extract(image_bytes=b"%PDF-1.4 onleesbaar")
    assert doc is not None


def test_vat_filing_without_moneybird():
    from boekhouder.providers.moneybird import MoneybirdProvider

    result = MoneybirdProvider().file_vat_return(None)   # geen token -> dry-run
    assert result["filed"] is False
    assert "zelf in" in result["message"].lower() or "geen moneybird" in result["message"].lower()


def test_grootboek_classification():
    from boekhouder.domain import grootboek

    # kosten op trefwoord
    assert grootboek.classify("Shell brandstof").nummer == "4500"
    assert grootboek.classify("Gamma materialen installatie").nummer == "7000"
    assert grootboek.classify("KPN telefoon").nummer == "4805"
    assert grootboek.classify("iets onbekends").nummer == "4900"        # default kosten
    # investering -> activa (0xxx)
    z = grootboek.classify("zonnepanelen", is_investment=True, energy=True)
    assert z.nummer == "0350" and z.soort == "activa"
    assert grootboek.classify("boormachine", is_investment=True).nummer == "0300"


def test_bookkeeping_assigns_grootboek():
    from boekhouder.agents.bookkeeping import BookkeepingAgent
    from boekhouder.domain.documents import ExtractedDocument
    from boekhouder.domain.enums import BtwTarief, EvidenceQuality

    doc = ExtractedDocument(supplier="SolarTech", description="zonnepanelen",
                            total_incl=Money.euro("6050.00"), btw_tarief=BtwTarief.HOOG,
                            evidence_quality=EvidenceQuality.HOOG)
    b = BookkeepingAgent().build(doc)
    assert b.grootboek == "0350"            # investering -> activa
    assert b.grootboek_naam.startswith("Zonnepanelen")


def test_detect_investment():
    from boekhouder.agents.optimization import OptimizationAgent

    det = OptimizationAgent.detect_investment
    assert det("zonnepanelen SolarTech", 5_000) == (True, True, False)    # energie
    assert det("boormachine gereedschap", 600) == (True, False, False)   # bedrijfsmiddel
    assert det("schroeven", 24) == (False, False, False)                 # te klein
    assert det("kantoorartikelen", 600)[0] is False                      # geen investering


def test_proactive_alerts_year_end():
    import datetime as _dt

    from boekhouder.agents.optimization import OptimizationAgent
    from boekhouder.domain.company import CompanyProfile

    prof = CompanyProfile.from_dict({"name": "K", "sector": "HANDEL", "legal_form": "EENMANSZAAK"})
    q4 = OptimizationAgent().proactive_alerts(prof, {}, today=_dt.date(2026, 11, 15))
    assert any("31-12" in a for a in q4)                         # jaareinde-signaal in Q4


# ----------------------------------------------------------------- fiscal
def test_fiscal_never_says_safe():
    res = FiscalAgent().run("telefoon zakelijk aftrekken")
    text = (res.payload.conclusie + res.payload.risico).lower()
    assert "verdedigbaar" in text or "alleen doen" in text


# ------------------------------------------------------------- bank importers
_CAMT = """<?xml version="1.0"?>
<Document><BkToCstmrStmt><Stmt><Ntry>
  <Amt Ccy="EUR">124.80</Amt><CdtDbtInd>DBIT</CdtDbtInd>
  <BookgDt><Dt>2026-06-13</Dt></BookgDt>
  <NtryDtls><TxDtls><RltdPties><Cdtr><Nm>Gamma Apeldoorn</Nm></Cdtr></RltdPties>
  <RmtInf><Ustrd>Project Jansen</Ustrd></RmtInf></TxDtls></NtryDtls>
</Ntry></Stmt></BkToCstmrStmt></Document>"""

_MT940 = """:20:STARTUMS
:25:NL00BANK0123456789
:28C:00001
:61:2606130613D124,80NTRFNONREF
:86:/NAME/Gamma Apeldoorn/REMI/Project Jansen
:62F:C260613EUR1000,00"""


def test_parse_camt053():
    txns = parse_camt053(_CAMT)
    assert len(txns) == 1
    assert txns[0].amount == Money.euro("-124.80")
    assert txns[0].counterparty == "Gamma Apeldoorn"


def test_parse_mt940():
    txns = parse_mt940(_MT940)
    assert len(txns) == 1
    assert txns[0].amount == Money.euro("-124.80")
    assert txns[0].date == date(2026, 6, 13)


def test_parse_csv_fixture():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "sample_ing.csv")
    with open(path, encoding="utf-8") as fh:
        txns = FileBankImporter().parse(fh.read())
    assert len(txns) == 3
    gamma = next(t for t in txns if "Gamma" in t.counterparty)
    assert gamma.amount == Money.euro("-124.80")        # 'Af' -> negative
    devries = next(t for t in txns if "Vries" in t.counterparty)
    assert devries.amount == Money.euro("2238.50")      # 'Bij' -> positive


# ------------------------------------------------------------- approval gate
def test_router_confirmation_flow():
    # Isolated DB so the test is hermetic.
    import boekhouder.store as store_mod
    from boekhouder.config import get_settings

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    get_settings().db_path = path
    store_mod._STORE = None
    from boekhouder.engine.router import Router

    r = Router()
    rep = r.handle("Maak factuur voor Jansen montage 1000 ex btw", session_id="s1")
    assert rep.requires_confirmation
    assert r.gate.pending("s1") is not None
    outcome = r.gate.confirm("s1")
    assert outcome["ok"] and outcome["final_id"].startswith("F")
    assert r.gate.pending("s1") is None
    os.remove(path)


# ------------------------------------------------------------------- runner
if __name__ == "__main__":
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            passed += 1
            print(f"ok   {fn.__name__}")
        except Exception:  # noqa: BLE001
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} tests geslaagd")
    raise SystemExit(0 if passed == len(fns) else 1)
