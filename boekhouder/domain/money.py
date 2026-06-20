"""Cent-precise money and btw arithmetic.

Floating point is unacceptable for accounting, so amounts are stored as integer
cents and all rounding uses banker-free ROUND_HALF_UP (the convention NL invoices
expect). Helpers split inclusive/exclusive amounts for any ``BtwTarief``.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from boekhouder.domain.enums import BtwTarief

_CENT = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class Money:
    """An amount in euro cents. Immutable; arithmetic returns new instances."""

    cents: int

    @classmethod
    def euro(cls, amount: float | int | str | Decimal) -> "Money":
        d = _round(Decimal(str(amount)))
        return cls(int(d * 100))

    @property
    def amount(self) -> Decimal:
        return (Decimal(self.cents) / 100).quantize(_CENT)

    def __add__(self, other: "Money") -> "Money":
        return Money(self.cents + other.cents)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.cents - other.cents)

    def __mul__(self, factor: float | int | Decimal) -> "Money":
        return Money.euro(self.amount * Decimal(str(factor)))

    def __str__(self) -> str:
        return format_eur(self)


def format_eur(m: Money) -> str:
    """Dutch formatting, e.g. ``€2.238,50`` — dot thousands, comma decimals."""
    sign = "-" if m.cents < 0 else ""
    whole, frac = divmod(abs(m.cents), 100)
    groups = f"{whole:,}".replace(",", ".")
    return f"{sign}€{groups},{frac:02d}"


@dataclass(frozen=True, slots=True)
class BtwSplit:
    excl: Money
    btw: Money
    incl: Money
    tarief: BtwTarief


def btw_from_excl(excl: Money, tarief: BtwTarief) -> BtwSplit:
    btw = Money.euro(excl.amount * Decimal(str(tarief.rate)))
    return BtwSplit(excl=excl, btw=btw, incl=excl + btw, tarief=tarief)


def btw_from_incl(incl: Money, tarief: BtwTarief) -> BtwSplit:
    rate = Decimal(str(tarief.rate))
    excl = Money.euro(incl.amount / (Decimal(1) + rate)) if rate else incl
    btw = incl - excl
    return BtwSplit(excl=excl, btw=btw, incl=incl, tarief=tarief)


def split_incl(incl_amount: float | str, tarief: BtwTarief) -> BtwSplit:
    """Convenience: split an inclusive euro amount into excl/btw/incl."""
    return btw_from_incl(Money.euro(incl_amount), tarief)
