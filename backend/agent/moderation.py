"""Guardrail determinista de lenguaje para los limites del agente."""

from __future__ import annotations

import re
import unicodedata

from backend.config import GUARDRAIL_BLOCKED_TERMS


def _normalizar(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto.casefold())
    return "".join(char for char in descompuesto if not unicodedata.combining(char))


def contiene_termino_bloqueado(texto: str) -> bool:
    normalizado = _normalizar(texto)
    return any(
        re.search(rf"(?<!\w){re.escape(_normalizar(term))}(?!\w)", normalizado)
        for term in GUARDRAIL_BLOCKED_TERMS
    )


MENSAJE_BLOQUEO = "La consulta fue bloqueada por las reglas de lenguaje respetuoso. Reformulala sin expresiones ofensivas."
