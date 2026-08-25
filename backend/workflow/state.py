"""
Contrato del State compartido entre todos los nodos del grafo
(LangGraph StateGraph). Toda la informacion que viaja por el agente
pasa por aqui: el PDF de entrada, lo extraido, resultados intermedios
y la respuesta final.
"""
from typing import List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # --- Entrada ---
    pdf_path: str
    pregunta: Optional[str]
    extraction_mode: str

    # --- Resultado de extraccion (nodo extractor) ---
    raw_text: str
    chunks: List[str]
    cifras: dict

    # --- Resultado de calculo (nodo indicadores) ---
    indicadores: dict

    # --- Resultado de deteccion (nodo alertas) ---
    alertas: list

    # --- Resultado de resumen (nodo resumen) ---
    resumen: str

    # --- Resultado de QA (nodos retrieval / answer / clarification) ---
    encontrado: Optional[bool]
    respuesta: Optional[str]
    fuente: Optional[str]
    _fragmentos_relevantes: List[str]

    # --- Metadatos ---
    analysis_id: Optional[str]
    error: Optional[str]
