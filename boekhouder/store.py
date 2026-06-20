"""Persistence — een kleine sqlite-store (alleen standaardbibliotheek), multi-tenant.

Bewaart wat een herstart moet overleven en auditbaar moet zijn: gebruikers en tenants
(bedrijven), opvolgende documentnummers (nooit overgeslagen/dubbel — sectie 10), de
audit log (sectie 13), versie-/bronbeheerde leerregels (agent J), de controlelijst,
geïmporteerde banktransacties, en bewaarde boekingen/facturen voor prognoses.

Alle administratiedata is per ``tenant_id`` afgeschermd; elk bedrijf ziet alleen het
eigen materiaal. Voor productie-schaal kan dezelfde interface op PostgreSQL draaien
(zie deploy/), maar sqlite met tenant-scoping volstaat voor de MVP-SaaS.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any

from boekhouder.config import get_settings
from boekhouder.domain.documents import BankTransaction, Boeking, SalesInvoice
from boekhouder.domain.learning import Leerregel
from boekhouder.domain.money import Money

_LOCK = threading.Lock()
LOCAL_TENANT = "local"          # standaard-tenant voor CLI/dashboard zonder login


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or get_settings().db_path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()
        self._migrate()
        self.ensure_tenant(LOCAL_TENANT, {"name": get_settings().company_name})

    def _init(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    id TEXT PRIMARY KEY, json TEXT, created_at TEXT);
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT,
                    tenant_id TEXT, role TEXT DEFAULT 'owner', provider TEXT DEFAULT 'password',
                    created_at TEXT);
                CREATE TABLE IF NOT EXISTS counters (
                    tenant_id TEXT, name TEXT, value INTEGER, PRIMARY KEY (tenant_id, name));
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT DEFAULT 'local',
                    ts TEXT, actor TEXT, input TEXT, doc_id TEXT, txn_id TEXT,
                    proposed_action TEXT, confidence REAL, decision TEXT,
                    confirmed_by TEXT, final_id TEXT);
                CREATE TABLE IF NOT EXISTS learning_rules (
                    rule_id TEXT PRIMARY KEY, tenant_id TEXT DEFAULT 'local', json TEXT);
                CREATE TABLE IF NOT EXISTS controlelijst (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT DEFAULT 'local',
                    ts TEXT, kind TEXT, summary TEXT, json TEXT, status TEXT DEFAULT 'open');
                CREATE TABLE IF NOT EXISTS bank_txns (
                    tenant_id TEXT DEFAULT 'local', txn_id TEXT, date TEXT, cents INTEGER,
                    counterparty TEXT, iban TEXT, description TEXT, source TEXT);
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT DEFAULT 'local',
                    ts TEXT, supplier TEXT, doc_date TEXT, incl_cents INTEGER, btw_cents INTEGER,
                    excl_cents INTEGER, category TEXT, risk_zone TEXT, definitief INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT DEFAULT 'local',
                    ts TEXT, number TEXT, customer TEXT, incl_cents INTEGER, btw_cents INTEGER,
                    excl_cents INTEGER, due_date TEXT, status TEXT DEFAULT 'concept');
                """
            )

    def _migrate(self) -> None:
        """Voeg tenant_id toe aan tabellen uit oudere DB-versies (idempotent)."""
        for table in ("audit", "learning_rules", "controlelijst", "bank_txns"):
            cols = {r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")}
            if "tenant_id" not in cols:
                with self.conn:
                    self.conn.execute(
                        f"ALTER TABLE {table} ADD COLUMN tenant_id TEXT DEFAULT 'local'")

    # ---- tenants & users -------------------------------------------------
    def ensure_tenant(self, tenant_id: str, profile: dict) -> None:
        with self.conn:
            self.conn.execute(
                "INSERT INTO tenants(id, json, created_at) VALUES(?,?,?) "
                "ON CONFLICT(id) DO NOTHING",
                (tenant_id, json.dumps(profile), _now()))

    def create_tenant(self, profile: dict) -> str:
        tenant_id = f"t-{uuid.uuid4().hex[:10]}"
        with self.conn:
            self.conn.execute(
                "INSERT INTO tenants(id, json, created_at) VALUES(?,?,?)",
                (tenant_id, json.dumps(profile), _now()))
        return tenant_id

    def get_tenant(self, tenant_id: str) -> dict | None:
        row = self.conn.execute(
            "SELECT json FROM tenants WHERE id=?", (tenant_id,)).fetchone()
        return json.loads(row["json"]) if row else None

    def update_tenant(self, tenant_id: str, profile: dict) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE tenants SET json=? WHERE id=?", (json.dumps(profile), tenant_id))

    def create_user(self, email: str, password_hash: str, tenant_id: str,
                    *, role: str = "owner", provider: str = "password") -> str:
        user_id = f"u-{uuid.uuid4().hex[:10]}"
        with self.conn:
            self.conn.execute(
                "INSERT INTO users(id, email, password_hash, tenant_id, role, provider, created_at) "
                "VALUES(?,?,?,?,?,?,?)",
                (user_id, email.lower(), password_hash, tenant_id, role, provider, _now()))
        return user_id

    def get_user_by_email(self, email: str) -> dict | None:
        row = self.conn.execute(
            "SELECT * FROM users WHERE email=?", (email.lower(),)).fetchone()
        return dict(row) if row else None

    def get_user(self, user_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
        return dict(row) if row else None

    # ---- sequential numbering (never skip/duplicate, per tenant) ---------
    def next_number(self, kind: str, prefix: str | None = None,
                    tenant_id: str = LOCAL_TENANT) -> str:
        year = datetime.now(timezone.utc).year
        key = f"{kind}-{year}"
        with _LOCK, self.conn:
            row = self.conn.execute(
                "SELECT value FROM counters WHERE tenant_id=? AND name=?",
                (tenant_id, key)).fetchone()
            value = (row["value"] if row else 0) + 1
            self.conn.execute(
                "INSERT INTO counters(tenant_id, name, value) VALUES(?,?,?) "
                "ON CONFLICT(tenant_id, name) DO UPDATE SET value=excluded.value",
                (tenant_id, key, value))
        pfx = prefix or {"factuur": "F", "offerte": "O"}.get(kind, kind[:1].upper())
        return f"{pfx}{year}-{value:04d}"

    # ---- audit log ------------------------------------------------------
    def log(self, *, tenant_id: str = LOCAL_TENANT, **fields: Any) -> int:
        cols = ["tenant_id", "ts", "actor", "input", "doc_id", "txn_id",
                "proposed_action", "confidence", "decision", "confirmed_by", "final_id"]
        values = [tenant_id, fields.get("ts", _now())] + [fields.get(c) for c in cols[2:]]
        with self.conn:
            cur = self.conn.execute(
                f"INSERT INTO audit ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                values)
        return cur.lastrowid

    def audit_trail(self, limit: int = 100, tenant_id: str = LOCAL_TENANT) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM audit WHERE tenant_id=? ORDER BY id DESC LIMIT ?",
            (tenant_id, limit)).fetchall()
        return [dict(r) for r in rows]

    # ---- learning rules -------------------------------------------------
    def save_rule(self, rule: Leerregel, tenant_id: str = LOCAL_TENANT) -> None:
        data = asdict(rule)
        data["valid_from"] = rule.valid_from.isoformat()
        data["valid_to"] = rule.valid_to.isoformat() if rule.valid_to else None
        data["last_checked"] = rule.last_checked.isoformat()
        with self.conn:
            self.conn.execute(
                "INSERT INTO learning_rules(rule_id, tenant_id, json) VALUES(?,?,?) "
                "ON CONFLICT(rule_id) DO UPDATE SET json=excluded.json",
                (rule.rule_id, tenant_id, json.dumps(data)))

    def get_rules(self, tenant_id: str = LOCAL_TENANT) -> list[Leerregel]:
        rows = self.conn.execute(
            "SELECT json FROM learning_rules WHERE tenant_id=?", (tenant_id,)).fetchall()
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
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO controlelijst(tenant_id, ts, kind, summary, json) VALUES(?,?,?,?,?)",
                (tenant_id, _now(), kind, summary, json.dumps(payload or {})))
        return cur.lastrowid

    def controlelijst(self, status: str = "open", tenant_id: str = LOCAL_TENANT) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM controlelijst WHERE tenant_id=? AND status=? ORDER BY id DESC",
            (tenant_id, status)).fetchall()
        return [dict(r) for r in rows]

    def resolve_controlelijst(self, item_id: int, tenant_id: str = LOCAL_TENANT) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE controlelijst SET status='resolved' WHERE id=? AND tenant_id=?",
                (item_id, tenant_id))

    # ---- bank transactions ----------------------------------------------
    def save_bank_txns(self, txns: list[BankTransaction], tenant_id: str = LOCAL_TENANT) -> int:
        with self.conn:
            for t in txns:
                self.conn.execute(
                    "INSERT INTO bank_txns(tenant_id, txn_id, date, cents, counterparty, "
                    "iban, description, source) VALUES (?,?,?,?,?,?,?,?)",
                    (tenant_id, t.txn_id, t.date.isoformat(), t.amount.cents, t.counterparty,
                     t.counterparty_iban, t.description, t.source))
        return len(txns)

    def get_bank_txns(self, tenant_id: str = LOCAL_TENANT) -> list[BankTransaction]:
        rows = self.conn.execute(
            "SELECT * FROM bank_txns WHERE tenant_id=?", (tenant_id,)).fetchall()
        return [BankTransaction(
            date=date.fromisoformat(r["date"]), amount=Money(r["cents"]),
            counterparty=r["counterparty"] or "", counterparty_iban=r["iban"] or "",
            description=r["description"] or "", source=r["source"] or "",
            txn_id=r["txn_id"] or "") for r in rows]

    # ---- bookings & invoices (voor prognoses/financiën) ------------------
    def save_booking(self, b: Boeking, tenant_id: str = LOCAL_TENANT) -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO bookings(tenant_id, ts, supplier, doc_date, incl_cents, "
                "btw_cents, excl_cents, category, risk_zone, definitief) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (tenant_id, _now(), b.supplier,
                 b.doc_date.isoformat() if b.doc_date else None,
                 b.total_incl.cents, b.btw.cents, b.total_excl.cents,
                 b.category, b.risk_zone.value, int(b.is_definitief)))
        return cur.lastrowid

    def save_invoice(self, inv: SalesInvoice, tenant_id: str = LOCAL_TENANT,
                     status: str = "concept") -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO invoices(tenant_id, ts, number, customer, incl_cents, "
                "btw_cents, excl_cents, due_date, status) VALUES(?,?,?,?,?,?,?,?,?)",
                (tenant_id, _now(), inv.invoice_number, inv.customer_name,
                 inv.total_incl.cents, inv.total_btw.cents, inv.total_excl.cents,
                 inv.due_date.isoformat() if inv.due_date else None, status))
        return cur.lastrowid

    def financial_totals(self, tenant_id: str = LOCAL_TENANT) -> dict:
        """Geaggregeerde cijfers voor CFO-analyse en prognose."""
        inv = self.conn.execute(
            "SELECT COALESCE(SUM(excl_cents),0) excl, COALESCE(SUM(btw_cents),0) btw, "
            "COALESCE(SUM(CASE WHEN status!='betaald' THEN incl_cents ELSE 0 END),0) open "
            "FROM invoices WHERE tenant_id=?", (tenant_id,)).fetchone()
        book = self.conn.execute(
            "SELECT COALESCE(SUM(excl_cents),0) excl, COALESCE(SUM(btw_cents),0) btw "
            "FROM bookings WHERE tenant_id=?", (tenant_id,)).fetchone()
        return {
            "omzet_cents": inv["excl"], "omzet_btw_cents": inv["btw"],
            "open_cents": inv["open"],
            "kosten_cents": book["excl"], "kosten_btw_cents": book["btw"],
        }


_STORE: Store | None = None


def get_store() -> Store:
    global _STORE
    if _STORE is None:
        _STORE = Store()
    return _STORE
