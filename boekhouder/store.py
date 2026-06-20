"""Persistence — multi-tenant store op sqlite of PostgreSQL (via ``boekhouder.db``).

Bewaart wat een herstart moet overleven en auditbaar moet zijn: gebruikers en tenants
(bedrijven), opvolgende documentnummers (nooit overgeslagen/dubbel — sectie 10), de
audit log (sectie 13), versie-/bronbeheerde leerregels (agent J), de controlelijst,
geïmporteerde banktransacties, en bewaarde boekingen/facturen voor prognoses.

Alle administratiedata is per ``tenant_id`` afgeschermd; elk bedrijf ziet alleen het
eigen materiaal. De backend (sqlite of PostgreSQL) wordt door ``boekhouder.db`` bepaald
op basis van ``BOEKHOUDER_DATABASE_URL``.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone

from boekhouder.config import get_settings
from boekhouder.db import DB
from boekhouder.domain.documents import BankTransaction, Boeking, SalesInvoice
from boekhouder.domain.learning import Leerregel
from boekhouder.domain.money import Money

LOCAL_TENANT = "local"          # standaard-tenant voor CLI/dashboard zonder login

_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS tenants (id TEXT PRIMARY KEY, json TEXT, created_at TEXT)",
    "CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT UNIQUE, "
    "password_hash TEXT, tenant_id TEXT, role TEXT DEFAULT 'owner', "
    "provider TEXT DEFAULT 'password', created_at TEXT)",
    "CREATE TABLE IF NOT EXISTS counters (tenant_id TEXT, name TEXT, value INTEGER, "
    "PRIMARY KEY (tenant_id, name))",
    "CREATE TABLE IF NOT EXISTS audit (id __AUTOPK__, tenant_id TEXT DEFAULT 'local', "
    "ts TEXT, actor TEXT, input TEXT, doc_id TEXT, txn_id TEXT, proposed_action TEXT, "
    "confidence REAL, decision TEXT, confirmed_by TEXT, final_id TEXT)",
    "CREATE TABLE IF NOT EXISTS learning_rules (rule_id TEXT PRIMARY KEY, "
    "tenant_id TEXT DEFAULT 'local', json TEXT)",
    "CREATE TABLE IF NOT EXISTS controlelijst (id __AUTOPK__, tenant_id TEXT DEFAULT 'local', "
    "ts TEXT, kind TEXT, summary TEXT, json TEXT, status TEXT DEFAULT 'open')",
    "CREATE TABLE IF NOT EXISTS bank_txns (tenant_id TEXT DEFAULT 'local', txn_id TEXT, "
    "date TEXT, cents INTEGER, counterparty TEXT, iban TEXT, description TEXT, source TEXT)",
    "CREATE TABLE IF NOT EXISTS bookings (id __AUTOPK__, tenant_id TEXT DEFAULT 'local', "
    "ts TEXT, supplier TEXT, doc_date TEXT, incl_cents INTEGER, btw_cents INTEGER, "
    "excl_cents INTEGER, category TEXT, grootboek TEXT, risk_zone TEXT, definitief INTEGER DEFAULT 0)",
    "CREATE TABLE IF NOT EXISTS invoices (id __AUTOPK__, tenant_id TEXT DEFAULT 'local', "
    "ts TEXT, number TEXT, customer TEXT, incl_cents INTEGER, btw_cents INTEGER, "
    "excl_cents INTEGER, due_date TEXT, status TEXT DEFAULT 'concept')",
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, url: str | None = None) -> None:
        s = get_settings()
        self.db = DB(url if url is not None else (s.database_url or s.db_path))
        self._init()
        self._migrate()
        self.ensure_tenant(LOCAL_TENANT, {"name": s.company_name})

    def _init(self) -> None:
        for stmt in _SCHEMA:
            self.db.execute(self.db.ddl(stmt))

    def _migrate(self) -> None:
        """Voeg ontbrekende kolommen toe aan oudere DB-versies (idempotent)."""
        for table in ("audit", "learning_rules", "controlelijst", "bank_txns"):
            if not self.db.column_exists(table, "tenant_id"):
                self.db.execute(
                    f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT DEFAULT 'local'")
        if not self.db.column_exists("bookings", "grootboek"):
            self.db.execute("ALTER TABLE bookings ADD COLUMN grootboek TEXT")

    # ---- tenants & users -------------------------------------------------
    def ensure_tenant(self, tenant_id: str, profile: dict) -> None:
        self.db.execute(
            "INSERT INTO tenants(id, json, created_at) VALUES(?,?,?) "
            "ON CONFLICT(id) DO NOTHING", (tenant_id, json.dumps(profile), _now()))

    def create_tenant(self, profile: dict) -> str:
        tenant_id = f"t-{uuid.uuid4().hex[:10]}"
        self.db.execute("INSERT INTO tenants(id, json, created_at) VALUES(?,?,?)",
                        (tenant_id, json.dumps(profile), _now()))
        return tenant_id

    def get_tenant(self, tenant_id: str) -> dict | None:
        row = self.db.query_one("SELECT json FROM tenants WHERE id=?", (tenant_id,))
        return json.loads(row["json"]) if row else None

    def update_tenant(self, tenant_id: str, profile: dict) -> None:
        self.db.execute("UPDATE tenants SET json=? WHERE id=?",
                        (json.dumps(profile), tenant_id))

    def create_user(self, email: str, password_hash: str, tenant_id: str,
                    *, role: str = "owner", provider: str = "password") -> str:
        user_id = f"u-{uuid.uuid4().hex[:10]}"
        self.db.execute(
            "INSERT INTO users(id, email, password_hash, tenant_id, role, provider, created_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (user_id, email.lower(), password_hash, tenant_id, role, provider, _now()))
        return user_id

    def get_user_by_email(self, email: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM users WHERE email=?", (email.lower(),))
        return dict(row) if row else None

    def get_user(self, user_id: str) -> dict | None:
        row = self.db.query_one("SELECT * FROM users WHERE id=?", (user_id,))
        return dict(row) if row else None

    # ---- sequential numbering (atomic, per tenant) ----------------------
    def next_number(self, kind: str, prefix: str | None = None,
                    tenant_id: str = LOCAL_TENANT) -> str:
        year = datetime.now(timezone.utc).year
        key = f"{kind}-{year}"
        # Atomaire upsert: geen race, ook met meerdere workers/PostgreSQL.
        row = self.db.query_one(
            "INSERT INTO counters(tenant_id, name, value) VALUES(?,?,1) "
            "ON CONFLICT(tenant_id, name) DO UPDATE SET value = counters.value + 1 "
            "RETURNING value", (tenant_id, key))
        value = row["value"] if isinstance(row, dict) else row[0]
        pfx = prefix or {"factuur": "F", "offerte": "O"}.get(kind, kind[:1].upper())
        return f"{pfx}{year}-{value:04d}"

    # ---- audit log ------------------------------------------------------
    def log(self, *, tenant_id: str = LOCAL_TENANT, **fields) -> int:
        cols = ["tenant_id", "ts", "actor", "input", "doc_id", "txn_id",
                "proposed_action", "confidence", "decision", "confirmed_by", "final_id"]
        values = [tenant_id, fields.get("ts", _now())] + [fields.get(c) for c in cols[2:]]
        return self.db.insert(
            f"INSERT INTO audit ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            tuple(values))

    def audit_trail(self, limit: int = 100, tenant_id: str = LOCAL_TENANT) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM audit WHERE tenant_id=? ORDER BY id DESC LIMIT ?", (tenant_id, limit))
        return [dict(r) for r in rows]

    # ---- learning rules -------------------------------------------------
    def save_rule(self, rule: Leerregel, tenant_id: str = LOCAL_TENANT) -> None:
        data = asdict(rule)
        data["valid_from"] = rule.valid_from.isoformat()
        data["valid_to"] = rule.valid_to.isoformat() if rule.valid_to else None
        data["last_checked"] = rule.last_checked.isoformat()
        self.db.execute(
            "INSERT INTO learning_rules(rule_id, tenant_id, json) VALUES(?,?,?) "
            "ON CONFLICT(rule_id) DO UPDATE SET json=excluded.json",
            (rule.rule_id, tenant_id, json.dumps(data)))

    def get_rules(self, tenant_id: str = LOCAL_TENANT) -> list[Leerregel]:
        rows = self.db.query(
            "SELECT json FROM learning_rules WHERE tenant_id=?", (tenant_id,))
        out: list[Leerregel] = []
        for r in rows:
            d = json.loads(r["json"])
            d["valid_from"] = date.fromisoformat(d["valid_from"])
            d["valid_to"] = date.fromisoformat(d["valid_to"]) if d["valid_to"] else None
            d["last_checked"] = date.fromisoformat(d["last_checked"])
            out.append(Leerregel(**{k: v for k, v in d.items() if k != "created_at"}))
        return out

    # ---- controlelijst --------------------------------------------------
    def add_controlelijst(self, kind: str, summary: str, payload: dict | None = None,
                          tenant_id: str = LOCAL_TENANT) -> int:
        return self.db.insert(
            "INSERT INTO controlelijst(tenant_id, ts, kind, summary, json) VALUES(?,?,?,?,?)",
            (tenant_id, _now(), kind, summary, json.dumps(payload or {})))

    def controlelijst(self, status: str = "open", tenant_id: str = LOCAL_TENANT) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM controlelijst WHERE tenant_id=? AND status=? ORDER BY id DESC",
            (tenant_id, status))
        return [dict(r) for r in rows]

    def resolve_controlelijst(self, item_id: int, tenant_id: str = LOCAL_TENANT) -> None:
        self.db.execute(
            "UPDATE controlelijst SET status='resolved' WHERE id=? AND tenant_id=?",
            (item_id, tenant_id))

    # ---- bank transactions ----------------------------------------------
    def save_bank_txns(self, txns: list[BankTransaction], tenant_id: str = LOCAL_TENANT) -> int:
        for t in txns:
            self.db.execute(
                "INSERT INTO bank_txns(tenant_id, txn_id, date, cents, counterparty, "
                "iban, description, source) VALUES (?,?,?,?,?,?,?,?)",
                (tenant_id, t.txn_id, t.date.isoformat(), t.amount.cents, t.counterparty,
                 t.counterparty_iban, t.description, t.source))
        return len(txns)

    def get_bank_txns(self, tenant_id: str = LOCAL_TENANT) -> list[BankTransaction]:
        rows = self.db.query("SELECT * FROM bank_txns WHERE tenant_id=?", (tenant_id,))
        return [BankTransaction(
            date=date.fromisoformat(r["date"]), amount=Money(r["cents"]),
            counterparty=r["counterparty"] or "", counterparty_iban=r["iban"] or "",
            description=r["description"] or "", source=r["source"] or "",
            txn_id=r["txn_id"] or "") for r in rows]

    # ---- bookings & invoices (voor prognoses/financiën) ------------------
    def save_booking(self, b: Boeking, tenant_id: str = LOCAL_TENANT) -> int:
        return self.db.insert(
            "INSERT INTO bookings(tenant_id, ts, supplier, doc_date, incl_cents, "
            "btw_cents, excl_cents, category, grootboek, risk_zone, definitief) "
            "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (tenant_id, _now(), b.supplier, b.doc_date.isoformat() if b.doc_date else None,
             b.total_incl.cents, b.btw.cents, b.total_excl.cents, b.category,
             b.grootboek, b.risk_zone.value, int(b.is_definitief)))

    def save_invoice(self, inv: SalesInvoice, tenant_id: str = LOCAL_TENANT,
                     status: str = "concept") -> int:
        return self.db.insert(
            "INSERT INTO invoices(tenant_id, ts, number, customer, incl_cents, "
            "btw_cents, excl_cents, due_date, status) VALUES(?,?,?,?,?,?,?,?,?)",
            (tenant_id, _now(), inv.invoice_number, inv.customer_name,
             inv.total_incl.cents, inv.total_btw.cents, inv.total_excl.cents,
             inv.due_date.isoformat() if inv.due_date else None, status))

    def list_invoices(self, tenant_id: str = LOCAL_TENANT) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM invoices WHERE tenant_id=? ORDER BY id DESC", (tenant_id,))
        return [dict(r) for r in rows]

    def list_bookings(self, tenant_id: str = LOCAL_TENANT) -> list[dict]:
        rows = self.db.query(
            "SELECT * FROM bookings WHERE tenant_id=? ORDER BY id DESC", (tenant_id,))
        return [dict(r) for r in rows]

    def financial_totals(self, tenant_id: str = LOCAL_TENANT) -> dict:
        """Geaggregeerde cijfers voor CFO-analyse en prognose."""
        inv = self.db.query_one(
            "SELECT COALESCE(SUM(excl_cents),0) excl, COALESCE(SUM(btw_cents),0) btw, "
            "COALESCE(SUM(CASE WHEN status!='betaald' THEN incl_cents ELSE 0 END),0) openc "
            "FROM invoices WHERE tenant_id=?", (tenant_id,))
        # Investeringen (activa-rekeningen 0xxx) zijn geen jaarkosten -> uitsluiten van
        # de kostentelling (ze worden afgeschreven, niet ineens als kosten geboekt).
        book = self.db.query_one(
            "SELECT COALESCE(SUM(excl_cents),0) excl, COALESCE(SUM(btw_cents),0) btw "
            "FROM bookings WHERE tenant_id=? AND (grootboek IS NULL OR grootboek NOT LIKE '0%')",
            (tenant_id,))
        return {
            "omzet_cents": int(inv["excl"]), "omzet_btw_cents": int(inv["btw"]),
            "open_cents": int(inv["openc"]),
            "kosten_cents": int(book["excl"]), "kosten_btw_cents": int(book["btw"]),
        }


_STORE: Store | None = None


def get_store() -> Store:
    global _STORE
    if _STORE is None:
        _STORE = Store()
    return _STORE
