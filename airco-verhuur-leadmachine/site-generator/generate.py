#!/usr/bin/env python3
"""
Leadmachine site-generator
==========================

Genereert uit ÉÉN config.yaml een complete website:
  - build/wordpress-import.xml   -> importeren in WordPress (Tools > Import)
  - build/preview/*.html         -> direct in je browser bekijken (geen WP nodig)

Gebruik:
    python generate.py                      # gebruikt config.yaml
    python generate.py andere-config.yaml   # ander product/bedrijf

Niets te configureren in de code: alles zit in config.yaml.
"""
from __future__ import annotations

import sys
from pathlib import Path

from siteflow import build_pages, build_preview, build_wxr, load_config

ROOT = Path(__file__).resolve().parent


def main(argv: list[str]) -> int:
    config_path = ROOT / (argv[1] if len(argv) > 1 else "config.yaml")
    if not config_path.exists():
        print(f"❌ Config niet gevonden: {config_path}")
        return 1

    print(f"📖 Config inlezen: {config_path.name}")
    cfg = load_config(config_path)

    pages = build_pages(cfg)
    print(f"🧱 {len(pages)} pagina's gebouwd "
          f"(incl. {len(cfg.get('cities', []))} lokale SEO-pagina's, "
          f"{len(cfg.get('segments', []))} dienstpagina's).")

    out = ROOT / "build"
    out.mkdir(exist_ok=True)

    wxr_path = out / "wordpress-import.xml"
    wxr_path.write_text(build_wxr(pages, cfg), encoding="utf-8")
    print(f"✅ WordPress-import: {wxr_path.relative_to(ROOT)}")

    preview_dir = out / "preview"
    build_preview(pages, cfg, preview_dir)
    print(f"✅ Preview-site:     {preview_dir.relative_to(ROOT)}/home.html")

    # Waarschuw als de formuliersleutel nog niet is ingevuld.
    if "PLAK-HIER" in cfg["lead"].get("web3forms_access_key", ""):
        print("⚠️  Let op: 'web3forms_access_key' in config.yaml staat nog op de "
              "placeholder. Maak een gratis key op https://web3forms.com zodat "
              "aanvragen naar je e-mail worden gestuurd.")

    print("\n🎉 Klaar. Open de preview in je browser of importeer de XML in WordPress.")
    print("   Zie README.md voor de exacte stappen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
