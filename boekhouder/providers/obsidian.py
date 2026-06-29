"""Obsidian-export: schrijf je boekhouding als Markdown-notities naar een Obsidian-vault.

Veilig en keyless: zonder een ingesteld vault-pad (``BOEKHOUDER_OBSIDIAN_VAULT``) is deze
provider inert. Hij schrijft uitsluitend lokale Markdown-bestanden in de gekozen vault-map
— geen netwerk, niets wordt verzonden of definitief geboekt. Elke notitie krijgt
YAML-frontmatter + tags zodat Obsidian erop kan zoeken/filteren.

De ``render_*``-functies zijn puur en zonder bestandssysteem testbaar (zelfde patroon als
``email_inbox.parse_message``); ``ObsidianVault.export`` doet de feitelijke schrijfactie.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

from boekhouder.config import get_settings
from boekhouder.domain.documents import BankTransaction
from boekhouder.domain.money import Money, format_eur

log = logging.getLogger("boekhouder.obsidian")

_SLUG_STRIP = re.compile(r"[^\w\- ]+", re.UNICODE)


def _euro(cents) -> str:
    """Formatteer een centbedrag (of None) als Nederlands euro, bv. ``€2.238,50``."""
    return format_eur(Money(int(cents or 0)))


def _slug(text: str, *, fallback: str = "notitie") -> str:
    """Bestandsnaam-veilige slug: geen pad-scheidingstekens of rare tekens."""
    cleaned = _SLUG_STRIP.sub("", (text or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:80] or fallback


def _yaml(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = "" if value is None else str(value)
    if s == "" or s != s.strip() or re.search(r"""[:#\[\]{}",'`]""", s):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _frontmatter(data: dict, tags: list[str]) -> str:
    lines = ["---"]
    for key, value in data.items():
        lines.append(f"{key}: {_yaml(value)}")
    if tags:
        lines.append("tags:")
        lines.extend(f"  - {t}" for t in tags)
    lines.append("---")
    return "\n".join(lines)


def _bedrag_tabel(excl_cents, btw_cents, incl_cents) -> str:
    return (
        "| | Bedrag |\n|---|---:|\n"
        f"| Exclusief btw | {_euro(excl_cents)} |\n"
        f"| Btw | {_euro(btw_cents)} |\n"
        f"| **Inclusief btw** | **{_euro(incl_cents)}** |\n"
    )


def render_invoice(row: dict) -> tuple[str, str]:
    """Render een verkoopfactuur-rij (``store.list_invoices``) naar (bestandsnaam, markdown)."""
    number = row.get("number") or f"concept-{row.get('id')}"
    customer = row.get("customer") or "Onbekende klant"
    datum = (row.get("ts") or "")[:10]
    fm = _frontmatter({
        "type": "verkoopfactuur",
        "nummer": number,
        "klant": customer,
        "datum": datum,
        "vervaldatum": row.get("due_date") or "",
        "status": row.get("status") or "concept",
        "bedrag_incl": _euro(row.get("incl_cents")),
        "bedrag_excl": _euro(row.get("excl_cents")),
        "btw": _euro(row.get("btw_cents")),
    }, tags=["boekhouding", "factuur"])
    body = (
        f"\n\n# Factuur {number}\n\n"
        f"- **Klant:** {customer}\n"
        f"- **Datum:** {datum or '—'}\n"
        f"- **Vervaldatum:** {row.get('due_date') or '—'}\n"
        f"- **Status:** {row.get('status') or 'concept'}\n\n"
        + _bedrag_tabel(row.get("excl_cents"), row.get("btw_cents"), row.get("incl_cents"))
    )
    filename = f"{_slug(f'Factuur {number} {customer}', fallback='factuur')}.md"
    return filename, fm + body


def render_booking(row: dict) -> tuple[str, str]:
    """Render een boeking-rij (``store.list_bookings``) naar (bestandsnaam, markdown)."""
    supplier = row.get("supplier") or "Onbekende leverancier"
    datum = row.get("doc_date") or (row.get("ts") or "")[:10]
    fm = _frontmatter({
        "type": "boeking",
        "leverancier": supplier,
        "datum": datum,
        "categorie": row.get("category") or "",
        "grootboek": row.get("grootboek") or "",
        "risico": row.get("risk_zone") or "",
        "definitief": bool(row.get("definitief")),
        "bedrag_incl": _euro(row.get("incl_cents")),
        "bedrag_excl": _euro(row.get("excl_cents")),
        "btw": _euro(row.get("btw_cents")),
    }, tags=["boekhouding", "boeking"])
    body = (
        f"\n\n# Boeking {supplier}\n\n"
        f"- **Datum:** {datum or '—'}\n"
        f"- **Categorie:** {row.get('category') or '—'}\n"
        f"- **Grootboek:** {row.get('grootboek') or '—'}\n"
        f"- **Risico:** {row.get('risk_zone') or '—'}\n"
        f"- **Definitief:** {'ja' if row.get('definitief') else 'nee (concept)'}\n\n"
        + _bedrag_tabel(row.get("excl_cents"), row.get("btw_cents"), row.get("incl_cents"))
    )
    filename = f"{_slug(f'{datum} {supplier}', fallback='boeking')}.md"
    return filename, fm + body


def render_bank_txn(txn: BankTransaction) -> tuple[str, str]:
    """Render een banktransactie naar (bestandsnaam, markdown)."""
    richting = "bij" if txn.amount.cents >= 0 else "af"
    datum = txn.date.isoformat()
    fm = _frontmatter({
        "type": "banktransactie",
        "datum": datum,
        "tegenpartij": txn.counterparty,
        "iban": txn.counterparty_iban,
        "richting": richting,
        "bedrag": format_eur(txn.amount),
        "bron": txn.source,
    }, tags=["boekhouding", "bank"])
    body = (
        f"\n\n# {txn.counterparty or 'Banktransactie'} — {format_eur(txn.amount)}\n\n"
        f"- **Datum:** {datum}\n"
        f"- **Tegenpartij:** {txn.counterparty or '—'}\n"
        f"- **IBAN:** {txn.counterparty_iban or '—'}\n"
        f"- **Bedrag:** {format_eur(txn.amount)} ({richting})\n"
        f"- **Omschrijving:** {txn.description or '—'}\n"
        f"- **Bron:** {txn.source or '—'}\n"
    )
    ref = txn.txn_id or f"{datum}-{txn.counterparty}"
    filename = f"{_slug(f'{datum} {txn.counterparty} {ref}', fallback='bank')}.md"
    return filename, fm + body


def render_summary(totals: dict, *, company: str, counts: dict) -> str:
    """Render de index-/MOC-notitie met financieel overzicht en inhoudsopgave."""
    omzet = totals.get("omzet_cents") or 0
    kosten = totals.get("kosten_cents") or 0
    fm = _frontmatter({"type": "overzicht", "bedrijf": company},
                      tags=["boekhouding", "overzicht"])
    body = (
        f"\n\n# Boekhouding — {company}\n\n"
        "> Geëxporteerd vanuit AI Boekhouder. Cijfers zijn concept/indicatief en geen "
        "vervanging voor je boekhouder of fiscalist.\n\n"
        "## Financieel overzicht\n\n"
        "| | Bedrag |\n|---|---:|\n"
        f"| Omzet (excl. btw) | {_euro(omzet)} |\n"
        f"| Kosten (excl. btw) | {_euro(kosten)} |\n"
        f"| Resultaat (indicatief) | {_euro(omzet - kosten)} |\n"
        f"| Openstaand (debiteuren) | {_euro(totals.get('open_cents'))} |\n\n"
        "## Inhoud\n\n"
        f"- {counts.get('invoices', 0)} facturen — `Facturen/`\n"
        f"- {counts.get('bookings', 0)} boekingen — `Boekingen/`\n"
        f"- {counts.get('bank', 0)} banktransacties — `Bank/`\n"
    )
    return fm + body


class ObsidianVault:
    """Exporteer de boekhouding van een tenant als Markdown-notities naar een vault."""

    name = "obsidian"
    SUBFOLDERS = {"invoices": "Facturen", "bookings": "Boekingen", "bank": "Bank"}

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def enabled(self) -> bool:
        return bool(self.settings.obsidian_vault)

    @property
    def root(self) -> Path:
        return Path(self.settings.obsidian_vault).expanduser() / self.settings.obsidian_folder

    def _write(self, folder: Path, filename: str, content: str) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / filename
        path.write_text(content, encoding="utf-8")
        return path

    def export(self, store, tenant_id: str = "local") -> dict:
        """Schrijf facturen, boekingen, banktransacties en een index naar de vault."""
        if not self.enabled:
            return {
                "enabled": False, "written": 0,
                "message": "Geen Obsidian-vault ingesteld (zet BOEKHOUDER_OBSIDIAN_VAULT). "
                           "Er is niets geschreven.",
            }
        root = self.root
        counts = {"invoices": 0, "bookings": 0, "bank": 0}
        for row in store.list_invoices(tenant_id):
            fn, content = render_invoice(row)
            self._write(root / self.SUBFOLDERS["invoices"], fn, content)
            counts["invoices"] += 1
        for row in store.list_bookings(tenant_id):
            fn, content = render_booking(row)
            self._write(root / self.SUBFOLDERS["bookings"], fn, content)
            counts["bookings"] += 1
        for txn in store.get_bank_txns(tenant_id):
            fn, content = render_bank_txn(txn)
            self._write(root / self.SUBFOLDERS["bank"], fn, content)
            counts["bank"] += 1
        summary = render_summary(store.financial_totals(tenant_id),
                                 company=self.settings.company_name, counts=counts)
        self._write(root, "Boekhouding.md", summary)
        written = counts["invoices"] + counts["bookings"] + counts["bank"] + 1
        log.info("Obsidian-export: %s notities naar %s", written, root)
        return {
            "enabled": True, "written": written, "counts": counts, "path": str(root),
            "message": f"{written} notities geschreven naar {root}",
        }
