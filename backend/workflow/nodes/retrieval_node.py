"""
Nodo: retrieval
Busca los fragmentos del documento mas relevantes para la pregunta del
usuario (RAG). Si no encuentra nada relevante, marca encontrado=False
para que el grafo enrute hacia el nodo de aclaracion (clarification_node)
en lugar del nodo de respuesta.
"""
from backend.agent.qa import buscar_fragmentos_graduados
from backend.observability.tracing import log_retrieval_metadata, traced_node
from backend.workflow.state import AgentState


@traced_node("retrieval")
def retrieval_node(state: AgentState) -> AgentState:
    pregunta = state.get("pregunta") or ""
    resultado = buscar_fragmentos_graduados(
        pregunta,
        state.get("document_chunks") or state.get("chunks", []),
        state.get("structured_chunks", []),
        state.get("document_embeddings", []),
    )
    fragmentos = resultado["fragmentos"]
    log_retrieval_metadata(
        resultado["ruta"],
        resultado["confianza"],
        len(fragmentos),
        resultado["cache_hit"],
    )
    return {
        **state,
        "_fragmentos_relevantes": fragmentos,
        "encontrado": bool(fragmentos),
        "document_embeddings": resultado["embeddings"],
        "retrieval_route": resultado["ruta"],
        "retrieval_confidence": resultado["confianza"],
        "retrieval_cache_hit": resultado["cache_hit"],
    }
