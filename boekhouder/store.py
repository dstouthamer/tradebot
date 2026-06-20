"""Persistence — a small sqlite store (stdlib only).

Holds the things that must survive a restart and be auditable: sequential document
numbers (never skipped or duplicated — masterprompt section 10), the audit log
(section 13), versioned learning rules (agent J), the controlelijst of uncertain items,
and imported bank transactions for matching.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import asdict
from datetime import date, datetime, timezone
from typing import Any

from boekhouder.config import get_settings
from boekhouder.domain.documents import BankTransaction
from boekhouder.domain.learning import Leerregel
from boekhouder.domain.money import Money

_LOCK = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, path: str | None = None) -> None:
        self.path = path or get_settings().db_path
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        with self.conn:
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS counters (name TEXT PRIMARY KEY, value INTEGER);
                CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, actor TEXT, input TEXT,
                    doc_id TEXT, txn_id TEXT, proposed_action TEXT, confidence REAL,
                    decision TEXT, confirmed_by TEXT, final_id TEXT);
                CREATE TABLE IF NOT EXISTS learning_rules (rule_id TEXT PRIMARY KEY, json TEXT);
                CREATE TABLE IF NOT EXISTS controlelijst (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT, summary TEXT,
                    json TEXT, status TEXT DEFAULT 'open');
                CREATE TABLE IF NOT EXISTS bank_txns (
                    txn_id TEXT, date TEXT, cents INTEGER, counterparty TEXT,
                    iban TEXT, description TEXT, source TEXT);
                """
            )

    # ---- sequential numbering (never skip/duplicate) ---------------------
    def next_number(self, kind: str, prefix: str | None = None) -> str:
        year = datetime.now(timezone.utc).year
        key = f"{kind}-{year}"
        with _LOCK, self.conn:
            row = self.conn.execute("SELECT value FROM counters WHERE name=?", (key,)).fetchone()
            value = (row["value"] if row else 0) + 1
            self.conn.execute(
                "INSERT INTO counters(name, value) VALUES(?,?) "
                "ON CONFLICT(name) DO UPDATE SET value=excluded.value", (key, value))
        pfx = prefix or {"factuur": "F", "offerte": "O"}.get(kind, kind[:1].upper())
        return f"{pfx}{year}-{value:04d}"

    # ---- audit log ------------------------------------------------------
    def log(self, **fields: Any) -> int:
        cols = ["ts", "actor", "input", "doc_id", "txn_id", "proposed_action",
                "confidence", "decision", "confirmed_by", "final_id"]
        values = [fields.get("ts", _now())] + [fields.get(c) for c in cols[1:]]
        with self.conn:
            cur = self.conn.execute(
                f"INSERT INTO audit ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
                values)
        return cur.lastrowid

    def audit_trail(self, limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ---- learning rules -------------------------------------------------
    def save_rule(self, rule: Leerregel) -> None:
        data = asdict(rule)
        data["valid_from"] = rule.valid_from.isoformat()
        data["valid_to"] = rule.valid_to.isoformat() if rule.valid_to else None
        data["last_checked"] = rule.last_checked.isoformat()
        with self.conn:
            self.conn.execute(
                "INSERT INTO learning_rules(rule_id, json) VALUES(?,?) "
                "ON CONFLICT(rule_id) DO UPDATE SET json=excluded.json",
                (rule.rule_id, json.dumps(data)))

    def get_rules(self) -> list[Leerregel]:
        rows = self.conn.execute("SELECT json FROM learning_rules").fetchall()
        out: list[Leerregel] = []
        for r in rows:
            d = json.loads(r["json"])
            d["valid_from"] = date.fromisoformat(d["valid_from"])
            d["valid_to"] = date.fromisoformat(d["valid_to"]) if d["valid_to"] else None
            d["last_checked"] = date.fromisoformat(d["last_checked"])
            d.pop("created_at", None)
            out.append(Leerregel(**{k: v for k, v in d.items() if k != "created_at"}))
        return out

    # ---- controlelijst --------------------------------------------------
    def add_controlelijst(self, kind: str, summary: str, payload: dict | None = None) -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO controlelijst(ts, kind, summary, json) VALUES(?,?,?,?)",
                (_now(), kind, summary, json.dumps(payload or {})))
        return cur.lastrowid

    def controlelijst(self, status: str = "open") -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM controlelijst WHERE status=? ORDER BY id DESC", (status,)).fetchall()
        return [dict(r) for r in rows]

    def resolve_controlelijst(self, item_id: int) -> None:
        with self.conn:
            self.conn.execute(
                "UPDATE controlelijst SET status='resolved' WHERE id=?", (item_id,))

    # ---- bank transactions ----------------------------------------------
    def save_bank_txns(self, txns: list[BankTransaction]) -> int:
        with self.conn:
            for t in txns:
                self.conn.execute(
                    "INSERT INTO bank_txns VALUES (?,?,?,?,?,?,?)",
                    (t.txn_id, t.date.isoformat(), t.amount.cents, t.counterparty,
                     t.counterparty_iban, t.description, t.source))
        return len(txns)

    def get_bank_txns(self) -> list[BankTransaction]:
        rows = self.conn.execute("SELECT * FROM bank_txns").fetchall()
        return [BankTransaction(
            date=date.fromisoformat(r["date"]), amount=Money(r["cents"]),
            counterparty=r["counterparty"] or "", counterparty_iban=r["iban"] or "",
            description=r["description"] or "", source=r["source"] or "",
            txn_id=r["txn_id"] or "") for r in rows]


_STORE: Store | None = None


def get_store() -> Store:
    global _STORE
    if _STORE is None:
        _STORE = Store()
    return _STORE
