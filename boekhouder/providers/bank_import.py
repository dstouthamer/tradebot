"""Bank statement import — real, offline parsers for the three formats Dutch banks
actually export: CAMT.053 (SEPA XML), MT940 (SWIFT), and CSV (ING/Rabo/ABN style).

No PSD2/live connection and no API keys: you feed a downloaded export and get back
``BankTransaction`` objects for the Bank Matching agent. Amount sign convention:
negative = outgoing (af), positive = incoming (bij).
"""
from __future__ import annotations

import csv
import io
import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime

from boekhouder.domain.documents import BankTransaction
from boekhouder.domain.money import Money
from boekhouder.providers.base import BankImporter

log = logging.getLogger("boekhouder.bank")


def _localname(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _findtext(elem, *names: str) -> str | None:
    """Namespace-agnostic descendant text lookup by local tag name path/alternatives."""
    for name in names:
        for node in elem.iter():
            if _localname(node.tag) == name and node.text:
                return node.text.strip()
    return None


# --------------------------------------------------------------------------- #
#  CAMT.053
# --------------------------------------------------------------------------- #
def parse_camt053(content: str) -> list[BankTransaction]:
    root = ET.fromstring(content)
    txns: list[BankTransaction] = []
    entries = [n for n in root.iter() if _localname(n.tag) == "Ntry"]
    for ntry in entries:
        amt_node = next((n for n in ntry.iter() if _localname(n.tag) == "Amt"), None)
        if amt_node is None or not amt_node.text:
            continue
        amount = Money.euro(amt_node.text.replace(",", "."))
        cd = _findtext(ntry, "CdtDbtInd") or "DBIT"
        if cd.upper().startswith("D"):
            amount = Money(-abs(amount.cents))
        booking_date = _findtext(ntry, "BookgDt") or _findtext(ntry, "ValDt")
        d = _parse_iso_date(booking_date)
        # Counterparty lives in transaction details when present.
        dtls = next((n for n in ntry.iter() if _localname(n.tag) == "TxDtls"), ntry)
        counterparty = _findtext(dtls, "Nm") or ""
        iban = _findtext(dtls, "IBAN") or ""
        info = _findtext(dtls, "Ustrd", "AddtlNtryInf", "AddtlTxInf") or ""
        ref = _findtext(dtls, "EndToEndId", "AcctSvcrRef") or ""
        txns.append(BankTransaction(
            date=d, amount=amount, counterparty=counterparty, counterparty_iban=iban,
            description=info, reference=ref, source="camt053", txn_id=ref,
        ))
    return txns


def _parse_iso_date(value: str | None) -> date:
    if not value:
        return date.today()
    value = value.strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return date.today()


# --------------------------------------------------------------------------- #
#  MT940
# --------------------------------------------------------------------------- #
_MT940_61 = re.compile(
    r"^:61:(?P<valdt>\d{6})(?P<entdt>\d{4})?(?P<mark>R?[DC])(?P<fund>[A-Z])?"
    r"(?P<amount>[\d,]+)"
)


def parse_mt940(content: str) -> list[BankTransaction]:
    txns: list[BankTransaction] = []
    current: BankTransaction | None = None
    for raw in content.splitlines():
        line = raw.strip()
        m = _MT940_61.match(line)
        if m:
            if current:
                txns.append(current)
            val = m.group("valdt")
            try:
                d = datetime.strptime(val, "%y%m%d").date()
            except ValueError:
                d = date.today()
            amount = Money.euro(m.group("amount").replace(",", "."))
            mark = m.group("mark")
            if mark.endswith("D"):           # D / RD = debit
                amount = Money(-abs(amount.cents))
            current = BankTransaction(date=d, amount=amount, source="mt940")
            continue
        if line.startswith(":86:") and current is not None:
            current.description = (current.description + " " + line[4:]).strip()
            iban = re.search(r"\b([A-Z]{2}\d{2}[A-Z0-9]{10,30})\b", line)
            if iban:
                current.counterparty_iban = iban.group(1)
            name = re.search(r"/NAME/([^/]+)", line)
            if name:
                current.counterparty = name.group(1).strip()
    if current:
        txns.append(current)
    return txns


# --------------------------------------------------------------------------- #
#  CSV (generic NL bank export)
# --------------------------------------------------------------------------- #
_DATE_COLS = ("datum", "date", "boekingsdatum", "transactiedatum")
_AMOUNT_COLS = ("bedrag", "amount", "bedrag (eur)", "transactiebedrag")
_DESC_COLS = ("omschrijving", "mededelingen", "description", "naam / omschrijving", "mededeling")
_NAME_COLS = ("naam", "tegenrekening naam", "naam tegenpartij", "counterparty")
_IBAN_COLS = ("tegenrekening", "tegenrekening iban", "iban/bban", "counterparty_iban")
_DEBCRED_COLS = ("af bij", "af/bij", "debit/credit", "bij/af")


def _pick(header: list[str], options: tuple[str, ...]) -> int | None:
    low = [h.strip().lower() for h in header]
    for opt in options:
        if opt in low:
            return low.index(opt)
    for i, h in enumerate(low):           # fuzzy contains
        if any(opt in h for opt in options):
            return i
    return None


def parse_csv(content: str) -> list[BankTransaction]:
    sample = content[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
    except csv.Error:
        dialect = csv.excel
        dialect.delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    reader = csv.reader(io.StringIO(content), dialect)
    rows = [r for r in reader if r]
    if not rows:
        return []
    header = rows[0]
    di, ai = _pick(header, _DATE_COLS), _pick(header, _AMOUNT_COLS)
    desc_i, name_i = _pick(header, _DESC_COLS), _pick(header, _NAME_COLS)
    iban_i, dc_i = _pick(header, _IBAN_COLS), _pick(header, _DEBCRED_COLS)

    txns: list[BankTransaction] = []
    for row in rows[1:]:
        if ai is None or ai >= len(row):
            continue
        amount = _parse_csv_amount(row[ai])
        if dc_i is not None and dc_i < len(row):
            if row[dc_i].strip().lower() in ("af", "debit", "d", "-"):
                amount = Money(-abs(amount.cents))
            elif row[dc_i].strip().lower() in ("bij", "credit", "c", "+"):
                amount = Money(abs(amount.cents))
        txns.append(BankTransaction(
            date=_parse_csv_date(row[di]) if di is not None and di < len(row) else date.today(),
            amount=amount,
            counterparty=row[name_i] if name_i is not None and name_i < len(row) else "",
            counterparty_iban=row[iban_i] if iban_i is not None and iban_i < len(row) else "",
            description=row[desc_i] if desc_i is not None and desc_i < len(row) else "",
            source="csv",
        ))
    return txns


def _parse_csv_amount(token: str) -> Money:
    token = token.strip().replace("€", "").replace(" ", "")
    neg = token.startswith("-")
    token = token.lstrip("+-")
    # Normalise: if both separators present, the last one is the decimal sep.
    if "," in token and "." in token:
        if token.rfind(",") > token.rfind("."):
            token = token.replace(".", "").replace(",", ".")
        else:
            token = token.replace(",", "")
    elif "," in token:
        token = token.replace(".", "").replace(",", ".")
    try:
        m = Money.euro(token or "0")
    except Exception:  # noqa: BLE001
        m = Money(0)
    return Money(-m.cents) if neg else m


def _parse_csv_date(token: str) -> date:
    token = token.strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%Y%m%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return date.today()


class FileBankImporter(BankImporter):
    name = "file"

    def parse(self, content, *, fmt="auto") -> list[BankTransaction]:
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        fmt = (fmt or "auto").lower()
        head = content.lstrip()[:200].lower()
        if fmt == "camt053" or (fmt == "auto" and head.startswith("<")):
            return parse_camt053(content)
        if fmt == "mt940" or (fmt == "auto" and ":61:" in content):
            return parse_mt940(content)
        return parse_csv(content)
