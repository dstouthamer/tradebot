"""Bouw een standalone HTML-preview zodat je de site direct in je browser ziet
(zonder WordPress). Handig om snel te beoordelen vóór je importeert."""
from __future__ import annotations

import html
from pathlib import Path

from .components import css, cta_buttons, schema_script, wa_link
from .pages import Page


def _nav(pages: list[Page], cfg: dict) -> str:
    links = ""
    for p in pages:
        if p.nav_label:
            links += f'<a href="./{p.slug}.html">{html.escape(p.nav_label)}</a>'
    return (
        f'<header class="lm-nav"><a class="brand" href="./home.html">{html.escape(cfg["business"]["name"])}</a>'
        f'<nav>{links}</nav>'
        f'<a class="lm-cta" href="./offerte-aanvragen.html">Aanvraag ▸</a></header>'
    )


def _sticky(cfg: dict) -> str:
    b = cfg["business"]
    return (
        f'<div class="lm-sticky">'
        f'<a href="tel:{b["phone_link"]}">📞 Bellen</a>'
        f'<a href="{wa_link(cfg)}">💬 WhatsApp</a>'
        f'<a href="./offerte-aanvragen.html">📝 Aanvraag</a></div>'
    )


def _footer(cfg: dict) -> str:
    b = cfg["business"]
    return (
        f'<footer class="lm-footer"><strong>{html.escape(b["name"])}</strong><br>'
        f'{html.escape(b.get("address",""))} · {html.escape(b["phone_display"])} · {html.escape(b["email"])}<br>'
        f'{html.escape(b.get("opening_hours",""))} · KvK {html.escape(str(b.get("kvk","")))}'
        f'<p class="lm-muted">Preview — gegenereerd door de leadmachine-generator. '
        f'Dit is een voorbeeld van hoe de WordPress-site eruitziet.</p></footer>'
    )


_SHELL_CSS = """
<style>
body{margin:0;background:#fff;padding-bottom:70px}
.lm-nav{display:flex;align-items:center;gap:18px;padding:12px 20px;border-bottom:1px solid #e6ebf0;position:sticky;top:0;background:#fff;z-index:10;flex-wrap:wrap}
.lm-nav .brand{font-weight:800;font-size:1.2rem;color:#0b7285;text-decoration:none;margin-right:auto}
.lm-nav nav a{margin:0 9px;color:#1d2433;text-decoration:none;font-size:.95rem}
.lm-footer{max-width:1080px;margin:40px auto 0;padding:24px 18px;border-top:1px solid #e6ebf0;color:#4a5568;font-size:.9rem}
.lm-sticky{display:none;position:fixed;bottom:0;left:0;right:0;background:#0b7285;z-index:20}
.lm-sticky a{flex:1;text-align:center;color:#fff;padding:14px 0;text-decoration:none;font-weight:600;border-right:1px solid rgba(255,255,255,.2)}
@media(max-width:760px){.lm-sticky{display:flex}.lm-nav nav{display:none}}
</style>
"""


def build_preview(pages: list[Page], cfg: dict, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Verwijder oude HTML zodat er geen pagina's van een vorige run blijven staan.
    for old in out_dir.glob("*.html"):
        old.unlink()
    css_block = css(cfg)
    nav = _nav(pages, cfg)
    sticky = _sticky(cfg)
    footer = _footer(cfg)
    for p in pages:
        schema = schema_script(*p.schema) if p.schema else ""
        # In de preview verwijzen interne /slug/-links naar ./slug.html
        body = _localize_links(p.body, pages)
        doc = f"""<!doctype html><html lang="nl"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(p.meta_title)}</title>
<meta name="description" content="{html.escape(p.meta_description)}">
{_SHELL_CSS}{css_block}{schema}</head><body>
{nav}
<main class="lm-wrap">{body}</main>
{footer}{sticky}
</body></html>"""
        (out_dir / f"{p.slug}.html").write_text(doc, encoding="utf-8")
    # index -> home
    (out_dir / "index.html").write_text(
        '<!doctype html><meta charset="utf-8">'
        '<meta http-equiv="refresh" content="0; url=./home.html">'
        '<a href="./home.html">Naar de homepage</a>', encoding="utf-8")


def _localize_links(body: str, pages: list[Page]) -> str:
    slugs = {p.slug for p in pages}
    import re

    def repl(m: re.Match) -> str:
        path = m.group(1).strip("/")
        last = path.split("/")[-1] if path else "home"
        if last in slugs:
            return f'href="./{last}.html"'
        return m.group(0)

    return re.sub(r'href="(/[^"]*)"', repl, body)
