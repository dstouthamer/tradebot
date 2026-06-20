"""Decision thresholds — the masterprompt's numeric rules in one auditable place.

Borrowed shape from ``apex/config.py``'s explicit-limits philosophy: thresholds live
as named constants/functions so they can be reviewed and tested, not scattered.
"""
from __future__ import annotations

from boekhouder.domain.enums import RiskZone

# ---- Bank Matching confidence bands (masterprompt agent C) ----------------
# 95-100% auto-suggest · 80-94% confirm · 50-79% controlelijst · <50% ask.
MATCH_AUTO = 95
MATCH_CONFIRM = 80
MATCH_CONTROLELIJST = 50


def match_action(confidence: int) -> str:
    if confidence >= MATCH_AUTO:
        return "boeken"           # propose as match automatically
    if confidence >= MATCH_CONFIRM:
        return "bevestigen"       # propose, let user confirm
    if confidence >= MATCH_CONTROLELIJST:
        return "controleren"      # park on the controlelijst
    return "afwijzen"             # do not link, ask for info


def match_zone(confidence: int) -> RiskZone:
    if confidence >= MATCH_CONFIRM:
        return RiskZone.GROEN
    if confidence >= MATCH_CONTROLELIJST:
        return RiskZone.ORANJE
    return RiskZone.ROOD


# ---- Date tolerance for matching a payment to a document ------------------
MATCH_DATE_WINDOW_DAYS = 7
