# 11 — WordPress Technische Specificatie
**Rol: WordPress-developer**

## 1. Doelen voor de techniek

Snel (<2,5s LCP), veilig, makkelijk te beheren, conversiegericht en SEO-proof. Geen opgeblazen pagebuilder-bende. Schaalbaar naar honderden lokale pagina's.

## 2. Hosting & infrastructuur

- **Hosting:** managed WordPress-hosting met PHP 8.2+, server-side caching, HTTP/2-3, NVMe SSD. Bv. een kwaliteits-NL-host of managed WP (Kinsta/SiteGround/Cloudways-niveau).
- **CDN:** Cloudflare (gratis tier volstaat vaak) — caching, security, snelheid.
- **SSL:** Let's Encrypt / via host, forceer HTTPS, HSTS.
- **Backups:** dagelijks automatisch, offsite, getest terugzetbaar (UpdraftPlus/host-backups).
- **Staging-omgeving** voor updates en tests vóór productie.
- **E-mail:** transactionele mail via SMTP-plugin + dienst (Brevo/Postmark/Mailgun) — voorkomt dat bevestigingsmails in spam belanden.

## 3. WordPress-stack

| Onderdeel | Keuze | Waarom |
|-----------|-------|--------|
| **Thema** | Lichtgewicht: GeneratePress / Kadence / Blocksy + child theme | Snel, flexibel, schone code |
| **Builder** | Block editor (Gutenberg) + thema-blocks, of Bricks/Kadence Blocks | Vermijd zware builders (Elementor bloat) waar het kan |
| **SEO** | RankMath of Yoast | Meta, schema, sitemaps, breadcrumbs |
| **Formulieren** | Fluent Forms / WPForms / Gravity Forms | Multi-step, conditioneel, CRM-koppeling |
| **Caching** | WP Rocket (of host-cache + LiteSpeed) | Pagecache, lazy-load, minify |
| **Afbeeldingen** | ShortPixel/Imagify + WebP/AVIF | Compressie, snelheid |
| **Security** | Wordfence/Solid Security + host-firewall | Bescherming |
| **WhatsApp** | Klik-naar-chat plugin of custom wa.me-knoppen | Sticky CTA |
| **Schema (extra)** | RankMath schema of custom | LocalBusiness/FAQ/Review |
| **Analytics** | GTM-container + GA4 | Tracking (zie 12) |
| **Lokale pagina's** | Custom Post Type "Locatie" + ACF, of herbruikbare template | Schaalbaar beheer |

## 4. Lokale pagina's technisch (schaalbaar)

Optie A — **Custom Post Type `locatie`** met ACF-velden (stad, intro, levertijd, buurplaatsen, FAQ) + één template (`single-locatie.php`). Voordeel: consistent, snel nieuwe stad toevoegen, centrale template-updates.
Optie B — Reguliere pagina's met een herbruikbaar block-pattern.
> Let op: ondanks templating moet de **content uniek** zijn (zie 05) — vul de unieke velden handmatig in. Template ≠ duplicate content, mits de tekst per stad echt verschilt.

Automatisch genereren van `LocalBusiness`-schema met `areaServed` per locatie via het template.

## 5. Performance (Core Web Vitals — ook rankingfactor)

- **Doelen:** LCP <2,5s · INP <200ms · CLS <0,1 · TTFB <0,8s.
- Pagecaching + objectcache (Redis indien beschikbaar).
- Afbeeldingen: WebP/AVIF, juiste afmetingen, `loading="lazy"`, expliciete width/height (voorkomt CLS).
- Critical CSS + uitgestelde JS, verwijder ongebruikte CSS/JS.
- Beperk plugins (elke plugin = gewicht/risico). Audit kwartaalsgewijs.
- Fonts: lokaal hosten, `font-display: swap`, beperk gewichten.
- Geen zware sliders/animaties boven de vouw.
- Test met PageSpeed Insights + WebPageTest, mobiel als norm.

## 6. Security & onderhoud

- Sterke wachtwoorden + 2FA op admin, login-URL beperken/raten, captcha op formulieren (onzichtbaar/hCaptcha — geen conversiefrictie).
- Beperk admingebruikers, least privilege.
- Auto-updates voor minor + bewaakte updates voor major (via staging).
- Wordfence/firewall, malware-scan, disable file-editing in wp-admin.
- AVG: cookiebanner (Complianz) met consent mode v2 voor tracking, privacy-/cookiebeleid, verwerkersovereenkomsten met tools.
- Maandelijks onderhoud: updates, backups testen, uptime-monitoring, broken-link-check, Core Web Vitals-check.

## 7. Tracking-implementatie (techniek; strategie in 12)

- **Google Tag Manager** container sitebreed.
- **GA4** via GTM, met events: `generate_lead` (formulier-submit), `click_to_call`, `click_whatsapp`, `view_pricing`, `start_form`.
- **Google Ads conversie-tags** + **enhanced conversions** (gehashte leadgegevens) via GTM.
- **Consent Mode v2** gekoppeld aan cookiebanner.
- **Server-side** events optioneel later (nauwkeuriger, ad-blocker-bestendig).
- Bedankpagina `/bedankt/` als conversie-trigger; klik-naar-bellen en wa.me-klikken als events.

## 8. Integraties (koppelingen)

```
WordPress-formulier (Fluent/WPForms)
   ├─► Webhook → Make/Zapier → CRM (zie 09)
   ├─► CRM-native integratie (HubSpot/Pipedrive plugin)
   ├─► E-mail (SMTP-dienst) → bevestiging (zie 08)
   ├─► WhatsApp API (Trengo/360dialog) → instant bericht
   └─► GTM dataLayer push → GA4 + Ads conversie
```

Belangrijk: formulier-inzending moet **synchroon** de lead naar CRM + notificatie naar sales pushen (geen vertraging — reactiesnelheid is alles).

## 9. Toegankelijkheid & UX-techniek

- Mobile-first responsive, tikdoelen ≥44px, leesbaar contrast.
- Sticky CTA-bar (mobiel) zonder content te overlappen.
- `tel:` en `wa.me`-links correct, `type="tel"`/`inputmode` op telefoonveld.
- Semantische HTML, alt-teksten, focus-states (toegankelijkheid + SEO).
- 404-pagina met CTA (zie 04).

## 10. Opleverchecklist (go-live)

- [ ] SSL + HTTPS-redirect + canonieke domeinversie.
- [ ] GA4 + GTM + Search Console + Ads-conversies live en getest (testlead gedaan).
- [ ] XML-sitemap ingediend, robots.txt correct, `/bedankt/` op noindex.
- [ ] Schema gevalideerd (Rich Results Test).
- [ ] Core Web Vitals groen op mobiel.
- [ ] Formulier → CRM → e-mail → WhatsApp → sales-notificatie end-to-end getest.
- [ ] Sticky bel/WhatsApp/aanvraag-knoppen werken op mobiel.
- [ ] Backups + staging + uptime-monitoring actief.
- [ ] Cookiebanner + consent mode + privacy/cookiebeleid live.
- [ ] NAP consistent met Google Business Profile.
- [ ] 404, alle interne links, alle CTA's getest.
