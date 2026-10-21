from langgraph.graph import END, START, StateGraph

from .nodes import emit_fixed_message_node, polish_node, speech_act_node, topic_node
from .schema import PipelineState


def _route_after_polish(state: PipelineState) -> str:
    """
    Route from polish to topic or to the failure message.

    Arguments:
        state (PipelineState): Current graph state with polish_status set.

    Returns:
        str: Next node name, either "topic" or "emit_failure".

    Example:
        >>> _route_after_polish({"polish_status": "ok"})
        'topic'
    """
    if state["polish_status"] == "ok":
        return "topic"
    return "emit_failure"


def build_graph():
    """
    Build and compile the HR query analysis subgraph.

    Arguments:
        None

    Returns:
        CompiledStateGraph: Compiled graph over PipelineState.

    Example:
        >>> build_graph().invoke({"raw_query": "How do I request leave?"})
        {'raw_query': '...', 'polish_status': 'ok', 'analyzed': [...]}
    """
    graph = StateGraph(PipelineState)
    graph.add_node("polish", polish_node)
    graph.add_node("emit_failure", emit_fixed_message_node)
    graph.add_node("topic", topic_node)
    graph.add_node("speech_act", speech_act_node)
    graph.add_edge(START, "polish")
    routes = {"topic": "topic", "emit_failure": "emit_failure"}
    graph.add_conditional_edges("polish", _route_after_polish, routes)
    graph.add_edge("emit_failure", END)
    graph.add_edge("topic", "speech_act")
    graph.add_edge("speech_act", END)
    compiled = graph.compile()
    return compiled
