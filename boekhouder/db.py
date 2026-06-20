"""Dunne database-laag: dezelfde store-code draait op sqlite én PostgreSQL.

- **sqlite** (standaard, geen config): lokaal en voor een kleine VPS-SaaS prima.
- **PostgreSQL** (zet ``BOEKHOUDER_DATABASE_URL=postgresql://...``): voor echte schaal
  en meerdere gelijktijdige gebruikers. Vereist het optionele pakket ``psycopg``.

Beide backends ondersteunen ``ON CONFLICT`` en ``RETURNING``, dus de SQL is grotendeels
gedeeld. Verschillen (placeholderstijl ``?``/``%s``, auto-increment, ``lastrowid`` vs
``RETURNING``) worden hier afgevangen, zodat ``store.py`` backend-agnostisch blijft.
"""
from __future__ import annotations

import sqlite3
import threading


class DB:
    def __init__(self, url: str | None) -> None:
        self.url = url or ""
        self.lock = threading.RLock()
        if self.url.startswith(("postgres://", "postgresql://")):
            import psycopg
            from psycopg.rows import dict_row

            self.dialect = "postgres"
            self.conn = psycopg.connect(self.url, autocommit=True, row_factory=dict_row)
        else:
            path = (self.url[len("sqlite:///"):] if self.url.startswith("sqlite:///")
                    else (self.url or "boekhouder.db"))
            self.dialect = "sqlite"
            # isolation_level=None -> autocommit: elke statement commit zelf. Nodig omdat
            # een expliciete commit faalt zolang een RETURNING-resultset openstaat.
            self.conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA journal_mode=WAL")

    @property
    def is_postgres(self) -> bool:
        return self.dialect == "postgres"

    def _q(self, sql: str) -> str:
        return sql.replace("?", "%s") if self.is_postgres else sql

    def ddl(self, sql: str) -> str:
        """Render dialect-specifieke DDL-tokens."""
        return sql.replace(
            "__AUTOPK__",
            "SERIAL PRIMARY KEY" if self.is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT")

    # ---- uitvoeren -------------------------------------------------------
    def execute(self, sql: str, params: tuple = ()):  # noqa: ANN201
        # Beide backends draaien in autocommit-modus (sqlite: isolation_level=None,
        # psycopg: autocommit=True), dus geen expliciete commit nodig.
        with self.lock:
            return self.conn.execute(self._q(sql), tuple(params))

    def query(self, sql: str, params: tuple = ()) -> list:
        return self.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple = ()):  # noqa: ANN201
        return self.execute(sql, params).fetchone()

    def insert(self, sql: str, params: tuple = ()) -> int | None:
        """INSERT die het gegenereerde id teruggeeft (RETURNING / lastrowid)."""
        if self.is_postgres:
            row = self.execute(sql + " RETURNING id", params).fetchone()
            return row["id"] if row else None
        return self.execute(sql, params).lastrowid

    def scalar(self, sql: str, params: tuple = ()):  # noqa: ANN201
        row = self.execute(sql, params).fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return next(iter(row.values()))
        return row[0]

    def column_exists(self, table: str, column: str) -> bool:
        if self.is_postgres:
            return self.query_one(
                "SELECT 1 FROM information_schema.columns WHERE table_name=? AND column_name=?",
                (table, column)) is not None
        cols = {r["name"] for r in self.conn.execute(f"PRAGMA table_info({table})")}
        return column in cols
