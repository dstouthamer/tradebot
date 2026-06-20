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
