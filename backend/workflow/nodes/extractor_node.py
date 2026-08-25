"""
Nodo: extractor
Recibe el path del PDF y delega en backend/agent/pdf_reader.py la
extraccion de texto, chunks y cifras clave. El nodo se mantiene
delgado: no contiene logica de extraccion propia.
"""
from backend.agent.pdf_reader import procesar_pdf
from backend.observability.tracing import traced_node
from backend.workflow.state import AgentState


@traced_node("extractor")
def extractor_node(state: AgentState) -> AgentState:
    resultado = procesar_pdf(state["pdf_path"], state.get("extraction_mode", "normal"))
    return {**state, **resultado}
