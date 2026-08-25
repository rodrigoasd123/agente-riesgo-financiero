"""Entrega de reportes por Gmail, Resend o SMTP."""

from __future__ import annotations

import base64
import re
import smtplib
import ssl
from email.message import EmailMessage
from threading import RLock

import requests
from dotenv import dotenv_values

from backend.config import (
    BASE_DIR,
    RESEND_API_KEY,
    RESEND_FROM_EMAIL,
    RESEND_TIMEOUT_SECONDS,
    SMTP_FROM_EMAIL,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_TIMEOUT_SECONDS,
    SMTP_USERNAME,
    SMTP_USE_TLS,
)
from backend.gmail_service import (
    GMAIL_MESSAGES,
    GmailError,
    gmail_authorized,
    send_gmail_report,
)


_RESEND_BASE_URL = "https://api.resend.com"
_MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
_resend_api_key = RESEND_API_KEY
_resend_from_email = RESEND_FROM_EMAIL
_resend_lock = RLock()


class EmailUnavailableError(RuntimeError):
    pass


class ResendValidationError(EmailUnavailableError):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


RESEND_MESSAGES = {
    "not_configured": "No hay una clave Resend guardada.",
    "invalid_key": "La clave Resend es inválida o no tiene permisos.",
    "network": "El servidor no puede conectarse con Resend por HTTPS.",
    "quota": "Resend rechazó la solicitud por cuota o límite de uso.",
    "sender": "El remitente no está autorizado. Usa tu correo de cuenta con onboarding@resend.dev o verifica un dominio.",
    "provider": "Resend no pudo completar la operación en este momento.",
}


def validate_recipient(value: str) -> str:
    recipient = value.strip()
    if len(recipient) > 254 or "\r" in recipient or "\n" in recipient:
        raise ValueError("Direccion de correo invalida")
    if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_\x60{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+", recipient):
        raise ValueError("Direccion de correo invalida")
    return recipient


def configure_resend(api_key: str, from_email: str) -> None:
    global _resend_api_key, _resend_from_email
    sender = validate_recipient(from_email)
    with _resend_lock:
        _resend_api_key = api_key.strip()
        _resend_from_email = sender


def stored_resend_settings() -> tuple[str, str]:
    values = dotenv_values(BASE_DIR / ".env")
    key = str(values.get("RESEND_API_KEY") or "").strip()
    sender = str(values.get("RESEND_FROM_EMAIL") or "onboarding@resend.dev").strip()
    return key, sender


def resend_configured() -> bool:
    return bool(_resend_api_key and _resend_from_email)


def smtp_configured() -> bool:
    return bool(SMTP_HOST and SMTP_FROM_EMAIL)


def email_provider() -> str | None:
    if gmail_authorized():
        return "gmail"
    if resend_configured():
        return "resend"
    if smtp_configured():
        return "smtp"
    return None


def _resend_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "agente-riesgo-financiero/1.4",
    }


def test_resend_api_key(api_key: str) -> bool:
    candidate = api_key.strip()
    if not candidate:
        raise ResendValidationError("not_configured")
    try:
        response = requests.get(
            f"{_RESEND_BASE_URL}/domains",
            headers=_resend_headers(candidate),
            timeout=RESEND_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise ResendValidationError("network") from None
    # Una clave con permiso `sending_access` se autentica correctamente, pero
    # Resend le niega la lectura de dominios con 403. Es válida para este uso.
    if response.status_code in {200, 403}:
        return True
    if response.status_code == 401:
        raise ResendValidationError("invalid_key")
    if response.status_code == 429:
        raise ResendValidationError("quota")
    raise ResendValidationError("provider")


def _send_resend(
    recipient: str,
    pdf_filename: str,
    pdf_bytes: bytes,
    csv_filename: str,
    csv_bytes: bytes,
) -> str:
    if not resend_configured():
        raise EmailUnavailableError("Resend no esta configurado")
    if len(pdf_bytes) + len(csv_bytes) > _MAX_ATTACHMENT_BYTES:
        raise ValueError("El reporte excede el limite permitido para correo")
    payload = {
        "from": f"Agente Financiero <{_resend_from_email}>",
        "to": [validate_recipient(recipient)],
        "subject": "Reporte de riesgo financiero",
        "text": "Se adjuntan los reportes PDF y CSV solicitados. Revise cifras y supuestos antes de tomar decisiones.",
        "attachments": [
            {
                "filename": pdf_filename,
                "content": base64.b64encode(pdf_bytes).decode("ascii"),
            },
            {
                "filename": csv_filename,
                "content": base64.b64encode(csv_bytes).decode("ascii"),
            },
        ],
    }
    try:
        response = requests.post(
            f"{_RESEND_BASE_URL}/emails",
            headers=_resend_headers(_resend_api_key),
            json=payload,
            timeout=RESEND_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise EmailUnavailableError(RESEND_MESSAGES["network"]) from None
    if response.status_code == 200:
        data = response.json()
        return str(data.get("id") or "sent")
    if response.status_code in {401, 403}:
        reason = "sender" if response.status_code == 403 else "invalid_key"
        raise EmailUnavailableError(RESEND_MESSAGES[reason])
    if response.status_code == 429:
        raise EmailUnavailableError(RESEND_MESSAGES["quota"])
    raise EmailUnavailableError(RESEND_MESSAGES["provider"])


def _send_smtp(
    recipient: str,
    pdf_filename: str,
    pdf_bytes: bytes,
    csv_filename: str,
    csv_bytes: bytes,
) -> str:
    message = EmailMessage()
    message["Subject"] = "Reporte de riesgo financiero"
    message["From"] = SMTP_FROM_EMAIL
    message["To"] = validate_recipient(recipient)
    message.set_content("Se adjuntan los reportes PDF y CSV solicitados. Revise sus cifras y supuestos antes de tomar decisiones.")
    message.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_filename)
    message.add_attachment(csv_bytes, maintype="text", subtype="csv", filename=csv_filename)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as server:
            if SMTP_USE_TLS:
                server.starttls(context=ssl.create_default_context())
            if SMTP_USERNAME:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
    except (OSError, smtplib.SMTPException):
        raise EmailUnavailableError("No se pudo entregar el correo mediante el servidor SMTP configurado") from None
    return "smtp-sent"


def enviar_reporte(
    recipient: str,
    pdf_filename: str,
    pdf_bytes: bytes,
    csv_filename: str,
    csv_bytes: bytes,
) -> tuple[str, str]:
    """Prioriza Gmail; no reintenta para evitar entregas duplicadas."""
    recipient = validate_recipient(recipient)
    if gmail_authorized():
        try:
            return "gmail", send_gmail_report(
                recipient, pdf_filename, pdf_bytes, csv_filename, csv_bytes
            )
        except GmailError as exc:
            raise EmailUnavailableError(
                GMAIL_MESSAGES.get(exc.reason, GMAIL_MESSAGES["provider"])
            ) from None
    if resend_configured():
        return "resend", _send_resend(
            recipient, pdf_filename, pdf_bytes, csv_filename, csv_bytes
        )
    if smtp_configured():
        return "smtp", _send_smtp(
            recipient, pdf_filename, pdf_bytes, csv_filename, csv_bytes
        )
    raise EmailUnavailableError(
        "El correo no esta configurado. Conecta Gmail desde Configuracion."
    )
