"""Deterministic evaluation set for graduated retrieval and quota behavior."""

from __future__ import annotations

import backend.agent.qa as qa
from backend.agent.financial_context import construir_fragmentos_indicadores


def _embedding_must_not_run(*_args, **_kwargs):
    raise AssertionError("the embedding provider must not be called on this route")


def test_structured_route_precedes_embeddings(monkeypatch):
    monkeypatch.setattr(qa, "embed_text", _embedding_must_not_run)
    structured = construir_fragmentos_indicadores({"roa": 0.12, "roe": 0.18}, [])

    result = qa.buscar_fragmentos_graduados(
        "¿Qué indican mi ROA y ROE?",
        ["[Pagina 1]\nActivos: 100"],
        structured,
    )

    assert result["ruta"] == "estructurada"
    assert result["confianza"] == 1
    assert len(result["fragmentos"]) == 2


def test_literal_route_precedes_embeddings_and_preserves_pdf(monkeypatch):
    monkeypatch.setattr(qa, "embed_text", _embedding_must_not_run)

    result = qa.buscar_fragmentos_graduados(
        "¿Cuáles fueron las ventas?",
        ["[Pagina 2]\nVentas netas: 125000", "[Pagina 3]\nInventarios: 900"],
        [],
    )

    assert result["ruta"] == "literal"
    assert result["fragmentos"][0].startswith("[Pagina 2]")
    assert result["confianza"] >= 0.65


def test_semantic_route_reuses_cache_and_only_embeds_query(monkeypatch):
    calls: list[str] = []

    def fake_embed(text: str, *, task_type: str) -> list[float]:
        calls.append(task_type)
        return [1.0, 0.0]

    monkeypatch.setattr(qa, "embed_text", fake_embed)
    result = qa.buscar_fragmentos_graduados(
        "holgura monetaria futura",
        ["La compañía conserva reservas abundantes.", "Los inventarios rotan lentamente."],
        [],
        [[1.0, 0.0], [0.0, 1.0]],
    )

    assert result["ruta"] == "semantica"
    assert result["cache_hit"] is True
    assert calls == ["RETRIEVAL_QUERY"]


def test_semantic_route_builds_cache_once_when_missing(monkeypatch):
    calls: list[str] = []

    def fake_embed(text: str, *, task_type: str) -> list[float]:
        calls.append(task_type)
        return [1.0, 0.0] if "reservas" in text or task_type == "RETRIEVAL_QUERY" else [0.0, 1.0]

    monkeypatch.setattr(qa, "embed_text", fake_embed)
    result = qa.buscar_fragmentos_graduados(
        "holgura monetaria futura",
        ["La compañía conserva reservas abundantes.", "Los inventarios rotan lentamente."],
        [],
    )

    assert result["ruta"] == "semantica"
    assert result["cache_hit"] is False
    assert len(result["embeddings"]) == 2
    assert calls.count("RETRIEVAL_DOCUMENT") == 2
    assert calls.count("RETRIEVAL_QUERY") == 1


def test_embedding_failure_returns_no_evidence(monkeypatch):
    monkeypatch.setattr(qa, "embed_text", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("quota")))

    result = qa.buscar_fragmentos_graduados(
        "temperatura marciana",
        ["[Pagina 1]\nVentas: 100"],
        [],
    )

    assert result["ruta"] == "sin_evidencia"
    assert result["fragmentos"] == []


def test_low_semantic_similarity_returns_no_evidence(monkeypatch):
    monkeypatch.setattr(qa, "embed_text", lambda *_args, **_kwargs: [1.0, 0.0])

    result = qa.buscar_fragmentos_graduados(
        "temperatura marciana",
        ["[Pagina 1]\nVentas: 100"],
        [],
        [[0.0, 1.0]],
    )

    assert result["ruta"] == "sin_evidencia"
    assert result["fragmentos"] == []
    assert result["cache_hit"] is True
