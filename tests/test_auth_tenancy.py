"""Deterministische tests voor auth, multi-tenancy en prognose — geen netwerk/keys.

Run:  python -m pytest tests/test_auth_tenancy.py -q
  or: python tests/test_auth_tenancy.py
"""
from __future__ import annotations

import os
import tempfile
from datetime import date


def _fresh_store():
    """Isoleer elke run op een eigen tijdelijke DB."""
    import boekhouder.store as store_mod
    from boekhouder.config import get_settings

    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    get_settings().db_path = path
    store_mod._STORE = None
    return store_mod.get_store(), path


# ------------------------------------------------------------- passwords
def test_password_hash_and_verify():
    from boekhouder.auth.passwords import hash_password, verify_password

    h = hash_password("geheim123")
    assert h.startswith("pbkdf2_sha256$")
    assert verify_password("geheim123", h)
    assert not verify_password("fout", h)


def test_password_min_length():
    from boekhouder.auth.passwords import hash_password

    try:
        hash_password("kort")
        assert False, "verwacht ValueError"
    except ValueError:
        pass


# ---------------------------------------------------------------- tokens
def test_token_roundtrip_and_tamper():
    from boekhouder.auth import tokens

    t = tokens.issue("u-1", "t-1")
    payload = tokens.verify(t)
    assert payload and payload["uid"] == "u-1" and payload["tid"] == "t-1"
    assert tokens.verify(t + "x") is None          # tampered signature
    assert tokens.verify("garbage") is None


def test_token_expiry():
    from boekhouder.auth import tokens

    assert tokens.verify(tokens.issue("u", "t", ttl=-1)) is None


# ------------------------------------------------------------- auth flow
def test_register_login_and_isolation():
    _fresh_store()
    from boekhouder.auth.service import AuthError, AuthService

    a = AuthService()
    s1 = a.register("jan@a.nl", "geheim123", "Bedrijf A")
    s2 = a.register("piet@b.nl", "geheim123", "Bedrijf B")
    assert s1.tenant_id != s2.tenant_id

    # login werkt, fout wachtwoord niet
    assert a.login("jan@a.nl", "geheim123").tenant_id == s1.tenant_id
    try:
        a.login("jan@a.nl", "fout")
        assert False
    except AuthError:
        pass

    # dubbele registratie geweigerd
    try:
        a.register("jan@a.nl", "geheim123", "X")
        assert False
    except AuthError:
        pass

    # token van A wijst naar tenant A
    assert a.resolve(s1.token).tenant_id == s1.tenant_id


def test_tenant_data_isolation():
    _fresh_store()
    from boekhouder.auth.service import AuthService
    from boekhouder.engine.router import Router

    a = AuthService()
    ta = a.register("jan@a.nl", "geheim123", "Bedrijf A").tenant_id
    tb = a.register("piet@b.nl", "geheim123", "Bedrijf B").tenant_id
    r = Router()
    r.handle("Maak factuur voor Klant klus 1000 ex btw", session_id="x", tenant_id=ta)
    r.handle("ja", session_id="x", tenant_id=ta)
    assert len(r.store.audit_trail(tenant_id=ta)) == 2     # propose + confirm
    assert len(r.store.audit_trail(tenant_id=tb)) == 0     # B ziet niets
    assert r.profile(ta).name == "Bedrijf A"
    assert r.profile(tb).name == "Bedrijf B"


def test_numbering_is_per_tenant():
    store, _ = _fresh_store()
    from boekhouder.auth.service import AuthService

    a = AuthService()
    ta = a.register("jan@a.nl", "geheim123", "A").tenant_id
    tb = a.register("piet@b.nl", "geheim123", "B").tenant_id
    assert store.next_number("factuur", tenant_id=ta).endswith("-0001")
    assert store.next_number("factuur", tenant_id=ta).endswith("-0002")
    assert store.next_number("factuur", tenant_id=tb).endswith("-0001")   # eigen reeks


# ---------------------------------------------------------------- forecast
def test_forecast_projects_cashflow():
    _fresh_store()
    from boekhouder.agents.forecast import ForecastAgent
    from boekhouder.domain.company import CompanyProfile
    from boekhouder.domain.documents import BankTransaction
    from boekhouder.domain.money import Money

    txns = [
        BankTransaction(date(2026, 4, 1), Money.euro("3000.00"), "Klant"),
        BankTransaction(date(2026, 4, 5), Money.euro("-1000.00"), "Leverancier"),
        BankTransaction(date(2026, 5, 1), Money.euro("3000.00"), "Klant"),
        BankTransaction(date(2026, 5, 5), Money.euro("-1000.00"), "Leverancier"),
    ]
    totals = {"omzet_cents": 600000, "omzet_btw_cents": 126000,
              "kosten_cents": 200000, "kosten_btw_cents": 42000}
    fc = ForecastAgent().build(txns, totals, CompanyProfile.from_settings(), horizon_days=90)
    assert fc.avg_monthly_net.cents > 0                 # net positive monthly
    assert fc.projected_net.cents > fc.avg_monthly_net.cents
    assert fc.vat_to_reserve == Money.euro("840.00")    # 1260 - 420
    assert fc.tax_indication.cents > 0


def test_forecast_warns_on_no_data():
    _fresh_store()
    from boekhouder.agents.forecast import ForecastAgent
    from boekhouder.domain.company import CompanyProfile

    fc = ForecastAgent().build([], {}, CompanyProfile.from_settings())
    assert any("Geen banktransacties" in w for w in fc.warnings)


def test_api_requires_auth_and_works_with_token():
    _fresh_store()
    from fastapi.testclient import TestClient

    import boekhouder.api.main as main
    main._router = None
    c = TestClient(main.app)
    assert c.post("/bericht", json={"message": "hoi"}).status_code == 401
    tok = c.post("/auth/register",
                 json={"email": "x@y.nl", "password": "geheim123",
                       "company_name": "Z"}).json()["token"]
    h = {"Authorization": f"Bearer {tok}"}
    r = c.post("/bericht", json={"message": "Maak factuur voor Jansen klus 1000 ex btw"}, headers=h)
    assert r.status_code == 200 and r.json()["agent"] == "invoice"


def test_db_dialect_rendering():
    """De DB-laag vertaalt placeholders en DDL per dialect (zonder live server)."""
    from boekhouder.db import DB

    sq = DB("")  # sqlite
    assert sq.dialect == "sqlite"
    assert sq._q("WHERE a=? AND b=?") == "WHERE a=? AND b=?"
    assert "AUTOINCREMENT" in sq.ddl("id __AUTOPK__")

    # Render-logica voor postgres zonder echt te verbinden.
    assert DB._q.__get__(_FakePg())("WHERE a=? AND b=?") == "WHERE a=%s AND b=%s"
    assert "SERIAL PRIMARY KEY" in DB.ddl.__get__(_FakePg())("id __AUTOPK__")


class _FakePg:
    dialect = "postgres"
    is_postgres = True


def test_postgres_backend_optional():
    """Draait alleen als BOEKHOUDER_TEST_PG_URL is gezet (echte Postgres)."""
    url = os.environ.get("BOEKHOUDER_TEST_PG_URL")
    if not url:
        return  # overslaan zonder server
    import boekhouder.store as store_mod
    from boekhouder.config import get_settings

    get_settings().database_url = url
    store_mod._STORE = None
    from boekhouder.auth.service import AuthService

    a = AuthService()
    t1 = a.register("pg1@a.nl", "geheim123", "PG A").tenant_id
    assert a.login("pg1@a.nl", "geheim123").tenant_id == t1
    assert store_mod.get_store().next_number("factuur", tenant_id=t1).endswith("-0001")
    get_settings().database_url = ""


def test_web_ui_served_and_oauth_guarded():
    _fresh_store()
    from fastapi.testclient import TestClient

    import boekhouder.api.main as main
    main._router = None
    c = TestClient(main.app)
    home = c.get("/")
    assert home.status_code == 200 and "AI Boekhouder" in home.text and "loginForm" in home.text
    # OAuth zonder geconfigureerde keys -> nette 400, geen redirect naar provider
    assert c.get("/auth/google/login", follow_redirects=False).status_code == 400


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
