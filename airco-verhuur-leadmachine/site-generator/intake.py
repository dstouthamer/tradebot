#!/usr/bin/env python3
"""
Intake-vragenlijst (zonder AI-agent)
====================================

Stelt de koper dezelfde kernvragen als ONBOARDING.md en schrijft een werkende
config. Daarna kun je meteen genereren:

    python intake.py                 # schrijft config.<bedrijf>.yaml
    python generate.py config.<bedrijf>.yaml

Alles met een standaardwaarde [tussen haakjes] kun je leeg laten (Enter).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def ask(q: str, default: str = "", required: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    while True:
        ans = input(f"{q}{suffix}: ").strip()
        if not ans:
            ans = default
        if ans or not required:
            return ans
        print("  (dit veld is verplicht)")


def ask_int(q: str, default: int = 0) -> int:
    ans = ask(q, str(default))
    try:
        return int(re.sub(r"\D", "", ans) or 0)
    except ValueError:
        return default


def yes(q: str) -> bool:
    return ask(f"{q} (j/n)", "n").lower().startswith("j")


def slugify(name: str) -> str:
    s = name.lower()
    for a, b in [("á", "a"), ("é", "e"), ("ë", "e"), ("ï", "i"), ("ö", "o"), ("ü", "u")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def intl_phone(display: str) -> str:
    digits = re.sub(r"\D", "", display)
    if digits.startswith("0"):
        return "+31" + digits[1:]
    if digits.startswith("31"):
        return "+" + digits
    return "+" + digits if digits else ""


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    print("Welkom! Ik stel je een paar vragen en zet daarna je website-config klaar.\n"
          "Druk op Enter om een standaardwaarde te accepteren.")

    section("Bedrijf")
    name = ask("Bedrijfsnaam", required=True)
    domain = ask("Website-adres (domein)", "https://www.jouwdomein.nl")
    phone_display = ask("Telefoonnummer (zoals getoond)", required=True)
    phone_link = ask("Telefoon internationaal", intl_phone(phone_display))
    whatsapp = ask("WhatsApp-nummer (internationaal, zonder +)", "")
    email = ask("E-mail voor aanvragen", required=True)
    region = ask("Werkgebied/regio", required=True)
    address = ask("Bedrijfsadres (optioneel)", "")
    kvk = ask("KvK-nummer (optioneel)", "")
    has_reviews = yes("Heb je al reviews?")
    rating = ask("Gemiddelde reviewscore", "4,9") if has_reviews else ""
    reviews_count = ask_int("Aantal reviews", 50) if has_reviews else 0
    opening_hours = ask("Openingstijden", "Ma-vr 09:00 - 17:00")

    section("Product / dienst")
    noun = ask("Wat lever je? (enkelvoud, bv. 'mobiele airco')", required=True)
    noun_plural = ask("Meervoud", noun + "'s")
    verb = ask("Huren / kopen / laten installeren?", "huren")
    verb_noun = ask("Zelfstandig naamwoord (verhuur/verkoop/installatie)", "verhuur")
    what = ask("Kernvoordeel in 1 zin", "")
    pain = ask("Welk probleem los je op?", "")
    promise = ask("Wat beloof je de klant?", f"Wij regelen je {noun} van begin tot eind.")
    category = ask("Bedrijfscategorie (voor lokale SEO)", "")
    price_from = ask("Vanaf-prijs", required=True)
    price_unit = ask("Per wat?", "per week")

    section("Branding")
    primary = ask("Hoofdkleur (hex)", "#0b7285")
    accent = ask("Accentkleur (hex)", "#fab005")
    tagline = ask("Slogan", "Snel geregeld, zorgeloos geleverd.")
    seo_hook = ask("Korte SEO-haak voor titels", "Snel Geregeld")

    section("Doelgroepen (eigen pagina's)")
    segments = []
    while True:
        sname = ask("Naam doelgroep/segment (leeg = klaar)", "")
        if not sname:
            break
        sintro = ask(f"  Korte intro voor '{sname}'", f"{noun.capitalize()} {verb} voor {sname.lower()}.")
        bullets = [b for b in [
            ask("  Voordeel 1", ""), ask("  Voordeel 2", ""), ask("  Voordeel 3", "")
        ] if b]
        cta = ask("  Call-to-action", "Aanvraag starten")
        segments.append({"slug": slugify(sname), "name": sname,
                         "h1": f"{noun.capitalize()} {verb} voor {sname.lower()} in {{region}}",
                         "intro": sintro, "bullets": bullets, "cta": cta})
    if not segments:
        segments.append({"slug": "particulier", "name": "Particulier", "h1": f"{noun.capitalize()} {verb} in {{region}}",
                         "intro": promise, "bullets": [], "cta": "Aanvraag starten"})

    section("Pakketten / prijzen")
    packages = []
    while True:
        pname = ask("Pakketnaam (leeg = klaar)", "")
        if not pname:
            break
        packages.append({"name": pname, "audience": ask("  Voor wie", ""),
                         "contents": ask("  Inhoud", ""), "price": ask("  Prijs", "op aanvraag")})

    section("USP's (waarom bij jou?)")
    usps = []
    for i in range(4):
        t = ask(f"USP {i+1} titel (leeg = klaar)", "")
        if not t:
            break
        usps.append({"icon": ask("  Emoji", "✅"), "title": t, "text": ask("  Toelichting", "")})

    section("Veelgestelde vragen")
    faq = []
    while True:
        q = ask("Vraag (leeg = klaar)", "")
        if not q:
            break
        faq.append({"q": q, "a": ask("  Antwoord", "")})

    section("Werkgebied (lokale SEO — belangrijk voor vindbaarheid)")
    cities = []
    while True:
        cname = ask("Plaatsnaam (leeg = klaar)", "")
        if not cname:
            break
        neighbors = [n.strip() for n in ask("  Buurplaatsen (komma-gescheiden)", "").split(",") if n.strip()]
        cities.append({"name": cname, "slug": slugify(cname),
                       "neighborhoods": ask("  Wijken/omschrijving", "de hele plaats"),
                       "delivery_time": ask("  Typische levertijd", "enkele dagen"),
                       "neighbors": neighbors})
    if not cities:
        cities.append({"name": region, "slug": slugify(region), "neighborhoods": "de hele regio",
                       "delivery_time": "enkele dagen", "neighbors": []})

    section("Over ons")
    about = ask("Korte tekst over je bedrijf", f"{name} is jouw specialist in {noun} {verb} in {region}.")

    cfg = {
        "business": {"name": name, "domain": domain.rstrip("/"), "phone_display": phone_display,
                     "phone_link": phone_link, "whatsapp": whatsapp, "email": email, "region": region,
                     "address": address, "kvk": kvk, "rating": rating, "reviews_count": reviews_count,
                     "opening_hours": opening_hours},
        "brand": {"primary_color": primary, "accent_color": accent, "tagline": tagline},
        "product": {"noun": noun, "noun_plural": noun_plural, "verb": verb, "verb_noun": verb_noun,
                    "what_you_offer": what, "pain": pain, "promise": promise,
                    "business_category": category, "price_from": price_from, "price_unit": price_unit},
        "lead": {"to_email": email, "web3forms_access_key": "PLAK-HIER-JE-WEB3FORMS-KEY",
                 "thanks_message": "Gelukt! We nemen zo snel mogelijk contact met je op."},
        "copy": {"seo_hook": seo_hook, "local_hero_suffix": tagline.lower().rstrip("."),
                 "local_speed_line": "Vraag het vandaag aan in {city}; wij regelen het {delivery_time}."},
        "usps": usps, "segments": segments, "packages": packages,
        "steps": [
            {"title": "Aanvraag", "text": "Vertel ons wat je nodig hebt. Reactie binnen enkele minuten."},
            {"title": "Advies & offerte", "text": "Wij geven advies en een heldere prijs."},
            {"title": "Levering", "text": "Wij regelen het van begin tot eind."},
            {"title": "Klaar", "text": "Jij hoeft nergens omkijken naar te hebben."},
        ],
        "faq": faq, "reviews": [],
        "about": {"text": about}, "cities": cities,
    }

    out = ROOT / f"config.{slugify(name)}.yaml"
    out.write_text(yaml.dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"\n✅ Config opgeslagen: {out.name}")
    print(f"   Genereer je site:  python generate.py {out.name}")
    print("   Vergeet niet een gratis key te maken op https://web3forms.com voor het leadformulier.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nAfgebroken.")
        sys.exit(1)
