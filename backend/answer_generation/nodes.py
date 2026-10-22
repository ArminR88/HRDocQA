import json
from functools import partial
from typing import Any

from backend.question_extraction.llm import call_with_retry
from backend.question_extraction.schema import Topic_Speech_Act_Labeled

from .prompts import ANSWER_JUDGE_SYSTEM, ANSWER_SYSTEM
from .retrieval_helper import embed_query, retrieve_top_k
from .schema import ANSWER_FAILURE_MESSAGE, AnswerState, CitedAnswer, Retrieval_Chunk


def _retrieve_question(question: Topic_Speech_Act_Labeled | dict[str, Any], question_index: int) -> dict[str, Any]:
    """Summary: Add retrieval results and routing metadata to one labeled question.

    Arguments:
        question: Question emitted by the analysis subgraph.
        question_index: Position of the question in the labeled list.

    Returns:
        Question record with retrieved chunks and a case marker.

    Example:
        >>> _retrieve_question(Topic_Speech_Act_Labeled(question="Is leave paid?", topic="parental_leave", speech_act="factual"), 0)
        {"question": "Is leave paid?", ...}
    """
    question_record = question.model_dump()
    query_vector = embed_query(question_record["question"])
    retrieved_chunks = retrieve_top_k(query_vector)
    case = "retrieved"
    if len(retrieved_chunks) == 0:
        case = "no_match"
    record = dict(question_record)
    record["question_index"] = question_index
    record["retrieved_chunks"] = retrieved_chunks
    record["case"] = case
    return record


def retrieval_node(state: AnswerState) -> dict[str, Any]:
    """Summary: Retrieve matching chunks for every labeled question.

    Arguments:
        state: Pipeline state after the analysis subgraph.

    Returns:
        State update containing retrieved question records.

    Example:
        >>> retrieval_node({"topic_speech_act_labeled": [...]})
        {"topic_speech_act_labeled": [...]}
    """
    labeled_questions = state["topic_speech_act_labeled"]
    indexed_questions = enumerate(labeled_questions)
    retrieved_questions = []
    for indexed_question in indexed_questions:
        question_index = indexed_question[0]
        question = indexed_question[1]
        retrieved_question = _retrieve_question(question, question_index)
        retrieved_questions.append(retrieved_question)
    update = {"topic_speech_act_labeled": retrieved_questions}
    return update


def _answer_user(
    question: str,
    speech_act: str,
    chunks: list[Retrieval_Chunk],
    feedback: str | None,
) -> str:
    """Summary: Build the answer model's user message.

    Arguments:
        question: Question to answer.
        speech_act: Classified speech act.
        chunks: Retrieved evidence chunks.
        feedback: Judge feedback from a prior attempt, if any.

    Returns:
        JSON user message with question context and evidence.

    Example:
        >>> _answer_user("Is leave paid?", "factual", [], None)
        '{"question": "Is leave paid?", ...}'
    """
    payload = {
        "question": question,
        "speech_act": speech_act,
        "retrieved_chunks": [chunk.model_dump() for chunk in chunks],
    }
    base_message = json.dumps(payload)
    if feedback is None:
        user_message = base_message
    else:
        user_message = f"{base_message}\n\n{feedback}"
    return user_message


def _answer_judge_input(
    question: str,
    speech_act: str,
    chunks: list[Retrieval_Chunk],
    output: CitedAnswer,
) -> str:
    """Summary: Build the answer judge's input from evidence and model output.

    Arguments:
        question: Question being answered.
        speech_act: Classified speech act.
        chunks: Retrieved evidence chunks.
        output: Candidate answer and citations.

    Returns:
        JSON judge input.

    Example:
        >>> _answer_judge_input("Is leave paid?", "factual", [], CitedAnswer(answer="Yes.", cited_chunk_ids=["x"]))
        '{"question": "Is leave paid?", ...}'
    """
    payload = {
        "question": question,
        "speech_act": speech_act,
        "retrieved_chunks": [chunk.model_dump() for chunk in chunks],
        "answer": output.answer,
        "cited_chunk_ids": output.cited_chunk_ids,
    }
    judge_input = json.dumps(payload)
    return judge_input


def _answer_question(question: dict[str, Any]) -> dict[str, Any]:
    """Summary: Generate, judge, and record one answer attempt sequence.

    Arguments:
        question: A labeled question with retrieved chunks.

    Returns:
        Question record populated with its answer, citations, sources, and case.

    Example:
        >>> _answer_question({"question": "Is leave paid?", "speech_act": "factual", ...})
        {"answer": "...", "cited_chunk_ids": [...], "sources": [...]}
    """
    text = question["question"]
    speech_act = question["speech_act"]
    chunks = question["retrieved_chunks"]
    user_builder = partial(_answer_user, text, speech_act, chunks)
    judge_input_builder = partial(_answer_judge_input, text, speech_act, chunks)
    retry_result = call_with_retry(
        ANSWER_SYSTEM,
        ANSWER_JUDGE_SYSTEM,
        user_builder,
        judge_input_builder,
        CitedAnswer,
        max_attempts=3,
    )
    output = retry_result[0]
    record = dict(question)
    cited_ids = output.cited_chunk_ids
    cited_chunks = [chunk for chunk in chunks if chunk.chunk_id in cited_ids]
    record["answer"] = output.answer
    record["cited_chunk_ids"] = cited_ids
    record["sources"] = [chunk.model_dump() for chunk in cited_chunks]
    record["case"] = "answered"
    return record


def answer_node(state: AnswerState) -> dict[str, Any]:
    """Summary: Generate answers for questions with retrieved evidence.

    Arguments:
        state: Pipeline state after retrieval.

    Returns:
        State update containing results from the answer branch.

    Example:
        >>> answer_node({"topic_speech_act_labeled": [...]})
        {"answer_results": [...]}
    """
    labeled_questions = state["topic_speech_act_labeled"]
    eligible_questions = [question for question in labeled_questions if question["case"] == "retrieved"]
    answer_results = [_answer_question(question) for question in eligible_questions]
    update = {"answer_results": answer_results}
    return update


def _no_match_question(question: dict[str, Any]) -> dict[str, Any]:
    """Summary: Record the no-match failure for one question.

    Arguments:
        question: Analyzed question with no chunks above threshold.

    Returns:
        Question record populated with the no-match failure result.

    Example:
        >>> _no_match_question({"question": "Is leave paid?", "question_index": 0})
        {"answer": "HRDocQA cannot provide an answer this time.", ...}
    """
    record = dict(question)
    record["answer"] = ANSWER_FAILURE_MESSAGE
    record["cited_chunk_ids"] = []
    record["sources"] = []
    record["case"] = "no_match"
    return record


def no_match_node(state: AnswerState) -> dict[str, Any]:
    """Summary: Record the no-match failure for questions without evidence.

    Arguments:
        state: Pipeline state after retrieval.

    Returns:
        State update containing results from the no-match branch.

    Example:
        >>> no_match_node({"topic_speech_act_labeled": [...]})
        {"no_match_results": [...]}
    """
    labeled_questions = state["topic_speech_act_labeled"]
    unmatched_questions = [question for question in labeled_questions if question["case"] == "no_match"]
    no_match_results = [_no_match_question(question) for question in unmatched_questions]
    update = {"no_match_results": no_match_results}
    return update


def join_node(state: AnswerState) -> dict[str, Any]:
    """Summary: Join answer and no-match branch results in question order.

    Arguments:
        state: Pipeline state containing branch results.

    Returns:
        State update with final labeled question records and final message.

    Example:
        >>> join_node({"topic_speech_act_labeled": [...], "answer_results": [...], "no_match_results": [...]})
        {"topic_speech_act_labeled": [...], "final_message": "..."}
    """
    results = []
    if "answer_results" in state:
        results.extend(state["answer_results"])
    if "no_match_results" in state:
        results.extend(state["no_match_results"])
    results_by_index = {result["question_index"]: result for result in results}
    labeled_questions = [
        results_by_index[question["question_index"]]
        for question in state["topic_speech_act_labeled"]
    ]
    final_message = "\n\n".join(question["answer"] for question in labeled_questions)
    update = {"topic_speech_act_labeled": labeled_questions, "final_message": final_message}
    return update
