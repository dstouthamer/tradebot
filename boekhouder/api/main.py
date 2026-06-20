"""AI Boekhouder REST API (pattern from apex/api/main.py).

Multi-tenant: de administratie-endpoints vereisen een Bearer-token (zie /auth). Elke
gebruiker werkt strikt binnen de eigen tenant. Alles blijft concept-only en
bevestiging-gated.

Run:  uvicorn boekhouder.api.main:app --reload
Docs: http://localhost:8000/docs
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

_WEB_DIR = Path(__file__).resolve().parent.parent / "web"

from boekhouder.api.auth_api import current_session
from boekhouder.api.auth_api import router as auth_router
from boekhouder.auth.service import Session
from boekhouder.config import get_settings
from boekhouder.engine.router import Router
from boekhouder.store import LOCAL_TENANT, get_store

app = FastAPI(
    title="AI Boekhouder API",
    version="0.3.0-mvp",
    description="Nederlandse AI-boekhoud-, CFO- en fiscale optimalisatie-agent. "
                "Multi-tenant, concept-only en bevestiging-gated by design.",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)

_router: Router | None = None


def router() -> Router:
    global _router
    if _router is None:
        _router = Router()
    return _router


class BerichtRequest(BaseModel):
    message: str
    session_id: str = "default"


@app.get("/", response_class=HTMLResponse)
async def home():
    """De web-app: inloggen/registreren + chat, prognoses en bevestigen in de browser."""
    index = _WEB_DIR / "index.html"
    # no-store: browser toont altijd de nieuwste versie na een update (geen oude cache).
    no_cache = {"Cache-Control": "no-store, must-revalidate"}
    if index.exists():
        return HTMLResponse(index.read_text(encoding="utf-8"), headers=no_cache)
    return HTMLResponse("<h1>AI Boekhouder</h1><p>Web-UI ontbreekt; gebruik /docs.</p>",
                        headers=no_cache)


@app.get("/health")
async def health():
    return {"status": "ok", "version": app.version}


@app.get("/config")
async def config():
    s = get_settings()
    return {
        "version": app.version,
        "require_confirmation": s.require_confirmation,
        "allow_auto_send": s.allow_auto_send,
        "allow_signup": s.allow_signup,
        "integrations": {
            "telegram": s.has_telegram, "whatsapp": s.has_whatsapp,
            "moneybird": s.has_moneybird, "email_inbox": s.has_email, "llm": s.has_llm,
            "ocr": s.ocr_provider, "google_login": s.has_google_oauth,
            "microsoft_login": s.has_microsoft_oauth, "idin_login": s.has_idin,
        },
    }


@app.post("/bericht")
async def bericht(req: BerichtRequest, session: Session = Depends(current_session)):
    reply = router().handle(req.message, session_id=req.session_id, tenant_id=session.tenant_id)
    return {
        "text": reply.text, "agent": reply.agent, "risk_zone": reply.risk_zone.value,
        "requires_confirmation": reply.requires_confirmation, "blocked": reply.blocked,
    }


@app.post("/upload")
async def upload(file: UploadFile, session_id: str = "default", supplier: str = "",
                 project: str = "", kind: str = "auto",
                 session: Session = Depends(current_session)):
    """Upload een bon (afbeelding/pdf) of een bankexport.

    ``kind``: 'bon' | 'bank' | 'auto'. Bij 'auto' raden we op de bestandsnaam én de
    inhoud, zodat een bankbestand niet per ongeluk als bonnetje wordt behandeld.
    """
    content = await file.read()
    name = (file.filename or "").lower()
    text = content.decode("utf-8", errors="replace")
    looks_bank = (name.endswith((".xml", ".mt940", ".sta", ".csv", ".940"))
                  or text.lstrip()[:200].lower().startswith("<")
                  or ":61:" in text[:4000])
    if kind == "bank" or (kind == "auto" and looks_bank):
        reply = router().handle("importeer bankafschrift", session_id=session_id,
                                tenant_id=session.tenant_id, file_content=text)
    else:
        msg = f"bonnetje {supplier} project {project}".strip()
        reply = router().handle(msg, session_id=session_id, tenant_id=session.tenant_id,
                                image_bytes=content)
    return {"text": reply.text, "agent": reply.agent, "risk_zone": reply.risk_zone.value,
            "requires_confirmation": reply.requires_confirmation}


class ProfileRequest(BaseModel):
    name: str | None = None
    legal_form: str | None = None
    kvk: str | None = None
    btw_id: str | None = None
    iban: str | None = None
    sector: str | None = None
    vat_period: str | None = None
    payment_term_days: int | None = None
    quote_validity_days: int | None = None
    accountant_contact: str | None = None


@app.get("/profile")
async def get_profile(session: Session = Depends(current_session)):
    return get_store().get_tenant(session.tenant_id) or {}


@app.put("/profile")
async def put_profile(req: ProfileRequest, session: Session = Depends(current_session)):
    store = get_store()
    profile = store.get_tenant(session.tenant_id) or {}
    profile.update({k: v for k, v in req.model_dump().items() if v is not None})
    store.update_tenant(session.tenant_id, profile)
    router().invalidate_profile(session.tenant_id)   # nieuwe gegevens meteen actief
    return {"ok": True, "profile": profile}


@app.get("/banktransacties")
async def banktransacties(session: Session = Depends(current_session)):
    from boekhouder.domain.money import format_eur

    return [{"datum": t.date.isoformat(), "bedrag": format_eur(t.amount),
             "cents": t.amount.cents, "tegenpartij": t.counterparty,
             "omschrijving": t.description, "bron": t.source}
            for t in get_store().get_bank_txns(session.tenant_id)]


@app.get("/facturen")
async def facturen(session: Session = Depends(current_session)):
    return get_store().list_invoices(session.tenant_id)


@app.get("/boekingen")
async def boekingen(session: Session = Depends(current_session)):
    return get_store().list_bookings(session.tenant_id)


@app.post("/approve")
async def approve(session_id: str = "default", session: Session = Depends(current_session)):
    return router().gate.confirm(session_id, tenant_id=session.tenant_id)


@app.get("/controlelijst")
async def controlelijst(session: Session = Depends(current_session)):
    return get_store().controlelijst(tenant_id=session.tenant_id)


@app.get("/audit")
async def audit(limit: int = 100, session: Session = Depends(current_session)):
    return get_store().audit_trail(limit, tenant_id=session.tenant_id)


@app.get("/whatsapp/webhook")
async def whatsapp_verify(request: Request):
    """Meta Cloud API webhook-verificatie (hub.challenge)."""
    from fastapi.responses import PlainTextResponse

    params = request.query_params
    if (params.get("hub.mode") == "subscribe"
            and params.get("hub.verify_token") == get_settings().whatsapp_verify_token
            and get_settings().whatsapp_verify_token):
        return PlainTextResponse(params.get("hub.challenge", ""))
    return PlainTextResponse("verification failed", status_code=403)


@app.post("/whatsapp/webhook")
async def whatsapp_webhook(payload: dict):
    """Inkomende WhatsApp-berichten (tekst + foto van bonnen) → router → antwoord."""
    from boekhouder.providers.whatsapp import WhatsAppChannel

    channel = WhatsAppChannel()
    for msg in WhatsAppChannel.parse_incoming(payload):
        sender = msg["from"]
        image_bytes = channel.download_media(msg["image_id"]) if msg["image_id"] else None
        reply = router().handle(msg["text"], session_id=sender, tenant_id=LOCAL_TENANT,
                                image_bytes=image_bytes)
        channel.send(sender, reply.text)
    return {"ok": True}


@app.post("/telegram/webhook")
async def telegram_webhook(update: dict):
    """Telegram intake (single-bot = single company -> local tenant). Zie docs."""
    from boekhouder.providers.telegram import TelegramChannel

    channel = TelegramChannel()
    msg = update.get("message", {})
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = msg.get("text") or msg.get("caption") or ""
    image_bytes = None
    if msg.get("photo"):
        image_bytes = channel.download_photo(msg["photo"][-1]["file_id"])
        text = text or "bonnetje"
    reply = router().handle(text, session_id=chat_id, tenant_id=LOCAL_TENANT,
                            image_bytes=image_bytes)
    channel.send(chat_id, reply.text)
    return {"ok": True}
