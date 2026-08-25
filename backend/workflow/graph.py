"""
Construccion del grafo del agente con LangGraph (StateGraph).
Se definen DOS grafos compilados:

1. analysis_graph: procesa un PDF de principio a fin
   extractor -> indicadores -> alertas -> resumen -> END

2. qa_graph: responde preguntas sobre un documento ya analizado
   retrieval -> (condicional) -> answer -> END
                              -> clarification -> END
   Esta rama condicional es el "loop de aclaracion" mencionado en el
   spec: si el agente no encuentra la respuesta en el documento, no
   inventa una, sino que lo indica explicitamente.
"""
from langgraph.graph import StateGraph, END

from backend.workflow.state import AgentState
from backend.workflow.nodes.extractor_node import extractor_node
from backend.workflow.nodes.indicadores_node import indicadores_node
from backend.workflow.nodes.alertas_node import alertas_node
from backend.workflow.nodes.resumen_node import resumen_node
from backend.workflow.nodes.retrieval_node import retrieval_node
from backend.workflow.nodes.answer_node import answer_node
from backend.workflow.nodes.clarification_node import clarification_node


def build_analysis_graph():
    graph = StateGraph(AgentState)
    graph.add_node("extraer_pdf", extractor_node)
    graph.add_node("calcular_indicadores", indicadores_node)
    graph.add_node("detectar_alertas", alertas_node)
    graph.add_node("generar_resumen", resumen_node)

    graph.set_entry_point("extraer_pdf")
    graph.add_edge("extraer_pdf", "calcular_indicadores")
    graph.add_edge("calcular_indicadores", "detectar_alertas")
    graph.add_edge("detectar_alertas", "generar_resumen")
    graph.add_edge("generar_resumen", END)

    return graph.compile()


def _route_despues_de_retrieval(state: AgentState) -> str:
    """Edge condicional: decide si vamos a responder o a pedir aclaracion."""
    return "responder" if state.get("encontrado") else "aclarar"


def build_qa_graph():
    graph = StateGraph(AgentState)
    graph.add_node("recuperar_fragmentos", retrieval_node)
    graph.add_node("responder", answer_node)
    graph.add_node("aclarar", clarification_node)

    graph.set_entry_point("recuperar_fragmentos")
    graph.add_conditional_edges(
        "recuperar_fragmentos",
        _route_despues_de_retrieval,
        {"responder": "responder", "aclarar": "aclarar"},
    )
    graph.add_edge("responder", END)
    graph.add_edge("aclarar", END)

    return graph.compile()


# Grafos compilados, listos para invocar desde la API.
analysis_graph = build_analysis_graph()
qa_graph = build_qa_graph()
