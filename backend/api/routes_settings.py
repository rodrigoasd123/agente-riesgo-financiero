"""Configuracion operativa autenticada sin lectura de secretos."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from threading import RLock
from typing import Annotated

from dotenv import set_key
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend.agent.gemini_client import (
    GeminiValidationError,
    VALIDATION_MESSAGES,
    configure_api_key,
    is_gemini_configured,
    stored_api_key,
    test_api_key,
)
from backend.auth.dependencies import get_current_user
from backend.config import BASE_DIR, FRONTEND_URL, GEMINI_MODEL, OCR_MAX_PAGES
from backend.email_service import (
    RESEND_MESSAGES,
    ResendValidationError,
    configure_resend,
    email_provider,
    resend_configured,
    smtp_configured,
    stored_resend_settings,
    test_resend_api_key,
    validate_recipient,
)
from backend.gmail_service import (
    GMAIL_MESSAGES,
    GmailError,
    complete_authorization,
    configure_gmail_authorization,
    configure_gmail_client,
    consume_oauth_state,
    create_authorization_url,
    disconnect_gmail,
    gmail_account_email,
    gmail_authorized,
    gmail_credentials_configured,
    gmail_redirect_uri,
    test_gmail_connection,
    update_gmail_account_email,
)


router = APIRouter(prefix="/settings", tags=["configuracion"])
_lock = RLock()
_last_tested_at: str | None = None
_connected: bool | None = None
_resend_connected: bool | None = None
_gmail_connected: bool | None = None
_gmail_last_tested_at: str | None = None


class GeminiKeyRequest(BaseModel):
    api_key: Annotated[str, Field(min_length=20, max_length=512)]


class ResendKeyRequest(BaseModel):
    api_key: Annotated[str, Field(min_length=10, max_length=512)]
    from_email: Annotated[str, Field(min_length=3, max_length=254)] = "onboarding@resend.dev"


class GmailCredentialsRequest(BaseModel):
    client_id: Annotated[str, Field(min_length=20, max_length=512)]
    client_secret: Annotated[str, Field(min_length=8, max_length=512)]


def _status() -> dict:
    configured = is_gemini_configured()
    resend_key, _ = stored_resend_settings()
    return {
        "gemini_configured": configured,
        "gemini_key_stored": bool(stored_api_key()),
        "gemini_connected": _connected,
        "ocr_available": configured and _connected is True,
        "ocr_max_pages": OCR_MAX_PAGES,
        "gemini_model": GEMINI_MODEL,
        "last_tested_at": _last_tested_at,
        "gmail_credentials_configured": gmail_credentials_configured(),
        "gmail_authorized": gmail_authorized(),
        "gmail_connected": _gmail_connected,
        "gmail_account": gmail_account_email(),
        "gmail_redirect_uri": gmail_redirect_uri(),
        "gmail_last_tested_at": _gmail_last_tested_at,
        "resend_configured": resend_configured(),
        "resend_key_stored": bool(resend_key),
        "resend_connected": _resend_connected,
        "smtp_configured": smtp_configured(),
        "email_provider": email_provider(),
        "email_configured": email_provider() is not None,
    }


@router.get("/status")
def settings_status(_: Annotated[str, Depends(get_current_user)]) -> dict:
    return _status()


def _test(candidate: str | None = None) -> dict:
    global _connected, _last_tested_at
    try:
        test_api_key(candidate)
    except GeminiValidationError as exc:
        _connected = False
        _last_tested_at = datetime.now(timezone.utc).isoformat()
        raise HTTPException(
            status_code=422,
            detail=VALIDATION_MESSAGES.get(exc.reason, VALIDATION_MESSAGES["provider"]),
        ) from None
    _connected = True
    _last_tested_at = datetime.now(timezone.utc).isoformat()
    return _status()


@router.post("/gemini/test")
def test_current_key(_: Annotated[str, Depends(get_current_user)]) -> dict:
    candidate = stored_api_key()
    _test(candidate)
    configure_api_key(candidate)
    return _status()


@router.post("/gemini")
def save_gemini_key(payload: GeminiKeyRequest, _: Annotated[str, Depends(get_current_user)]) -> dict:
    candidate = payload.api_key.strip()
    _test(candidate)
    with _lock:
        set_key(str(BASE_DIR / ".env"), "GEMINI_API_KEY", candidate, quote_mode="never")
        configure_api_key(candidate)
    return _status()


def _test_resend(candidate: str) -> None:
    global _resend_connected
    try:
        test_resend_api_key(candidate)
    except ResendValidationError as exc:
        _resend_connected = False
        raise HTTPException(
            status_code=422,
            detail=RESEND_MESSAGES.get(exc.reason, RESEND_MESSAGES["provider"]),
        ) from None
    _resend_connected = True


def _validate_sender(value: str) -> str:
    try:
        return validate_recipient(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.post("/resend/test")
def test_current_resend(_: Annotated[str, Depends(get_current_user)]) -> dict:
    candidate, sender = stored_resend_settings()
    sender = _validate_sender(sender)
    _test_resend(candidate)
    configure_resend(candidate, sender)
    return _status()


@router.post("/resend")
def save_resend(payload: ResendKeyRequest, _: Annotated[str, Depends(get_current_user)]) -> dict:
    candidate = payload.api_key.strip()
    sender = _validate_sender(payload.from_email)
    _test_resend(candidate)
    with _lock:
        set_key(str(BASE_DIR / ".env"), "RESEND_API_KEY", candidate, quote_mode="never")
        set_key(str(BASE_DIR / ".env"), "RESEND_FROM_EMAIL", sender, quote_mode="never")
        configure_resend(candidate, sender)
    return _status()


def _gmail_error(exc: GmailError, status_code: int = 422) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=GMAIL_MESSAGES.get(exc.reason, GMAIL_MESSAGES["provider"]),
    )


@router.post("/gmail/credentials")
def save_gmail_credentials(
    payload: GmailCredentialsRequest,
    _: Annotated[str, Depends(get_current_user)],
) -> dict:
    global _gmail_connected
    client_id = payload.client_id.strip()
    client_secret = payload.client_secret.strip()
    if not re.fullmatch(r"[A-Za-z0-9._-]+\.apps\.googleusercontent\.com", client_id):
        raise HTTPException(status_code=422, detail="El Client ID de Google no tiene el formato esperado.")
    if "\r" in client_secret or "\n" in client_secret:
        raise HTTPException(status_code=422, detail="El Client Secret de Google no es válido.")
    with _lock:
        set_key(str(BASE_DIR / ".env"), "GMAIL_CLIENT_ID", client_id, quote_mode="never")
        set_key(str(BASE_DIR / ".env"), "GMAIL_CLIENT_SECRET", client_secret, quote_mode="always")
        set_key(str(BASE_DIR / ".env"), "GMAIL_REFRESH_TOKEN", "", quote_mode="never")
        set_key(str(BASE_DIR / ".env"), "GMAIL_ACCOUNT_EMAIL", "", quote_mode="never")
        configure_gmail_client(client_id, client_secret)
        disconnect_gmail()
    _gmail_connected = False
    return _status()


@router.post("/gmail/authorize")
def authorize_gmail(_: Annotated[str, Depends(get_current_user)]) -> dict:
    try:
        authorization_url = create_authorization_url()
    except GmailError as exc:
        raise _gmail_error(exc) from None
    return {"authorization_url": authorization_url, "redirect_uri": gmail_redirect_uri()}


@router.get("/gmail/callback", include_in_schema=False)
def gmail_callback(
    state: str = "",
    code: str = "",
    error: str = "",
) -> RedirectResponse:
    global _gmail_connected, _gmail_last_tested_at
    if error:
        try:
            consume_oauth_state(state)
        except GmailError as exc:
            raise _gmail_error(exc, 400) from None
        return RedirectResponse(f"{FRONTEND_URL}/?gmail=cancelled", status_code=303)
    try:
        encrypted_token, account_email = complete_authorization(code, state)
    except GmailError as exc:
        if exc.reason == "state":
            raise _gmail_error(exc, 400) from None
        return RedirectResponse(f"{FRONTEND_URL}/?gmail=error", status_code=303)
    with _lock:
        set_key(str(BASE_DIR / ".env"), "GMAIL_REFRESH_TOKEN", encrypted_token, quote_mode="always")
        set_key(str(BASE_DIR / ".env"), "GMAIL_ACCOUNT_EMAIL", account_email, quote_mode="never")
        configure_gmail_authorization(encrypted_token, account_email)
    _gmail_connected = True
    _gmail_last_tested_at = datetime.now(timezone.utc).isoformat()
    return RedirectResponse(f"{FRONTEND_URL}/?gmail=connected", status_code=303)


@router.post("/gmail/test")
def test_current_gmail(_: Annotated[str, Depends(get_current_user)]) -> dict:
    global _gmail_connected, _gmail_last_tested_at
    try:
        account_email = test_gmail_connection()
    except GmailError as exc:
        _gmail_connected = False
        _gmail_last_tested_at = datetime.now(timezone.utc).isoformat()
        raise _gmail_error(exc) from None
    update_gmail_account_email(account_email)
    with _lock:
        set_key(str(BASE_DIR / ".env"), "GMAIL_ACCOUNT_EMAIL", account_email, quote_mode="never")
    _gmail_connected = True
    _gmail_last_tested_at = datetime.now(timezone.utc).isoformat()
    return _status()


@router.delete("/gmail")
def remove_gmail(_: Annotated[str, Depends(get_current_user)]) -> dict:
    global _gmail_connected, _gmail_last_tested_at
    with _lock:
        set_key(str(BASE_DIR / ".env"), "GMAIL_REFRESH_TOKEN", "", quote_mode="never")
        set_key(str(BASE_DIR / ".env"), "GMAIL_ACCOUNT_EMAIL", "", quote_mode="never")
        disconnect_gmail()
    _gmail_connected = False
    _gmail_last_tested_at = datetime.now(timezone.utc).isoformat()
    return _status()
