from langgraph.graph import END, START, StateGraph

from .nodes import question_polish_node, topic_and_speech_act_node
from .schema import Question_Extraction_State


def _route_after_polish(state: Question_Extraction_State) -> str:
    """
    Route from polish to classification or graph end.

    Arguments:
        state (Question_Extraction_State): Current graph state with polish_status set.

    Returns:
        str: Next route name, either "classify" or "end".

    Example:
        >>> _route_after_polish({"polish_status": "ok"})
        'classify'
    """
    if state["polish_status"] == "ok":
        return "classify"
    return "end"


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
    graph.add_node("polish", question_polish_node)
    graph.add_node("classify", topic_and_speech_act_node)
    graph.add_edge(START, "polish")
    # Route polish failures directly to graph end.
    graph.add_conditional_edges(
        "polish",
        _route_after_polish,
        {"classify": "classify", "end": END},
    )
    graph.add_edge("classify", END)
    compiled = graph.compile()
    return compiled