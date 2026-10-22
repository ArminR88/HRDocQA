from langgraph.graph import END, START, StateGraph

from .nodes import classify_node, emit_fixed_message_node, polish_node
from .schema import Question_Extraction_State


def _route_after_polish(state: Question_Extraction_State) -> str:
    """
    Route from polish to classification or to the failure message.

    Arguments:
        state (Question_Extraction_State): Current graph state with polish_status set.

    Returns:
        str: Next node name, either "classify" or "emit_failure".

    Example:
        >>> _route_after_polish({"polish_status": "ok"})
        'classify'
    """
    if state["polish_status"] == "ok":
        return "classify"
    return "emit_failure"


def build_extraction_graph():
    """
    Build and compile the HR query analysis subgraph.

    Arguments:
        None

    Returns:
        CompiledStateGraph: Compiled graph over Question_Extraction_State.

    Example:
        >>> build_extraction_graph().invoke({"raw_query": "How do I request leave?"})
        {'raw_query': '...', 'polish_status': 'ok', 'topic_speech_act_labeled': [...]}
    """
    graph = StateGraph(Question_Extraction_State)
    graph.add_node("polish", polish_node)
    graph.add_node("emit_failure", emit_fixed_message_node)
    graph.add_node("classify", classify_node)
    graph.add_edge(START, "polish")
    routes = {"classify": "classify", "emit_failure": "emit_failure"}
    graph.add_conditional_edges("polish", _route_after_polish, routes)
    graph.add_edge("emit_failure", END)
    graph.add_edge("classify", END)
    compiled = graph.compile()
    return compiled
