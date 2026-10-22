from langgraph.graph import END, START, StateGraph

from backend.question_extraction import build_extraction_graph

from .nodes import answer_node, join_node, no_match_node, retrieval_node
from .schema import AnswerState


def _route_after_analysis(state: AnswerState) -> str:
    """Summary: Route failed analysis directly to its existing failure result.

    Arguments:
        state: State returned by the analysis subgraph.

    Returns:
        The retrieval route for successful analysis or the end route on failure.

    Example:
        >>> _route_after_analysis({"polish_status": "ok"})
        "retrieval"
    """
    if state["polish_status"] == "ok":
        route = "retrieval"
    else:
        route = "end"
    return route


def _route_after_retrieval(state: AnswerState) -> list[str]:
    """Summary: Select answer and no-match branches for retrieved questions.

    Arguments:
        state: Pipeline state with retrieval case markers.

    Returns:
        Branch names needed to process the analyzed questions.

    Example:
        >>> _route_after_retrieval({"analyzed": [...]})
        ["answer", "no_match"]
    """
    analyzed = state["analyzed"]
    cases = [question["case"] for question in analyzed]
    routes = []
    if any(case == "retrieved" for case in cases):
        routes.append("answer")
    if any(case == "no_match" for case in cases):
        routes.append("no_match")
    return routes


def build_answer_graph():
    """Summary: Build the HR question-answer pipeline graph.

    Arguments:
        None.

    Returns:
        Compiled graph running analysis, retrieval, and answer generation.

    Example:
        >>> build_answer_graph().invoke({"raw_query": "How do I request leave?"})
        {"analyzed": [...], "final_message": "..."}
    """
    graph = StateGraph(AnswerState)
    graph.add_node("analysis", build_extraction_graph())
    graph.add_node("retrieval", retrieval_node)
    graph.add_node("answer", answer_node)
    graph.add_node("no_match", no_match_node)
    graph.add_node("join", join_node)
    graph.add_edge(START, "analysis")
    graph.add_conditional_edges(
        "analysis",
        _route_after_analysis,
        {"retrieval": "retrieval", "end": END},
    )
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
