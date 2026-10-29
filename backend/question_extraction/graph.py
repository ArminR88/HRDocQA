from langgraph.graph import END, START, StateGraph

from .nodes import (
    join_labels_node,
    question_polish_node,
    speech_act_classify_node,
    topic_classify_node,
)
from .schema import Question_Extraction_State


def _route_after_polish_to_topic(state: Question_Extraction_State) -> str:
    """
    Description: Route from polish to topic classification or graph end.

    Arguments:
        state (Question_Extraction_State): Current graph state with polish_status set.

    Returns:
        str: Next route name, either "topic_classify" or "end".

    Example:
        >>> _route_after_polish_to_topic({"polish_status": "ok"})
        'topic_classify'
    """
    if state["polish_status"] == "ok":
        return "topic_classify"
    return "end"


def _route_after_polish_to_speech_act(
    state: Question_Extraction_State,
) -> str:
    """
    Route from polish to speech-act classification or graph end.

    Arguments:
        state (Question_Extraction_State): Current graph state with polish_status set.

    Returns:
        str: Next route name, either "speech_act_classify" or "end".

    Example:
        >>> _route_after_polish_to_speech_act({"polish_status": "ok"})
        'speech_act_classify'
    """
    if state["polish_status"] == "ok":
        return "speech_act_classify"
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
    graph.add_node("topic_classify", topic_classify_node)
    graph.add_node("speech_act_classify", speech_act_classify_node)
    graph.add_node("join_labels", join_labels_node)
    graph.add_edge(START, "polish")
    # Fan out to two parallel branches on success; failures end the graph.
    graph.add_conditional_edges(
        "polish",
        _route_after_polish_to_topic,
        {"topic_classify": "topic_classify", "end": END},
    )
    graph.add_conditional_edges(
        "polish",
        _route_after_polish_to_speech_act,
        {"speech_act_classify": "speech_act_classify", "end": END},
    )
    graph.add_edge("topic_classify", "join_labels")
    graph.add_edge("speech_act_classify", "join_labels")
    graph.add_edge("join_labels", END)
    compiled = graph.compile()
    return compiled