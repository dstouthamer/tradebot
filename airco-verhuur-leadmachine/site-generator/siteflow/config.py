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
