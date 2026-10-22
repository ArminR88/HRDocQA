from .question_extraction import build_extraction_graph
from .answer_generation import build_answer_graph


def run(raw_query):
    """
    Run extraction then answer generation on one raw query.

    Arguments:
        raw_query (str): The user's raw query.

    Returns:
        dict: Answer-state output from the answer generation graph.

    Example:
        >>> run("How many vacation days do I have?")
        {'topic_speech_act_labeled': [...], 'final_message': None}
    """
    extraction_state = {}
    extraction_state["raw_query"] = raw_query
    extraction_graph = build_extraction_graph()
    extraction = extraction_graph.invoke(extraction_state)
    answer_state = {}
    answer_state["raw_query"] = raw_query
    answer_state["topic_speech_act_labeled"] = extraction["topic_speech_act_labeled"]
    answer_state["final_message"] = extraction.get("final_message")
    answer_graph = build_answer_graph()
    result = answer_graph.invoke(answer_state)
    return result


__all__ = ["run", "build_extraction_graph", "build_answer_graph"]
