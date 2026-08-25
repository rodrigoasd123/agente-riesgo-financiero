"""
Nodo: resumen
Genera el resumen ejecutivo final usando Gemini, a partir de los
indicadores y alertas ya calculados. La logica vive en
backend/agent/resumen.py.
"""
from backend.agent.resumen import generar_resumen
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("resumen")
def resumen_node(state: AgentState) -> AgentState:
    resumen = generar_resumen(state.get("indicadores", {}), state.get("alertas", []))
    return {**state, "resumen": resumen}
