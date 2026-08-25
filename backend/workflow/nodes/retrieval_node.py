"""
Nodo: retrieval
Busca los fragmentos del documento mas relevantes para la pregunta del
usuario (RAG). Si no encuentra nada relevante, marca encontrado=False
para que el grafo enrute hacia el nodo de aclaracion (clarification_node)
en lugar del nodo de respuesta.
"""
from backend.agent.qa import buscar_fragmentos_relevantes
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("retrieval")
def retrieval_node(state: AgentState) -> AgentState:
    pregunta = state.get("pregunta") or ""
    chunks = state.get("chunks", [])
    fragmentos = buscar_fragmentos_relevantes(pregunta, chunks)
    return {
        **state,
        "_fragmentos_relevantes": fragmentos,
        "encontrado": bool(fragmentos),
    }
