import base64
from email import policy
from email.parser import BytesParser
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest

import backend.gmail_service as gmail


@pytest.fixture(autouse=True)
def reset_gmail(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(gmail, "_client_id", "demo.apps.googleusercontent.com")
    monkeypatch.setattr(gmail, "_client_secret", "secret-demo")
    monkeypatch.setattr(gmail, "_encrypted_refresh_token", "")
    monkeypatch.setattr(gmail, "_account_email", "")
    gmail._oauth_states.clear()


def test_refresh_token_se_cifra_y_no_acepta_texto_plano():
    encrypted = gmail.encrypt_refresh_token("refresh-secreto")
    assert encrypted.startswith("enc:v1:")
    assert "refresh-secreto" not in encrypted
    assert gmail.decrypt_refresh_token(encrypted) == "refresh-secreto"
    with pytest.raises(gmail.GmailError) as exc:
        gmail.decrypt_refresh_token("refresh-secreto")
    assert exc.value.reason == "reconnect"


def test_authorization_url_usa_alcance_minimo_y_estado_de_un_uso():
    url = gmail.create_authorization_url()
    params = parse_qs(urlparse(url).query)
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert params["access_type"] == ["offline"]
    assert params["prompt"] == ["consent"]
    assert set(params["scope"][0].split()) == set(gmail._SCOPES)
    state = params["state"][0]
    gmail.consume_oauth_state(state)
    with pytest.raises(gmail.GmailError) as exc:
        gmail.consume_oauth_state(state)
    assert exc.value.reason == "state"


def test_callback_intercambia_codigo_y_verifica_permiso(monkeypatch: pytest.MonkeyPatch):
    state = parse_qs(urlparse(gmail.create_authorization_url()).query)["state"][0]
    calls = []

    def fake_post(url, data, timeout, allow_redirects):
        calls.append((url, allow_redirects))
        return SimpleNamespace(
            status_code=200,
            json=lambda: {
                "access_token": "access",
                "refresh_token": "refresh",
                "scope": " ".join(gmail._SCOPES),
            },
        )

    def fake_get(url, headers, timeout, allow_redirects):
        calls.append((url, allow_redirects))
        return SimpleNamespace(status_code=200, json=lambda: {"email": "owner@gmail.com"})

    monkeypatch.setattr(gmail.requests, "post", fake_post)
    monkeypatch.setattr(gmail.requests, "get", fake_get)
    encrypted, email = gmail.complete_authorization("code", state)
    assert gmail.decrypt_refresh_token(encrypted) == "refresh"
    assert email == "owner@gmail.com"
    assert calls == [
        ("https://oauth2.googleapis.com/token", False),
        ("https://openidconnect.googleapis.com/v1/userinfo", False),
    ]


def test_gmail_renueva_y_envia_pdf_mime(monkeypatch: pytest.MonkeyPatch):
    encrypted = gmail.encrypt_refresh_token("refresh")
    gmail.configure_gmail_authorization(encrypted, "owner@gmail.com")
    sent = {}

    def fake_post(url, **kwargs):
        if url == "https://oauth2.googleapis.com/token":
            return SimpleNamespace(status_code=200, json=lambda: {"access_token": "access"})
        sent.update({"url": url, **kwargs})
        return SimpleNamespace(status_code=200, json=lambda: {"id": "gmail-1"})

    monkeypatch.setattr(gmail.requests, "post", fake_post)
    message_id = gmail.send_gmail_report(
        "analista@example.com",
        "reporte.pdf",
        b"%PDF-demo",
        "reporte.csv",
        b"seccion,valor\nventas,100",
    )
    assert message_id == "gmail-1"
    assert sent["url"] == "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
    assert sent["allow_redirects"] is False
    raw = base64.urlsafe_b64decode(sent["json"]["raw"])
    message = BytesParser(policy=policy.default).parsebytes(raw)
    assert message["From"] == "owner@gmail.com"
    assert message["To"] == "analista@example.com"
    attachments = list(message.iter_attachments())
    assert [attachment.get_filename() for attachment in attachments] == [
        "reporte.pdf",
        "reporte.csv",
    ]
    assert attachments[0].get_payload(decode=True) == b"%PDF-demo"
    assert attachments[1].get_payload(decode=True) == b"seccion,valor\nventas,100"


def test_gmail_sanitiza_error_de_red(monkeypatch: pytest.MonkeyPatch):
    encrypted = gmail.encrypt_refresh_token("refresh")
    gmail.configure_gmail_authorization(encrypted, "owner@gmail.com")
    monkeypatch.setattr(
        gmail.requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(gmail.requests.ConnectTimeout("interno")),
    )
    with pytest.raises(gmail.GmailError) as exc:
        gmail.test_gmail_connection()
    assert exc.value.reason == "network"
