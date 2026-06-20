"""Bouw alle pagina's (home, diensten, prijzen, lokaal, ...) uit de config."""
from __future__ import annotations

import html
from dataclasses import dataclass, field

from . import components as c


@dataclass
class Page:
    pid: int
    slug: str
    title: str            # H1 / interne titel
    meta_title: str
    meta_description: str
    body: str             # HTML (zonder CSS/wrapper; die voegt de renderer toe)
    nav_label: str | None = None
    parent_slug: str = ""
    menu_order: int = 0
    schema: list = field(default_factory=list)


def _band(cfg: dict, label: str = "Klaar voor verkoeling?") -> str:
    return (
        f'<div class="lm-band"><h2 style="color:#fff;margin-top:0">{html.escape(label)}</h2>'
        f'<p>Doe in 1 minuut je aanvraag — wij reageren binnen enkele minuten.</p>'
        f'{c.cta_buttons(cfg, "Aanvraag starten")}</div>'
    )


def build_pages(cfg: dict) -> list[Page]:
    P = cfg["product"]
    B = cfg["business"]
    CO = cfg.get("copy", {})
    noun, verb, region = P["noun"], P["verb"], B["region"]
    # Product-onafhankelijke 'haakjes' (defaults passen bij verhuur; overschrijf in config.copy)
    seo_hook = CO.get("seo_hook", "Vandaag Geleverd")
    local_suffix = CO.get("local_hero_suffix", "vandaag geleverd")
    pages: list[Page] = []
    pid = 100

    def nxt() -> int:
        nonlocal pid
        pid += 1
        return pid

    # ---------- HOME ----------
    hero = (
        f'<div class="lm-hero"><h1>{noun.capitalize()} {verb} in {region} — {cfg["brand"]["tagline"].lower().rstrip(".")}</h1>'
        f'<p>{html.escape(P["pain"])} {html.escape(P["promise"])}</p>'
        f'{c.cta_buttons(cfg, "Bekijk beschikbaarheid")}{c.trust_row(cfg)}</div>'
    )
    seg_tiles = "".join(
        f'<a class="lm-card" style="text-decoration:none;color:inherit" href="/diensten/{s["slug"]}/">'
        f'<h3>{html.escape(s["name"])}</h3><p class="lm-muted">{html.escape(s["intro"][:90])}…</p></a>'
        for s in cfg.get("segments", [])
    )
    home_body = (
        hero
        + "<h2>Zo werkt het</h2>" + _steps_html(cfg)
        + "<h2>Voor wie?</h2>" + f'<div class="lm-grid">{seg_tiles}</div>'
        + f"<h2>Waarom {html.escape(B['name'])}?</h2>" + c.usp_grid(cfg)
        + c.reviews_block(cfg)
        + f'<h2>Prijzen</h2><p>Al een {noun} <strong>{P["price_from"]} {P["price_unit"]}</strong>, inclusief bezorging en installatie. <a href="/prijzen/">Bekijk alle tarieven ▸</a></p>'
        + _band(cfg)
    )
    pages.append(Page(nxt(), "home", f"{noun.capitalize()} {verb} {region}",
        f"{noun.capitalize()} {verb.capitalize()} {region} | {seo_hook} | {B['name']}",
        f"{noun.capitalize()} {verb} in {region}? ✓ Vandaag geleverd ✓ Installatie inbegrepen ✓ Per dag, week of maand. Vraag direct aan.",
        home_body, nav_label="Home", menu_order=0,
        schema=[c.local_business_schema(cfg)]))

    # ---------- PILLAR ----------
    pillar_body = (
        f'<h1>{noun.capitalize()} {verb}: alles wat je moet weten (en direct regelen)</h1>'
        f'<p>Een {noun} {verb} kost {P["price_from"]} {P["price_unit"]} en is meestal binnen 24 uur geleverd en geïnstalleerd. Ideaal voor {html.escape(P["what_you_offer"])}.</p>'
        + c.cta_buttons(cfg)
        + "<h2>Voor welke ruimtes?</h2>"
        + f'<div class="lm-grid">{seg_tiles}</div>'
        + "<h2>Hoe werkt het?</h2>" + _steps_html(cfg)
        + "<h2>Veelgestelde vragen</h2>" + c.faq_html(cfg.get("faq", []))
        + _band(cfg)
    )
    pages.append(Page(nxt(), _slug(f"{noun} {verb}"), f"{noun.capitalize()} {verb}",
        f"{noun.capitalize()} {verb.capitalize()} — Complete Gids & Direct Regelen | {B['name']}",
        f"Alles over {noun} {verb}: prijzen, capaciteit en levering. Vandaag besteld, vandaag koel. Vraag direct aan bij {B['name']}.",
        pillar_body, nav_label=None, menu_order=1,
        schema=[c.faq_schema(cfg.get("faq", []))]))

    # ---------- DIENSTEN-OVERZICHT ----------
    overview_body = (
        f"<h1>Onze diensten — {noun} {verb} voor elke situatie</h1>"
        + f'<div class="lm-grid">{seg_tiles}</div>' + _band(cfg)
    )
    diensten = Page(nxt(), "diensten", "Diensten",
        f"{noun.capitalize()} {verb.capitalize()} — Diensten | {B['name']}",
        f"Bekijk waarvoor je een {noun} kunt {verb} bij {B['name']}: thuis, kantoor, serverruimte en evenement.",
        overview_body, nav_label="Diensten", menu_order=2)
    pages.append(diensten)

    # ---------- SEGMENT-PAGINA'S ----------
    for i, s in enumerate(cfg.get("segments", [])):
        bullets = "".join(f"<li>{html.escape(b)}</li>" for b in s.get("bullets", []))
        body = (
            f'<div class="lm-hero"><h1>{html.escape(s["h1"])}</h1><p>{html.escape(s["intro"])}</p>'
            f'{c.cta_buttons(cfg, s.get("cta", "Aanvraag starten"))}</div>'
            f"<h2>Wat je krijgt</h2><ul>{bullets}</ul>"
            + c.usp_grid(cfg)
            + "<h2>Zo werkt het</h2>" + _steps_html(cfg)
            + c.reviews_block(cfg)
            + _band(cfg, s.get("cta", "Vraag direct aan"))
        )
        pages.append(Page(nxt(), s["slug"], s["name"],
            f"{s['name']} — {noun.capitalize()} {verb.capitalize()} {region} | {B['name']}",
            f"{html.escape(s['intro'][:150])}",
            body, parent_slug="diensten", menu_order=i,
            schema=[{"@context": "https://schema.org", "@type": "Service",
                     "serviceType": s["name"], "provider": {"@type": "LocalBusiness", "name": B["name"]},
                     "areaServed": region}]))

    # ---------- PRIJZEN ----------
    rows = "".join(
        f'<tr><td><strong>{html.escape(p["name"])}</strong></td><td>{html.escape(p["audience"])}</td>'
        f'<td>{html.escape(p["contents"])}</td><td>{html.escape(p["price"])}</td></tr>'
        for p in cfg.get("packages", [])
    )
    prijzen_body = (
        f"<h1>Wat kost een {noun} {verb}? — Transparante tarieven</h1>"
        f"<p>Bij {html.escape(B['name'])} weet je vooraf waar je aan toe bent. Prijzen zijn inclusief bezorging, installatie en ophalen binnen {region}. Geen verborgen kosten.</p>"
        f'<table class="lm-price"><tr><th>Pakket</th><th>Voor wie</th><th>Inhoud</th><th>Prijs</th></tr>{rows}</table>'
        f'<p class="lm-reassure">✓ Inclusief bezorging & installatie ✓ Korting bij langere huur ✓ Zakelijke factuur met btw</p>'
        + _band(cfg, "Bekijk beschikbaarheid voor jouw periode")
    )
    pages.append(Page(nxt(), "prijzen", "Prijzen",
        f"{noun.capitalize()} {verb.capitalize()} — Prijzen & Tarieven {region} | {B['name']}",
        f"Bekijk de tarieven voor {noun} {verb} in {region}. Vanaf {P['price_from']} {P['price_unit']} incl. bezorging & installatie.",
        prijzen_body, nav_label="Prijzen", menu_order=3))

    # ---------- HOE WERKT HET ----------
    pages.append(Page(nxt(), "hoe-werkt-het", "Hoe werkt het",
        f"Zo {verb.capitalize()} Je een {noun.capitalize()} | {B['name']}",
        f"In 4 simpele stappen een {noun} {verb} bij {B['name']}: aanvraag, advies, levering en ophalen.",
        f"<h1>Zo {verb} je een {noun} bij {html.escape(B['name'])}</h1>" + _steps_html(cfg) + _band(cfg),
        nav_label="Hoe werkt het", menu_order=4))

    # ---------- OVER ONS ----------
    pages.append(Page(nxt(), "over-ons", "Over ons",
        f"Over {B['name']} — Lokale Specialist in {noun.capitalize()} {P['verb_noun'].capitalize()}",
        f"Maak kennis met {B['name']}, jouw lokale specialist voor {noun} {verb} in {region}.",
        f"<h1>Over {html.escape(B['name'])}</h1><p>{html.escape(cfg.get('about', {}).get('text', ''))}</p>"
        + c.usp_grid(cfg) + _band(cfg),
        nav_label=None, menu_order=8))

    # ---------- FAQ ----------
    pages.append(Page(nxt(), "veelgestelde-vragen", "Veelgestelde vragen",
        f"Veelgestelde Vragen — {noun.capitalize()} {verb.capitalize()} | {B['name']}",
        f"Antwoorden op veelgestelde vragen over {noun} {verb}: levertijd, prijzen, installatie en meer.",
        f"<h1>Veelgestelde vragen</h1>" + c.faq_html(cfg.get("faq", [])) + _band(cfg),
        nav_label=None, menu_order=9,
        schema=[c.faq_schema(cfg.get("faq", []))]))

    # ---------- CONTACT ----------
    contact_body = (
        f"<h1>Neem contact op — wij reageren binnen 5 minuten</h1>"
        f'<p>📞 <a href="tel:{B["phone_link"]}">{html.escape(B["phone_display"])}</a> · '
        f'💬 <a href="{c.wa_link(cfg)}">WhatsApp</a> · ✉️ {html.escape(B["email"])}</p>'
        f'<p class="lm-muted">{html.escape(B.get("opening_hours",""))} · {html.escape(B.get("address",""))} · KvK {html.escape(str(B.get("kvk","")))}</p>'
        + c.lead_form(cfg, subject=f"Contactaanvraag {B['name']}")
    )
    pages.append(Page(nxt(), "contact", "Contact",
        f"Contact — {noun.capitalize()} {verb.capitalize()} {region} | {B['name']}",
        f"Contact met {B['name']} voor {noun} {verb} in {region}. Bel, app of vul het formulier in — reactie binnen 5 minuten.",
        contact_body, nav_label="Contact", menu_order=10,
        schema=[c.local_business_schema(cfg)]))

    # ---------- OFFERTE-LANDINGSPAGINA ----------
    landing_body = (
        f'<div class="lm-hero"><h1>{noun.capitalize()} {verb} in {region} — vraag direct aan</h1>'
        f'<p>{html.escape(P["promise"])} Reactie binnen 5 minuten.</p>{c.trust_row(cfg)}</div>'
        + '<div class="lm-grid"><div>' + c.lead_form(cfg, subject="Offerteaanvraag website")
        + "</div><div>" + c.usp_grid(cfg) + c.reviews_block(cfg) + "</div></div>"
    )
    pages.append(Page(nxt(), "offerte-aanvragen", "Offerte aanvragen",
        f"Offerte Aanvragen — {noun.capitalize()} {verb.capitalize()} {region} | {B['name']}",
        f"Vraag vrijblijvend een offerte aan voor {noun} {verb} in {region}. Reactie binnen 5 minuten.",
        landing_body, nav_label=None, menu_order=11))

    # ---------- BEDANKT ----------
    pages.append(Page(nxt(), "bedankt", "Bedankt",
        f"Bedankt voor je aanvraag | {B['name']}",
        "Bedankt voor je aanvraag. We nemen zo snel mogelijk contact op.",
        f'<div class="lm-hero"><h1>Gelukt! 🎉</h1><p>{html.escape(cfg["lead"].get("thanks_message",""))}</p></div>'
        f'<p>Met spoed nodig? Bel ons direct: <a class="lm-cta" href="tel:{B["phone_link"]}">📞 {html.escape(B["phone_display"])}</a> '
        f'of <a class="lm-cta wa" href="{c.wa_link(cfg)}">💬 WhatsApp</a></p>'
        f'<p class="lm-muted">Tip: stuur ons alvast een foto van je ruimte en de m², dan kunnen we sneller schakelen.</p>',
        nav_label=None, menu_order=12))

    # ---------- LOKALE PAGINA'S ----------
    hub_links = "".join(
        f'<a class="lm-card" style="text-decoration:none;color:inherit" href="/verhuur-in/{ci["slug"]}/"><h3>{html.escape(ci["name"])}</h3></a>'
        for ci in cfg.get("cities", [])
    )
    verhuur_hub = Page(nxt(), "verhuur-in", "Werkgebied",
        f"{noun.capitalize()} {verb.capitalize()} in {region} — Werkgebied | {B['name']}",
        f"In welke plaatsen leveren wij? Bekijk ons werkgebied voor {noun} {verb} in {region}.",
        f"<h1>{noun.capitalize()} {verb} in {region}</h1><p>Wij leveren in onderstaande plaatsen en omgeving:</p>"
        f'<div class="lm-grid">{hub_links}</div>' + _band(cfg),
        nav_label="Werkgebied", menu_order=5)
    pages.append(verhuur_hub)

    for ci in cfg.get("cities", []):
        nb_links = " · ".join(
            f'<a href="/verhuur-in/{_slug(n)}/">{html.escape(n)}</a>' for n in ci.get("neighbors", [])
        )
        local_faq = [
            {"q": f"Hoe snel leveren jullie in {ci['name']}?",
             "a": f"Meestal binnen {ci.get('delivery_time','enkele uren')}, vaak dezelfde dag bij bestelling vóór 15:00."},
            {"q": f"Installeren jullie de {noun} ook in {ci['name']}?",
             "a": "Ja, installatie en ophalen zijn inbegrepen."},
        ]
        body = (
            f'<div class="lm-hero"><h1>{noun.capitalize()} {verb} in {ci["name"]} — {local_suffix}</h1>'
            f'<p>Wij zijn actief in heel {ci["name"]} en omgeving — van {html.escape(ci.get("neighborhoods","de hele stad"))}. '
            f'Snel ter plaatse: doorgaans {ci.get("delivery_time","enkele uren")}.</p>{c.cta_buttons(cfg)}{c.trust_row(cfg)}</div>'
            f'<h2>Snel geregeld in {ci["name"]}</h2>'
            f'<p>{_local_speed_line(CO, ci)} '
            f'Wij verzorgen het van begin tot eind, zodat jij nergens omkijken naar hebt.</p>'
            f'<h2>Tarieven in {ci["name"]}</h2>'
            f'<p>{noun.capitalize()} {verb} in {ci["name"]} kan al vanaf {P["price_from"]} {P["price_unit"]}, inclusief bezorging en installatie. '
            f'<a href="/prijzen/">Bekijk alle tarieven ▸</a></p>'
            + (f'<h2>Ook rondom {ci["name"]}</h2><p>Wij leveren ook in: {nb_links}.</p>' if nb_links else "")
            + f"<h2>Veelgestelde vragen — {ci['name']}</h2>" + c.faq_html(local_faq)
            + _band(cfg, f"Koel je woning of bedrijf in {ci['name']} vandaag nog")
        )
        pages.append(Page(nxt(), ci["slug"], f"{noun.capitalize()} {verb} {ci['name']}",
            f"{noun.capitalize()} {verb.capitalize()} {ci['name']} | {seo_hook} | {B['name']}",
            f"{noun.capitalize()} {verb} in {ci['name']}? ✓ Vaak dezelfde dag geleverd ✓ Installatie inbegrepen ✓ Vanaf {P['price_from']} {P['price_unit']}.",
            body, parent_slug="verhuur-in",
            schema=[c.local_business_schema(cfg, area=ci["name"]), c.faq_schema(local_faq)]))

    # Zorg dat alle slugs URL-veilig zijn (ook bij spaties/accenten in config).
    for p in pages:
        p.slug = _slug(p.slug)
        if p.parent_slug:
            p.parent_slug = _slug(p.parent_slug)
    return pages


def _local_speed_line(copy_cfg: dict, city: dict) -> str:
    """Lokale 'snelheid'-zin; overschrijfbaar via config.copy.local_speed_line.
    Gebruik {city} en {delivery_time} als placeholders in de config."""
    default = "Bestel je vóór 15:00, dan zijn we vaak nog dezelfde dag in {city}."
    tpl = copy_cfg.get("local_speed_line", default)
    return html.escape(tpl.replace("{city}", city["name"]).replace(
        "{delivery_time}", city.get("delivery_time", "enkele uren")))


def _steps_html(cfg: dict) -> str:
    cards = ""
    for i, s in enumerate(cfg.get("steps", []), 1):
        cards += (f'<div class="lm-card"><div class="ic">{i}.</div>'
                  f'<h3>{html.escape(s["title"])}</h3><p>{html.escape(s["text"])}</p></div>')
    return f'<div class="lm-steps">{cards}</div>'


def _slug(name: str) -> str:
    import re
    s = name.lower()
    for a, b in [("á", "a"), ("é", "e"), ("ë", "e"), ("ï", "i"), ("ö", "o"), ("ü", "u")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
