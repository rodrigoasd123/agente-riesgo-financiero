"""OAuth 2.0 y envio de reportes mediante Gmail API por HTTPS."""

from __future__ import annotations

import base64
import hashlib
import secrets
import time
from email.message import EmailMessage
from threading import RLock
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken

from backend.config import (
    GMAIL_ACCOUNT_EMAIL,
    GMAIL_CLIENT_ID,
    GMAIL_CLIENT_SECRET,
    GMAIL_REDIRECT_URI,
    GMAIL_REFRESH_TOKEN,
    GMAIL_TIMEOUT_SECONDS,
    JWT_SECRET_KEY,
)


_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
_SCOPES = (
    "openid",
    "email",
    "https://www.googleapis.com/auth/gmail.send",
)
_STATE_TTL_SECONDS = 600
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_lock = RLock()
_oauth_states: dict[str, float] = {}
_client_id = GMAIL_CLIENT_ID
_client_secret = GMAIL_CLIENT_SECRET
_encrypted_refresh_token = GMAIL_REFRESH_TOKEN
_account_email = GMAIL_ACCOUNT_EMAIL


class GmailError(RuntimeError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


GMAIL_MESSAGES = {
    "credentials": "Configura el Client ID y Client Secret OAuth de Google.",
    "not_connected": "Gmail todavía no está conectado. Autoriza tu cuenta desde Configuración.",
    "state": "La autorización de Google expiró o ya fue utilizada. Inicia la conexión nuevamente.",
    "denied": "La autorización de Gmail fue cancelada.",
    "reconnect": "La autorización de Gmail venció o fue revocada. Conecta la cuenta nuevamente.",
    "permission": "La cuenta no concedió el permiso gmail.send. Conecta Gmail nuevamente.",
    "network": "El servidor no puede conectarse con Google por HTTPS.",
    "quota": "Gmail rechazó el envío por cuota o límite de uso.",
    "provider": "Google no pudo completar la operación en este momento.",
}


def _fernet() -> Fernet:
    digest = hashlib.sha256(f"gmail-refresh-v1:{JWT_SECRET_KEY}".encode("utf-8")).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_refresh_token(refresh_token: str) -> str:
    if not refresh_token.strip():
        raise GmailError("not_connected")
    encrypted = _fernet().encrypt(refresh_token.strip().encode("utf-8")).decode("ascii")
    return f"enc:v1:{encrypted}"


def decrypt_refresh_token(value: str) -> str:
    if not value.startswith("enc:v1:"):
        raise GmailError("reconnect")
    try:
        return _fernet().decrypt(value.removeprefix("enc:v1:").encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        raise GmailError("reconnect") from None


def configure_gmail_client(client_id: str, client_secret: str) -> None:
    global _client_id, _client_secret
    with _lock:
        _client_id = client_id.strip()
        _client_secret = client_secret.strip()


def configure_gmail_authorization(encrypted_refresh_token: str, account_email: str) -> None:
    global _encrypted_refresh_token, _account_email
    with _lock:
        _encrypted_refresh_token = encrypted_refresh_token.strip()
        _account_email = account_email.strip()


def update_gmail_account_email(account_email: str) -> None:
    global _account_email
    with _lock:
        _account_email = account_email.strip()


def disconnect_gmail() -> None:
    configure_gmail_authorization("", "")


def gmail_credentials_configured() -> bool:
    return bool(_client_id and _client_secret and GMAIL_REDIRECT_URI)


def gmail_authorized() -> bool:
    if not gmail_credentials_configured() or not _encrypted_refresh_token:
        return False
    try:
        decrypt_refresh_token(_encrypted_refresh_token)
    except GmailError:
        return False
    return True


def gmail_account_email() -> str | None:
    return _account_email or None


def gmail_redirect_uri() -> str:
    return GMAIL_REDIRECT_URI


def _purge_states(now: float) -> None:
    expired = [state for state, deadline in _oauth_states.items() if deadline < now]
    for state in expired:
        _oauth_states.pop(state, None)


def create_authorization_url() -> str:
    if not gmail_credentials_configured():
        raise GmailError("credentials")
    state = secrets.token_urlsafe(32)
    now = time.monotonic()
    with _lock:
        _purge_states(now)
        _oauth_states[state] = now + _STATE_TTL_SECONDS
    params = {
        "client_id": _client_id,
        "redirect_uri": GMAIL_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def consume_oauth_state(state: str) -> None:
    now = time.monotonic()
    with _lock:
        _purge_states(now)
        deadline = _oauth_states.pop(state, None)
    if deadline is None or deadline < now:
        raise GmailError("state")


def _post_token(data: dict[str, str]) -> dict:
    try:
        response = requests.post(
            _TOKEN_URL,
            data=data,
            timeout=GMAIL_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise GmailError("network") from None
    if response.status_code == 200:
        try:
            return response.json()
        except ValueError:
            raise GmailError("provider") from None
    if response.status_code in {400, 401}:
        raise GmailError("reconnect")
    if response.status_code == 429:
        raise GmailError("quota")
    raise GmailError("provider")


def _userinfo(access_token: str) -> str:
    try:
        response = requests.get(
            _USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=GMAIL_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise GmailError("network") from None
    if response.status_code != 200:
        reason = "reconnect" if response.status_code in {401, 403} else "provider"
        raise GmailError(reason)
    try:
        email = str(response.json().get("email") or "").strip()
    except ValueError:
        raise GmailError("provider") from None
    if not email or "\r" in email or "\n" in email:
        raise GmailError("provider")
    return email


def complete_authorization(code: str, state: str) -> tuple[str, str]:
    if not code.strip():
        raise GmailError("denied")
    consume_oauth_state(state)
    token_data = _post_token(
        {
            "code": code.strip(),
            "client_id": _client_id,
            "client_secret": _client_secret,
            "redirect_uri": GMAIL_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    )
    access_token = str(token_data.get("access_token") or "")
    refresh_token = str(token_data.get("refresh_token") or "")
    granted = set(str(token_data.get("scope") or "").split())
    if not access_token or not refresh_token:
        raise GmailError("reconnect")
    if _SCOPES[-1] not in granted:
        raise GmailError("permission")
    return encrypt_refresh_token(refresh_token), _userinfo(access_token)


def _refresh_access_token() -> str:
    if not gmail_authorized():
        raise GmailError("not_connected")
    refresh_token = decrypt_refresh_token(_encrypted_refresh_token)
    token_data = _post_token(
        {
            "client_id": _client_id,
            "client_secret": _client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )
    access_token = str(token_data.get("access_token") or "")
    if not access_token:
        raise GmailError("reconnect")
    return access_token


def test_gmail_connection() -> str:
    return _userinfo(_refresh_access_token())


def send_gmail_report(
    recipient: str,
    pdf_filename: str,
    pdf_bytes: bytes,
    csv_filename: str,
    csv_bytes: bytes,
) -> str:
    if len(pdf_bytes) + len(csv_bytes) > _MAX_ATTACHMENT_BYTES:
        raise ValueError("El reporte excede el limite permitido para correo")
    access_token = _refresh_access_token()
    message = EmailMessage()
    message["Subject"] = "Reporte de riesgo financiero"
    message["From"] = _account_email or "me"
    message["To"] = recipient
    message.set_content(
        "Se adjuntan los reportes PDF y CSV solicitados. Revise cifras y supuestos antes de tomar decisiones."
    )
    message.add_attachment(
        pdf_bytes, maintype="application", subtype="pdf", filename=pdf_filename
    )
    message.add_attachment(
        csv_bytes, maintype="text", subtype="csv", filename=csv_filename
    )
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    try:
        response = requests.post(
            _SEND_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"raw": raw},
            timeout=GMAIL_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise GmailError("network") from None
    if response.status_code == 200:
        try:
            return str(response.json().get("id") or "sent")
        except ValueError:
            return "sent"
    if response.status_code == 401:
        raise GmailError("reconnect")
    if response.status_code == 403:
        raise GmailError("permission")
    if response.status_code == 429:
        raise GmailError("quota")
    raise GmailError("provider")
