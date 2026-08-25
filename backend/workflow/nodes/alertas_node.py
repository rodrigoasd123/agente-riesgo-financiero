"""
Nodo: alertas
Detecta senales de alerta a partir de los indicadores calculados.
La logica vive en backend/agent/alertas.py.
"""
from backend.agent.alertas import detectar_alertas
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("alertas")
def alertas_node(state: AgentState) -> AgentState:
    alertas = detectar_alertas(state.get("indicadores", {}), state.get("cifras", {}))
    return {**state, "alertas": alertas}
