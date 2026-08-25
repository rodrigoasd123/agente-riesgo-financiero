"""Contrato local del adaptador Gemini, sin llamadas de red."""

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

import backend.agent.gemini_client as gemini_client


class DemoSchema(BaseModel):
    valor: int


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def test_generate_structured_usa_modelo_y_schema(monkeypatch: pytest.MonkeyPatch):
    models = FakeModels(SimpleNamespace(parsed=DemoSchema(valor=7), text='{"valor":7}'))
    monkeypatch.setattr(
        gemini_client,
        "_get_client",
        lambda: SimpleNamespace(models=models),
    )

    result = gemini_client.generate_structured("dato", DemoSchema, "sistema")

    assert result.valor == 7
    call = models.calls[0]
    assert call["model"] == gemini_client.GEMINI_MODEL
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_schema is DemoSchema
    assert call["config"].system_instruction == "sistema"


def test_generate_structured_sanitiza_error(monkeypatch: pytest.MonkeyPatch):
    class BrokenModels:
        def generate_content(self, **_):
            raise RuntimeError("detalle sensible del proveedor")

    monkeypatch.setattr(
        gemini_client,
        "_get_client",
        lambda: SimpleNamespace(models=BrokenModels()),
    )
    with pytest.raises(gemini_client.GeminiUnavailableError) as exc:
        gemini_client.generate_structured("dato", DemoSchema)
    assert "sensible" not in str(exc.value)


def test_ocr_envia_png_con_prompt_acotado(monkeypatch: pytest.MonkeyPatch):
    models = FakeModels(SimpleNamespace(text="Ventas: 1000"))
    monkeypatch.setattr(gemini_client, "_get_client", lambda: SimpleNamespace(models=models))

    result = gemini_client.transcribe_page_image(b"imagen-png")

    assert result == "Ventas: 1000"
    call = models.calls[0]
    assert call["contents"][1].inline_data.mime_type == "image/png"
    assert call["config"].temperature == 0
    assert "Transcribe literalmente" in call["contents"][0]


def test_validacion_gemini_prueba_generacion_real(monkeypatch: pytest.MonkeyPatch):
    models = FakeModels(SimpleNamespace(text=""))
    monkeypatch.setattr(gemini_client, "_build_client", lambda key: SimpleNamespace(models=models))

    assert gemini_client.test_api_key("clave-valida") is True
    assert models.calls[0]["model"] == gemini_client.GEMINI_MODEL
    assert "Responde solamente OK" in models.calls[0]["contents"]


@pytest.mark.parametrize(
    ("code", "reason"),
    [(400, "invalid_key"), (404, "model_unavailable"), (429, "quota")],
)
def test_validacion_gemini_clasifica_error_sin_payload(monkeypatch: pytest.MonkeyPatch, code: int, reason: str):
    class ProviderError(Exception):
        pass

    error = ProviderError("secreto del proveedor")
    error.code = code

    class BrokenModels:
        def generate_content(self, **kwargs):
            raise error

    monkeypatch.setattr(gemini_client, "_build_client", lambda key: SimpleNamespace(models=BrokenModels()))
    with pytest.raises(gemini_client.GeminiValidationError) as exc:
        gemini_client.test_api_key("clave")
    assert exc.value.reason == reason
    assert "secreto" not in str(exc.value)
