"""Observability metadata must be useful without leaking financial content."""

from __future__ import annotations

import pytest

from backend.observability import tracing


class FakeTracker:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.metrics: dict[str, float] = {}
        self.params: dict[str, str] = {}

    def log_metric(self, key: str, value: float) -> None:
        if self.fail:
            raise RuntimeError("tracker unavailable")
        self.metrics[key] = value

    def log_param(self, key: str, value: str) -> None:
        if self.fail:
            raise RuntimeError("tracker unavailable")
        self.params[key] = value


def _activate_fake_tracker(monkeypatch, tracker: FakeTracker) -> None:
    monkeypatch.setattr(tracing, "_available", True)
    monkeypatch.setattr(tracing, "_initialized", True)
    monkeypatch.setattr(tracing, "_mlflow_module", tracker)


def test_traced_node_logs_safe_input_and_output_schema(monkeypatch):
    tracker = FakeTracker()
    _activate_fake_tracker(monkeypatch, tracker)
    secret = "cliente-secreto-98765"

    @tracing.traced_node("demo")
    def node(state: dict) -> dict:
        assert state["raw_text"] == secret
        return {"resumen": secret, "indicadores": {"roe": 0.42}}

    result = node({"raw_text": secret, "question": "dato privado"})

    assert result["resumen"] == secret
    assert tracker.params["demo_campos_entrada"] == "question,raw_text"
    assert tracker.params["demo_campos_salida"] == "indicadores,resumen"
    assert tracker.params["demo_estado"] == "completado"
    assert tracker.metrics["demo_cantidad_campos_entrada"] == 2
    assert tracker.metrics["demo_cantidad_campos_salida"] == 2
    assert "demo_duracion_ms" in tracker.metrics
    assert secret not in repr(tracker.params)
    assert secret not in repr(tracker.metrics)


def test_traced_node_omits_unsafe_mapping_keys(monkeypatch):
    tracker = FakeTracker()
    _activate_fake_tracker(monkeypatch, tracker)

    @tracing.traced_node("demo")
    def node(state: dict) -> dict:
        return {"respuesta": "ok", "clave con contenido privado": "no registrar"}

    node({"question": "ok", "API-KEY-123": "no registrar"})

    assert tracker.params["demo_campos_entrada"] == "question"
    assert tracker.params["demo_campos_salida"] == "respuesta"


def test_traced_node_logs_failure_and_propagates(monkeypatch):
    tracker = FakeTracker()
    _activate_fake_tracker(monkeypatch, tracker)

    @tracing.traced_node("demo")
    def node(state: dict) -> dict:
        raise ValueError("private failure detail")

    with pytest.raises(ValueError, match="private failure detail"):
        node({"raw_text": "private document"})

    assert tracker.params["demo_estado"] == "fallido"
    assert tracker.params["demo_error_tipo"] == "ValueError"
    assert "private failure detail" not in repr(tracker.params)
    assert tracker.metrics["demo_cantidad_campos_salida"] == 0


def test_tracker_failure_does_not_change_node_result(monkeypatch):
    _activate_fake_tracker(monkeypatch, FakeTracker(fail=True))

    @tracing.traced_node("demo")
    def node(state: dict) -> dict:
        return {"answer": 42}

    assert node({"question": "test"}) == {"answer": 42}


def test_retrieval_metadata_is_allowlisted_and_content_free(monkeypatch):
    tracker = FakeTracker()
    _activate_fake_tracker(monkeypatch, tracker)

    tracing.log_retrieval_metadata("semantica", 0.82, 2, True)

    assert tracker.params == {"retrieval_route": "semantica"}
    assert tracker.metrics["retrieval_confidence"] == 0.82
    assert tracker.metrics["retrieval_result_count"] == 2
    assert tracker.metrics["retrieval_cache_hit"] == 1
    assert "private document" not in repr(tracker.params)


def test_retrieval_metadata_rejects_unknown_route(monkeypatch):
    tracker = FakeTracker()
    _activate_fake_tracker(monkeypatch, tracker)

    tracing.log_retrieval_metadata("user-controlled-content", 1, 1, False)

    assert tracker.params == {}
    assert tracker.metrics == {}
