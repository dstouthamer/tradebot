"""Laad config.yaml en vul placeholders zoals {region}, {noun} overal in."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

# Placeholders die in elke tekst van de config gebruikt mogen worden.
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


def _context(cfg: dict) -> dict[str, str]:
    b = cfg.get("business", {})
    p = cfg.get("product", {})
    ctx = {
        "name": b.get("name", ""),
        "region": b.get("region", ""),
        "phone": b.get("phone_display", ""),
        "email": b.get("email", ""),
        "noun": p.get("noun", ""),
        "noun_plural": p.get("noun_plural", ""),
        "verb": p.get("verb", ""),
        "verb_noun": p.get("verb_noun", ""),
        "price_from": p.get("price_from", ""),
        "price_unit": p.get("price_unit", ""),
    }
    return ctx


def _interp(value: Any, ctx: dict[str, str]) -> Any:
    """Vervang {key} door waarde uit ctx; onbekende keys blijven staan."""
    if isinstance(value, str):
        return _PLACEHOLDER.sub(lambda m: ctx.get(m.group(1), m.group(0)), value)
    if isinstance(value, list):
        return [_interp(v, ctx) for v in value]
    if isinstance(value, dict):
        return {k: _interp(v, ctx) for k, v in value.items()}
    return value


def load_config(path: str | Path) -> dict:
    """Lees en valideer de config, met placeholder-interpolatie."""
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not raw:
        raise ValueError(f"Lege of ongeldige config: {path}")

    ctx = _context(raw)
    # Twee passes: zodat placeholders die naar andere placeholders verwijzen ook werken.
    cfg = _interp(_interp(raw, ctx), ctx)

    for key in ("business", "product", "lead"):
        if key not in cfg:
            raise ValueError(f"Config mist verplicht blok: '{key}'")
    return cfg


# Verplichte velden per blok (gebruikt door de onboarding/validatie).
_REQUIRED = {
    "business": ["name", "domain", "phone_display", "phone_link", "whatsapp", "email", "region"],
    "product": ["noun", "verb", "price_from"],
    "lead": ["to_email"],
}

# Velden die nog op een placeholder mogen staan maar wél vóór livegang ingevuld
# moeten worden (de agent/koper moet hierop wijzen).
_PLACEHOLDER_HINTS = {
    "lead.web3forms_access_key": "PLAK-HIER",
    "business.domain": "jouwdomein",
    "business.email": "jouwdomein",
}


def validate_config(cfg: dict) -> list[str]:
    """Geef een lijst met problemen terug (leeg = compleet en klaar)."""
    problems: list[str] = []
    for block, fields in _REQUIRED.items():
        b = cfg.get(block, {})
        for f in fields:
            if not str(b.get(f, "")).strip():
                problems.append(f"Ontbreekt: {block}.{f}")

    for path, marker in _PLACEHOLDER_HINTS.items():
        block, field = path.split(".")
        if marker.lower() in str(cfg.get(block, {}).get(field, "")).lower():
            problems.append(f"Nog niet ingevuld (placeholder): {path}")

    if not cfg.get("cities"):
        problems.append("Geen lokale pagina's: voeg minstens 1 plaats toe onder 'cities'.")
    if not cfg.get("segments"):
        problems.append("Geen dienstpagina's: voeg minstens 1 item toe onder 'segments'.")
    return problems

