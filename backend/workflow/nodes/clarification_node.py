"""
Nodo: clarification
Se ejecuta cuando retrieval_node NO encontro fragmentos relevantes.
Responde explicitamente que no se encontro la informacion, en vez de
dejar que el LLM alucine una respuesta.
"""
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("clarification")
def clarification_node(state: AgentState) -> AgentState:
    return {
        **state,
        "respuesta": (
            "No encontre esa informacion en el documento analizado. "
            "Intenta reformular la pregunta o verifica que el dato "
            "este presente en el PDF cargado."
        ),
        "fuente": None,
        "encontrado": False,
    }
