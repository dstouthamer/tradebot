"""Herbruikbare HTML-bouwstenen (CTA's, formulier, USP's, reviews, schema).

Alle gegenereerde pagina's gebruiken dezelfde bouwstenen, zodat de site
consistent is en de preview er hetzelfde uitziet als in WordPress.
"""
from __future__ import annotations

import html
import json
import urllib.parse


def css(cfg: dict) -> str:
    """Scoped CSS die in elke pagina én in de preview wordt meegeladen."""
    primary = cfg["brand"]["primary_color"]
    accent = cfg["brand"]["accent_color"]
    return f"""
<style>
.lm-wrap{{--p:{primary};--a:{accent};font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1d2433;line-height:1.6;max-width:1080px;margin:0 auto;padding:0 18px}}
.lm-wrap h1{{font-size:2rem;line-height:1.2;margin:.2em 0}}
.lm-wrap h2{{font-size:1.5rem;margin:1.6em 0 .4em}}
.lm-hero{{background:linear-gradient(135deg,var(--p),#0c4a52);color:#fff;border-radius:18px;padding:38px 30px;margin:18px 0}}
.lm-hero h1{{color:#fff}}
.lm-hero p{{font-size:1.15rem;opacity:.95}}
.lm-trust{{display:flex;flex-wrap:wrap;gap:14px;font-size:.95rem;margin-top:10px}}
.lm-cta{{display:inline-block;background:var(--a);color:#1d2433;font-weight:700;padding:14px 22px;border-radius:10px;text-decoration:none;margin:6px 8px 6px 0}}
.lm-cta.alt{{background:#fff;color:var(--p);border:2px solid var(--p)}}
.lm-cta.wa{{background:#25D366;color:#fff}}
.lm-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px;margin:18px 0}}
.lm-card{{background:#f6f8fa;border:1px solid #e6ebf0;border-radius:14px;padding:20px}}
.lm-card .ic{{font-size:1.8rem}}
.lm-steps{{counter-reset:s;display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:18px}}
.lm-steps .lm-card{{position:relative}}
.lm-form{{background:#f6f8fa;border:1px solid #e6ebf0;border-radius:14px;padding:22px;max-width:520px}}
.lm-form input,.lm-form select,.lm-form textarea{{width:100%;box-sizing:border-box;padding:12px;margin:7px 0;border:1px solid #cdd6df;border-radius:9px;font-size:1rem}}
.lm-form button{{width:100%;background:var(--a);color:#1d2433;font-weight:700;border:0;padding:15px;border-radius:10px;font-size:1.05rem;cursor:pointer}}
.lm-reassure{{font-size:.9rem;color:#4a5568;margin:8px 0 0}}
.lm-review{{background:#fff;border:1px solid #e6ebf0;border-radius:12px;padding:16px}}
.lm-stars{{color:#fab005}}
.lm-faq details{{border-bottom:1px solid #e6ebf0;padding:12px 0}}
.lm-faq summary{{font-weight:600;cursor:pointer}}
.lm-price{{width:100%;border-collapse:collapse}}
.lm-price th,.lm-price td{{text-align:left;padding:11px;border-bottom:1px solid #e6ebf0}}
.lm-band{{background:var(--p);color:#fff;border-radius:14px;padding:26px;text-align:center;margin:26px 0}}
.lm-band .lm-cta{{margin-top:8px}}
.lm-muted{{color:#5a6472}}
@media(max-width:640px){{.lm-wrap h1{{font-size:1.6rem}}}}
</style>
"""


def wa_link(cfg: dict, text: str | None = None) -> str:
    num = cfg["business"]["whatsapp"]
    msg = text or f"Hoi {cfg['business']['name']}, ik wil graag een {cfg['product']['noun']} {cfg['product']['verb']}."
    return f"https://wa.me/{num}?text=" + urllib.parse.quote(msg)


def cta_buttons(cfg: dict, primary_label: str = "Aanvraag in 1 minuut") -> str:
    tel = cfg["business"]["phone_link"]
    tel_disp = cfg["business"]["phone_display"]
    return (
        f'<p><a class="lm-cta" href="/offerte-aanvragen/">{html.escape(primary_label)} ▸</a>'
        f'<a class="lm-cta wa" href="{wa_link(cfg)}">💬 WhatsApp</a>'
        f'<a class="lm-cta alt" href="tel:{tel}">📞 {html.escape(tel_disp)}</a></p>'
    )


def trust_row(cfg: dict) -> str:
    b = cfg["business"]
    return (
        f'<div class="lm-trust"><span>⭐ {b["rating"]}/5 uit {b["reviews_count"]} reviews</span>'
        f'<span>⚡ Levering binnen 24 uur</span><span>🔧 Installatie inbegrepen</span>'
        f'<span>📅 Flexibele huurperiode</span></div>'
    )


def usp_grid(cfg: dict) -> str:
    cards = "".join(
        f'<div class="lm-card"><div class="ic">{u["icon"]}</div>'
        f'<h3>{html.escape(u["title"])}</h3><p>{html.escape(u["text"])}</p></div>'
        for u in cfg.get("usps", [])
    )
    return f'<div class="lm-grid">{cards}</div>'


def reviews_block(cfg: dict) -> str:
    items = ""
    for r in cfg.get("reviews", []):
        stars = "★" * int(r.get("stars", 5))
        items += (
            f'<div class="lm-review"><div class="lm-stars">{stars}</div>'
            f'<p>"{html.escape(r["text"])}"</p>'
            f'<p class="lm-muted">— {html.escape(r["name"])}, {html.escape(r["place"])}</p></div>'
        )
    return f'<h2>Wat klanten zeggen</h2><div class="lm-grid">{items}</div>'


def lead_form(cfg: dict, subject: str = "Nieuwe aanvraag via website") -> str:
    lead = cfg["lead"]
    key = lead.get("web3forms_access_key", "")
    redirect = cfg["business"]["domain"].rstrip("/") + "/bedankt/"
    segs = cfg.get("segments", [])
    options = "".join(f'<option>{html.escape(s["name"])}</option>' for s in segs) or "<option>Anders</option>"
    return f"""
<form class="lm-form" action="https://api.web3forms.com/submit" method="POST">
  <input type="hidden" name="access_key" value="{html.escape(key)}">
  <input type="hidden" name="subject" value="{html.escape(subject)}">
  <input type="hidden" name="from_name" value="{html.escape(cfg['business']['name'])} website">
  <input type="hidden" name="redirect" value="{html.escape(redirect)}">
  <input type="checkbox" name="botcheck" style="display:none" tabindex="-1" autocomplete="off">
  <input type="text" name="naam" placeholder="Je naam" required>
  <input type="tel" name="telefoon" placeholder="Telefoonnummer" inputmode="tel" required>
  <input type="text" name="plaats" placeholder="Plaats of postcode" required>
  <select name="wat_wil_je_koelen" required>
    <option value="" disabled selected>Wat wil je {html.escape(cfg['product']['verb'])}?</option>
    {options}
  </select>
  <select name="wanneer">
    <option value="" disabled selected>Vanaf wanneer?</option>
    <option>Vandaag / spoed</option><option>Deze week</option><option>Later / plannen</option>
  </select>
  <input type="email" name="email" placeholder="E-mail (optioneel)">
  <textarea name="bericht" rows="3" placeholder="Bericht (optioneel)"></textarea>
  <button type="submit">Verstuur — wij bellen je zo terug ▸</button>
  <p class="lm-reassure">✓ Vrijblijvend ✓ Gratis advies ✓ Reactie binnen 5 minuten</p>
</form>
"""


# ---------- JSON-LD schema ----------

def local_business_schema(cfg: dict, area: str | None = None) -> dict:
    b = cfg["business"]
    data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": b["name"],
        "url": b["domain"],
        "telephone": b["phone_link"],
        "email": b["email"],
        "address": {"@type": "PostalAddress", "addressLocality": b.get("region", ""), "streetAddress": b.get("address", "")},
        "areaServed": area or b.get("region", ""),
        "description": f'{cfg["product"]["noun"].capitalize()} {cfg["product"]["verb"]} in {area or b.get("region","")}.',
    }
    if b.get("rating") and b.get("reviews_count"):
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(b["rating"]).replace(",", "."),
            "reviewCount": str(b["reviews_count"]),
        }
    return data


def faq_schema(faq: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in faq
        ],
    }


def schema_script(*objs: dict) -> str:
    out = ""
    for o in objs:
        if o:
            out += f'<script type="application/ld+json">{json.dumps(o, ensure_ascii=False)}</script>'
    return out


def faq_html(faq: list[dict]) -> str:
    items = "".join(
        f"<details><summary>{html.escape(f['q'])}</summary><p>{html.escape(f['a'])}</p></details>"
        for f in faq
    )
    return f'<div class="lm-faq">{items}</div>'
