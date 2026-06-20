# Site-generator — jouw leadmachine in één bestand

Deze map bevat een **werkende generator**. Jij past één bestand aan
(`config.yaml`) en krijgt een complete website: alle pagina's, lokale
SEO-pagina's, leadformulier (aanvragen → jouw e-mail), WhatsApp/bel-knoppen,
SEO-meta en schema. Voor **WordPress** én als directe **browser-preview**.

> Wil je zo min mogelijk zelf doen? Geef je agent een opdracht uit
> [`AGENTS.md`](AGENTS.md) — die past de config aan, draait de generator en
> publiceert naar WordPress.

## Wat krijg je

| Bestand | Wat |
|---------|-----|
| `config.yaml` | **Het enige dat jij aanpast**: bedrijf, product, USP's, prijzen, steden, leads-e-mail |
| `build/wordpress-import.xml` | Kant-en-klaar WordPress-importbestand (alle pagina's) |
| `build/preview/home.html` | De hele site om direct in je browser te bekijken |
| `config.voorbeeld-zonnepanelen.yaml` | Bewijs dat dezelfde machine een ander product maakt |

## In 3 stappen live (WordPress)

**1. Genereren**
```bash
cd site-generator
pip install -r requirements.txt      # eenmalig
python generate.py                   # leest config.yaml
```
Bekijk eerst `build/preview/home.html` in je browser. Tevreden?

**2. Importeren in WordPress**
- WordPress-admin → **Tools → Import → WordPress** (installeer de importer als dat gevraagd wordt).
- Upload `build/wordpress-import.xml`. Klaar — alle pagina's staan erop, inclusief SEO-titels (Yoast én RankMath) en schema.

**3. Afronden (eenmalig, ~10 min)**
- **Menu**: Weergave → Menu's → zet Home, Diensten, Prijzen, Hoe werkt het, Werkgebied, Contact erin.
- **Formulier-e-mail**: maak een gratis key op <https://web3forms.com> en zet die bij `lead.web3forms_access_key` in `config.yaml`, genereer opnieuw en importeer (of pas de key aan in de formulier-pagina's). Aanvragen komen dan binnen op je e-mail — geen plugin of server nodig.
- **Permalinks**: Instellingen → Permalinks → "Berichtnaam" (mooie URL's).
- Voeg je logo, kleuren en foto's toe in je thema.

## Direct publiceren zonder importeren (voor agents)

In plaats van handmatig importeren kan een agent (of jij) rechtstreeks naar
WordPress publiceren via de REST API:

```bash
export WP_URL="https://www.jouwdomein.nl"
export WP_USER="jouw-wp-gebruiker"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx xxxx xxxx"   # WP > Profiel > Applicatiewachtwoorden
python wp_publish.py --dry-run     # toon wat er gebeurt
python wp_publish.py               # maak/­update alle pagina's
```
Bestaande pagina's (zelfde slug) worden bijgewerkt; nieuwe aangemaakt. Zo
houden je agents de site actueel.

## Een ander product verkopen

1. Kopieer `config.yaml` of pas het `product`-, `usps`-, `segments`-,
   `packages`-, `faq`-, `cities`- en `copy`-blok aan.
2. `python generate.py mijn-nieuwe-config.yaml`
3. Importeren/publiceren. Voorbeeld: `python generate.py config.voorbeeld-zonnepanelen.yaml`.

## Hoe het in elkaar zit

```
config.yaml ─► siteflow/config.py    (laden + {placeholders} invullen)
            ─► siteflow/pages.py      (alle pagina's opbouwen)
            ─► siteflow/components.py (formulier, CTA's, USP's, schema)
            ─► siteflow/wxr.py        (WordPress-importbestand)
            ─► siteflow/preview.py    (browser-preview)
generate.py   = draait dit alles            wp_publish.py = publiceert via REST API
```

De inhoudelijke strategie (SEO, sales, opvolging, Ads, CRM) staat in de
[bovenliggende map](../README.md). Deze generator zet de *website* uit die
strategie automatisch neer.

> `build/` wordt elke run opnieuw gegenereerd; je hoeft daar nooit handmatig
> iets te wijzigen.
