"""
Nodo: answer
Se ejecuta solo cuando retrieval_node SI encontro fragmentos relevantes.
Genera la respuesta final citando el fragmento fuente del documento.
"""
from backend.agent.qa import responder_pregunta
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("answer")
def answer_node(state: AgentState) -> AgentState:
    pregunta = state.get("pregunta") or ""
    chunks = state.get("_fragmentos_relevantes") or state.get("chunks", [])
    resultado = responder_pregunta(pregunta, chunks)
    return {
        **state,
        "respuesta": resultado["respuesta"],
        "fuente": resultado["fuente"],
        "encontrado": resultado["encontrado"],
    }
