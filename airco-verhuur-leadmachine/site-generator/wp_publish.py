#!/usr/bin/env python3
"""
Publiceer direct naar WordPress via de REST API
===============================================

Hiermee kan een agent (of jijzelf) de gegenereerde pagina's rechtstreeks
naar je WordPress-site zetten of bijwerken — zonder handmatig importeren.
Bestaande pagina's met dezelfde slug worden bijgewerkt, nieuwe aangemaakt.

Eenmalig instellen in WordPress:
  Gebruikers > Profiel > Applicatiewachtwoorden -> maak er een aan.

Zet daarna deze omgevingsvariabelen (of gebruik een .env):
  WP_URL=https://www.jouwdomein.nl
  WP_USER=jouw-wp-gebruikersnaam
  WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

Gebruik:
  python wp_publish.py            # publiceert alles uit config.yaml
  python wp_publish.py --dry-run  # toont alleen wat er zou gebeuren
  python wp_publish.py andere-config.yaml
"""
from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from siteflow import build_pages, load_config
from siteflow.components import css, schema_script

ROOT = Path(__file__).resolve().parent


def _auth_header() -> str:
    user = os.environ.get("WP_USER")
    pw = os.environ.get("WP_APP_PASSWORD")
    if not user or not pw:
        sys.exit("❌ Zet WP_USER en WP_APP_PASSWORD (applicatiewachtwoord) in je omgeving.")
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return f"Basic {token}"


def _api(base: str, path: str, method: str = "GET", data: dict | None = None) -> dict | list:
    url = f"{base}/wp-json/wp/v2{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", _auth_header())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ WordPress API-fout {e.code} bij {method} {path}: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        sys.exit(f"❌ Kan WordPress niet bereiken op {url}: {e.reason}")


def _find_page_id(base: str, slug: str) -> int | None:
    res = _api(base, f"/pages?slug={slug}&status=publish,draft&per_page=1")
    return res[0]["id"] if isinstance(res, list) and res else None


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    args = [a for a in argv[1:] if not a.startswith("--")]
    config_path = ROOT / (args[0] if args else "config.yaml")

    cfg = load_config(config_path)
    base = os.environ.get("WP_URL", cfg["business"]["domain"]).rstrip("/")
    pages = build_pages(cfg)
    css_block = css(cfg)

    print(f"🌐 Doel: {base}  ({len(pages)} pagina's){'  [DRY-RUN]' if dry else ''}")

    # Eerst id's van bestaande pagina's ophalen om parents te kunnen koppelen.
    slug_to_remote_id: dict[str, int] = {}
    for p in pages:
        if not dry:
            existing = _find_page_id(base, p.slug)
            if existing:
                slug_to_remote_id[p.slug] = existing

    created = updated = 0
    for p in pages:
        schema = schema_script(*p.schema) if p.schema else ""
        content = f'<div class="lm-wrap">{css_block}{schema}{p.body}</div>'
        payload = {
            "title": p.title,
            "slug": p.slug,
            "content": content,
            "excerpt": p.meta_description,
            "status": "publish",
            "menu_order": p.menu_order,
        }
        parent_id = slug_to_remote_id.get(p.parent_slug)
        if parent_id:
            payload["parent"] = parent_id

        if dry:
            print(f"   • zou publiceren: /{p.slug}/  ({p.title})")
            continue

        existing = slug_to_remote_id.get(p.slug) or _find_page_id(base, p.slug)
        if existing:
            _api(base, f"/pages/{existing}", "POST", payload)
            slug_to_remote_id[p.slug] = existing
            updated += 1
            print(f"   ✏️  bijgewerkt: /{p.slug}/")
        else:
            res = _api(base, "/pages", "POST", payload)
            slug_to_remote_id[p.slug] = res["id"]
            created += 1
            print(f"   ➕ aangemaakt: /{p.slug}/")

    if not dry:
        print(f"\n✅ Klaar: {created} aangemaakt, {updated} bijgewerkt.")
        print("   Tip: stel in WordPress nog het hoofdmenu samen (zie README, stap 'Menu').")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
