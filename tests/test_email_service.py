from types import SimpleNamespace

import pytest
import requests

import backend.email_service as email_service


@pytest.fixture(autouse=True)
def reset_resend(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(email_service, "_resend_api_key", "")
    monkeypatch.setattr(email_service, "_resend_from_email", "onboarding@resend.dev")
    monkeypatch.setattr(email_service, "gmail_authorized", lambda: False)


def test_resend_valida_clave_por_https(monkeypatch: pytest.MonkeyPatch):
    seen = {}

    def fake_get(url, headers, timeout, allow_redirects):
        seen.update({
            "url": url,
            "headers": headers,
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        })
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr(email_service.requests, "get", fake_get)
    assert email_service.test_resend_api_key("re_demo") is True
    assert seen["url"] == "https://api.resend.com/domains"
    assert seen["headers"]["Authorization"] == "Bearer re_demo"
    assert seen["allow_redirects"] is False


def test_resend_acepta_clave_restringida_a_envio(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        email_service.requests,
        "get",
        lambda *args, **kwargs: SimpleNamespace(status_code=403),
    )
    assert email_service.test_resend_api_key("re_solo_envio") is True


def test_resend_envia_pdf_base64_por_endpoint_fijo(monkeypatch: pytest.MonkeyPatch):
    seen = {}

    def fake_post(url, headers, json, timeout, allow_redirects):
        seen.update({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
            "allow_redirects": allow_redirects,
        })
        return SimpleNamespace(status_code=200, json=lambda: {"id": "email-1"})

    monkeypatch.setattr(email_service.requests, "post", fake_post)
    email_service.configure_resend("re_demo", "onboarding@resend.dev")
    provider, message_id = email_service.enviar_reporte(
        "owner@example.com",
        "reporte.pdf",
        b"%PDF-demo",
        "reporte.csv",
        b"seccion,valor",
    )

    assert (provider, message_id) == ("resend", "email-1")
    assert seen["url"] == "https://api.resend.com/emails"
    assert seen["allow_redirects"] is False
    assert [item["filename"] for item in seen["json"]["attachments"]] == [
        "reporte.pdf",
        "reporte.csv",
    ]
    assert all(item["content"] for item in seen["json"]["attachments"])


def test_resend_sanitiza_red_y_remitente(monkeypatch: pytest.MonkeyPatch):
    def fail_get(*args, **kwargs):
        raise requests.ConnectTimeout("interno")

    monkeypatch.setattr(
        email_service.requests,
        "get",
        fail_get,
    )
    with pytest.raises(email_service.ResendValidationError) as exc:
        email_service.test_resend_api_key("re_demo")
    assert exc.value.reason == "network"
    with pytest.raises(ValueError):
        email_service.configure_resend("re_demo", "cabecera\r\nbcc@example.com")


def test_gmail_tiene_prioridad_sin_reintentar_en_resend(monkeypatch: pytest.MonkeyPatch):
    sent = {}
    monkeypatch.setattr(email_service, "gmail_authorized", lambda: True)
    monkeypatch.setattr(
        email_service,
        "send_gmail_report",
        lambda recipient, pdf_filename, pdf, csv_filename, csv: sent.update(
            {
                "recipient": recipient,
                "pdf_filename": pdf_filename,
                "pdf": pdf,
                "csv_filename": csv_filename,
                "csv": csv,
            }
        ) or "gmail-1",
    )
    monkeypatch.setattr(
        email_service,
        "_send_resend",
        lambda *args: pytest.fail("No debe usar Resend si Gmail está autorizado"),
    )
    assert email_service.enviar_reporte(
        "owner@example.com",
        "reporte.pdf",
        b"%PDF",
        "reporte.csv",
        b"a,b",
    ) == ("gmail", "gmail-1")
    assert sent["recipient"] == "owner@example.com"
    assert sent["csv_filename"] == "reporte.csv"


def test_smtp_adjunta_pdf_y_csv(monkeypatch: pytest.MonkeyPatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            captured.update({"host": host, "port": port, "timeout": timeout})

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context):
            captured["tls"] = True

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(email_service, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(email_service, "SMTP_FROM_EMAIL", "sender@example.com")
    monkeypatch.setattr(email_service, "SMTP_USE_TLS", True)
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)
    provider, message_id = email_service.enviar_reporte(
        "owner@example.com",
        "reporte.pdf",
        b"%PDF",
        "reporte.csv",
        b"a,b",
    )
    assert (provider, message_id) == ("smtp", "smtp-sent")
    attachments = list(captured["message"].iter_attachments())
    assert [item.get_filename() for item in attachments] == [
        "reporte.pdf",
        "reporte.csv",
    ]
