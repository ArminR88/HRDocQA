from langgraph.graph import END, START, StateGraph

from backend.question_extraction import build_extraction_graph

from .nodes import (
    answer_failure_node,
    answer_generation_node,
    join_answer_results_node,
    no_match_record_node,
    question_retrieval_node,
)
from .schema import Answer_State


def _route_after_extraction(state: Answer_State) -> str:
    """Description: Route failed extraction directly to its failure result.

    Arguments:
        state (Answer_State): State returned by the question-extraction subgraph.

    Returns:
        The retrieval route after successful extraction or the failure route otherwise.

    Example:
        >>> _route_after_extraction({"polish_status": "ok"})
        "retrieval"
        >>> _route_after_extraction({"polish_status": "failed"})
        "failure"
    """
    if state["polish_status"] == "ok":
        route = "retrieval"
    else:
        route = "failure"
    return route


def _route_after_retrieval(state: Answer_State) -> list[str]:
    """Description: Select answer and no-match branches for retrieved questions.

    Arguments:
        state: Pipeline state with retrieval case markers.

    Returns:
        Branch names needed to process the labeled questions.

    Example:
        >>> _route_after_retrieval({"topic_speech_act_labeled": [...]})
        ["answer", "no_match"]
    """
    labeled_questions = state["topic_speech_act_labeled"]
    has_retrieved = False
    has_no_match = False
    for question in labeled_questions:
        case = question["case"]
        if case == "retrieved":
            has_retrieved = True
        if case == "no_match":
            has_no_match = True

    routes = []
    if has_retrieved:
        routes.append("answer")
    if has_no_match:
        routes.append("no_match")
    return routes


def build_answer_graph():
    """Description: Build the HR question-answer pipeline graph.

    Arguments:
        None.

    Returns:
        Compiled graph running analysis, retrieval, and answer generation.

    Example:
        >>> build_answer_graph().invoke({"raw_query": "How do I request leave?"})
        {"topic_speech_act_labeled": [...], "final_message": "..."}
    """
    graph = StateGraph(Answer_State)
    graph.add_node("question_extraction", build_extraction_graph())
    graph.add_node("failure", answer_failure_node)
    graph.add_node("retrieval", question_retrieval_node)
    graph.add_node("answer", answer_generation_node)
    graph.add_node("no_match", no_match_record_node)
    graph.add_node("join", join_answer_results_node)
    graph.add_edge(START, "question_extraction")
    graph.add_conditional_edges(
        "question_extraction",
        _route_after_extraction,
        {"retrieval": "retrieval", "failure": "failure"},
    )
    graph.add_edge("failure", END)
    graph.add_conditional_edges(
        "retrieval",
        _route_after_retrieval,
        {"answer": "answer", "no_match": "no_match"},
    )
    graph.add_edge("answer", "join")
    graph.add_edge("no_match", "join")
    graph.add_edge("join", END)
    compiled = graph.compile()
    return compiled
