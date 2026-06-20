"""Authenticatie & multi-tenant toegang.

Echte werkende login met e-mail + wachtwoord (gratis, geen externe afhankelijkheid).
OAuth (Google/Microsoft) en iDIN (banklogin) zitten als kant-en-klare 'stekkers' in
``providers`` — ze worden actief zodra de bijbehorende sleutels in de config staan.
Elk bedrijf is een tenant; alle administratiedata is per tenant afgeschermd.
"""
