"""Trazas MLflow opcionales, minimizadas y tolerantes a fallos."""

from __future__ import annotations

import functools
import re
import time
from collections.abc import Mapping
from typing import Callable

from backend.agent.gemini_client import PROMPT_VERSION
from backend.config import (
    GEMINI_MODEL,
    MLFLOW_ENABLED,
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
)


_initialized = False
_available = MLFLOW_ENABLED
_mlflow_module = None
_SAFE_FIELD_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_MAX_SCHEMA_CHARS = 450


def _safe_schema(value: object) -> tuple[str, int]:
    """Describe a mapping without logging any value or user-controlled key."""
    if not isinstance(value, Mapping):
        return "", 0
    names = sorted(
        key for key in value.keys()
        if isinstance(key, str) and _SAFE_FIELD_NAME.fullmatch(key)
    )
    schema = ",".join(names)
    return schema[:_MAX_SCHEMA_CHARS], len(names)


def _mlflow():
    global _mlflow_module
    if _mlflow_module is None:
        import mlflow

        _mlflow_module = mlflow
    return _mlflow_module


def _ensure_mlflow() -> bool:
    global _initialized, _available
    if not _available:
        return False
    if not _initialized:
        try:
            tracker = _mlflow()
            tracker.set_tracking_uri(MLFLOW_TRACKING_URI)
            tracker.set_experiment(MLFLOW_EXPERIMENT_NAME)
            _initialized = True
        except Exception:
            _available = False
    return _available


def traced_node(node_name: str) -> Callable:
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(state: dict) -> dict:
            inicio = time.perf_counter()
            error_type: str | None = None
            result: object = None
            try:
                result = fn(state)
                return result
            except Exception as exc:
                error_type = type(exc).__name__
                raise
            finally:
                if _ensure_mlflow():
                    try:
                        tracker = _mlflow()
                        input_schema, input_count = _safe_schema(state)
                        output_schema, output_count = _safe_schema(result)
                        tracker.log_metric(
                            f"{node_name}_duracion_ms",
                            round((time.perf_counter() - inicio) * 1000, 2),
                        )
                        tracker.log_metric(f"{node_name}_cantidad_campos_entrada", input_count)
                        tracker.log_metric(f"{node_name}_cantidad_campos_salida", output_count)
                        tracker.log_param(
                            f"{node_name}_campos_entrada",
                            input_schema,
                        )
                        tracker.log_param(f"{node_name}_campos_salida", output_schema)
                        tracker.log_param(
                            f"{node_name}_estado",
                            "fallido" if error_type else "completado",
                        )
                        if error_type:
                            tracker.log_param(f"{node_name}_error_tipo", error_type)
                    except Exception:
                        pass

        return wrapper

    return decorator


class agent_run:
    def __init__(self, run_name: str):
        self.run_name = run_name
        self._active = False

    def __enter__(self):
        if _ensure_mlflow():
            try:
                tracker = _mlflow()
                run = tracker.start_run(run_name=self.run_name)
                tracker.log_param("prompt_version", PROMPT_VERSION)
                tracker.log_param("gemini_model", GEMINI_MODEL)
                tracker.log_param("tracing_policy", "metadata-only-v1")
                self._active = True
                return run
            except Exception:
                self._active = False
        return None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._active:
            try:
                _mlflow().end_run(status="FAILED" if exc_type else "FINISHED")
            except Exception:
                pass
        return False
