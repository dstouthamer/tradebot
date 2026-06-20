"""Auth-endpoints: registratie, inloggen, login-methoden en OAuth-callbacks.

E-mail+wachtwoord werkt direct. Google/Microsoft worden actief zodra de client
id/secret in de config staan; iDIN zodra een broker-contract is geconfigureerd.
"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from boekhouder.auth import providers
from boekhouder.auth.service import AuthError, AuthService, Session
from boekhouder.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _service() -> AuthService:
    return AuthService()


def current_session(authorization: str = Header(default="")) -> Session:
    """Dependency: resolve the Bearer token to a Session, or 401."""
    token = authorization[7:] if authorization.lower().startswith("bearer ") else authorization
    session = _service().resolve(token) if token else None
    if session is None:
        raise HTTPException(401, "Niet ingelogd of token verlopen.")
    return session


class RegisterRequest(BaseModel):
    email: str
    password: str
    company_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.get("/methods")
async def methods():
    from dataclasses import asdict

    return [asdict(m) for m in providers.available_methods()]


@router.post("/register")
async def register(req: RegisterRequest):
    try:
        s = _service().register(req.email, req.password, req.company_name)
    except AuthError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"token": s.token, "tenant_id": s.tenant_id, "email": s.email}


@router.post("/login")
async def login(req: LoginRequest):
    try:
        s = _service().login(req.email, req.password)
    except AuthError as exc:
        raise HTTPException(401, str(exc)) from exc
    return {"token": s.token, "tenant_id": s.tenant_id, "email": s.email}


@router.get("/me")
async def me(session: Session = Depends(current_session)):
    return {"email": session.email, "tenant_id": session.tenant_id, "user_id": session.user_id}


# ---- OAuth (Google / Microsoft) — actief zodra keys gezet zijn ----------
@router.get("/{provider}/login")
async def oauth_login(provider: str):
    state = secrets.token_urlsafe(16)
    url = (providers.google_authorize_url(state) if provider == "google"
           else providers.microsoft_authorize_url(state) if provider == "microsoft"
           else None)
    if not url:
        raise HTTPException(400, f"Login via {provider} is niet geconfigureerd.")
    return RedirectResponse(url)


@router.get("/{provider}/callback")
async def oauth_callback(provider: str, code: str = "", state: str = ""):
    from urllib.parse import quote

    email = await _exchange_oauth(provider, code)
    if not email:
        raise HTTPException(400, f"OAuth via {provider} mislukt of niet geconfigureerd.")
    s = _service().login_or_create_external(email, provider=provider)
    # Stuur terug naar de web-app, die de token uit de query oppakt.
    return RedirectResponse(f"/?token={quote(s.token)}&email={quote(s.email)}")


async def _exchange_oauth(provider: str, code: str) -> str | None:
    """Wissel de OAuth-code in voor een geverifieerd e-mailadres."""
    s = get_settings()
    import httpx

    try:
        if provider == "google" and s.has_google_oauth and code:
            async with httpx.AsyncClient(timeout=20) as c:
                tok = (await c.post("https://oauth2.googleapis.com/token", data={
                    "code": code, "client_id": s.google_client_id,
                    "client_secret": s.google_client_secret,
                    "redirect_uri": f"{s.oauth_redirect_base}/auth/google/callback",
                    "grant_type": "authorization_code"})).json()
                info = (await c.get("https://www.googleapis.com/oauth2/v3/userinfo",
                        headers={"Authorization": f"Bearer {tok.get('access_token','')}"})).json()
                return info.get("email")
        if provider == "microsoft" and s.has_microsoft_oauth and code:
            async with httpx.AsyncClient(timeout=20) as c:
                tok = (await c.post(
                    "https://login.microsoftonline.com/common/oauth2/v2.0/token", data={
                        "code": code, "client_id": s.microsoft_client_id,
                        "client_secret": s.microsoft_client_secret,
                        "redirect_uri": f"{s.oauth_redirect_base}/auth/microsoft/callback",
                        "grant_type": "authorization_code"})).json()
                info = (await c.get("https://graph.microsoft.com/oidc/userinfo",
                        headers={"Authorization": f"Bearer {tok.get('access_token','')}"})).json()
                return info.get("email") or info.get("preferred_username")
    except Exception:  # noqa: BLE001 - degrade to a clean error
        return None
    return None
