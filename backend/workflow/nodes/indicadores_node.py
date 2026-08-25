"""
Nodo: indicadores
Calcula los indicadores financieros a partir de las cifras extraidas.
La logica de calculo vive en backend/agent/indicadores.py.
"""
from backend.agent.indicadores import calcular_indicadores
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("indicadores")
def indicadores_node(state: AgentState) -> AgentState:
    indicadores = calcular_indicadores(state.get("cifras", {}))
    return {**state, "indicadores": indicadores}
