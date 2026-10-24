import json
from typing import Any, Callable, Type, TypeVar

from pydantic import BaseModel

from backend.question_extraction.llm import (
    _call,
    _format_feedback,
    _parse,
    _prepend_heading_to_question,
)
from backend.question_extraction.schema import (
    Question_Extraction_Judge_Output,
    Topic_Speech_Act_Labeled,
)

from .prompts import ANSWER_JUDGE_SYSTEM, ANSWER_SYSTEM
from .retrieval_helper import embed_query, retrieve_top_k
from .schema import ANSWER_FAILURE_MESSAGE, AnswerState, CitedAnswer, Retrieval_Chunk

T = TypeVar("T", bound=BaseModel)


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


def _build_answer_generator_message(
    question_text: str,
    speech_act: str,
    chunks: list[Retrieval_Chunk],
) -> str:
    """Build the generator message for one answer attempt.

    Arguments:
        question_text: The question being answered.
        speech_act: "instruction" or "factual".
        chunks: Retrieved chunks supplying the evidence.

    Returns:
        JSON string sent to the answer generator.
    """
    # Collect the question, speech act, and retrieved chunks.
    payload = {}
    payload["question"] = question_text
    payload["speech_act"] = speech_act
    payload["retrieved_chunks"] = [chunk.model_dump() for chunk in chunks]

    # Serialize the generator message as JSON.
    generator_message = json.dumps(payload)
    return generator_message


def _answer_judge_input(
    generator_context: str,
    output: CitedAnswer,
) -> str:
    """Summary: Build the answer judge's input from evidence and model output.

    Arguments:
        generator_context: JSON context passed to the answer generator.
        output: Candidate answer and citations.

    Returns:
        JSON judge input.

    Example:
        >>> _answer_judge_input('{"question": "Is leave paid?", "speech_act": "factual", "retrieved_chunks": []}', CitedAnswer(answer="Yes.", cited_chunk_ids=["x"]))
        '{"question": "Is leave paid?", ...}'
    """
    # Add the candidate answer and citations to the generator context.
    judge_payload = json.loads(generator_context)
    judge_payload["answer"] = output.answer
    judge_payload["cited_chunk_ids"] = output.cited_chunk_ids

    # Serialize the complete answer-judge payload as JSON.
    serialized_judge_input = json.dumps(judge_payload)
    return serialized_judge_input


def _call_with_retry(
    generator_system_prompt: str,
    judge_system_prompt: str,
    label: str,
    text: str,
    judge_input_builder: Callable[[str, T], str],
    output_schema: Type[T],
    max_attempts: int = 3,
) -> tuple[T | None, bool]:
    """
    Call a generator prompt and judge each result, retrying with judge feedback.

    Arguments:
        generator_system_prompt (str): System prompt of the generator call.
        judge_system_prompt (str): System prompt of the judge call.
        label (str): Heading for the generator user message, e.g. "Raw query".
        text (str): The query or question being processed.
        judge_input_builder (Callable[[str, T], str]): Builds the judge user
            message from the original text and the parsed generator output.
        output_schema (Type[T]): Pydantic model the generator output is parsed into.
        max_attempts (int): Maximum number of generator attempts.

    Returns:
        tuple[T | None, bool]: (output, True) on a judged pass, otherwise
            (last_output, False) after max_attempts attempts.

    Example:
        >>> _call_with_retry(
        ...     POLISH_SYSTEM,
        ...     POLISH_JUDGE_SYSTEM,
        ...     "Raw query",
        ...     "hi how do i req leave",
        ...     _build_polish_comparison_payload,
        ...     Polished_Questions,
        ... )
        (Polished_Questions(status='ok', questions=['How do I request leave?']), True)
    """
    # Start with no feedback for the first attempt.
    feedback = None

    # Track whether the judge passed the last output.
    passed = False

    for _ in range(max_attempts):
        # Build the generator message and call the generator prompt.
        user_message = _prepend_heading_to_question(label, text, feedback)
        raw_output = _call(generator_system_prompt, user_message)

        # Parse the generator output into the expected schema.
        parsed_output = _parse(raw_output, output_schema)

        # Build the judge message from the original text and parsed output.
        judge_message = judge_input_builder(text, parsed_output)

        # Call the judge and parse its verdict.
        judge_raw_output = _call(judge_system_prompt, judge_message)
        verdict = _parse(
            judge_raw_output,
            Question_Extraction_Judge_Output,
        )

        # Stop when the judge passes the output.
        if verdict.passed == True:
            passed = True
            break

        # Format feedback for the next generator attempt.
        feedback = _format_feedback(
            verdict.failed_criteria,
            verdict.feedback,
        )

    # Return the final output and whether the judge passed it.
    retry_result = (parsed_output, passed)
    return retry_result


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
    # Read the labeled fields and retrieved chunks.
    question_text = question["question"]
    speech_act = question["speech_act"]
    chunks = question["retrieved_chunks"]

    # Build the generator message before starting the retry-and-judge flow.
    generator_message = _build_answer_generator_message(
        question_text,
        speech_act,
        chunks,
    )

    # Generate and judge the answer with the shared retry helper.
    retry_result = _call_with_retry(
        ANSWER_SYSTEM,
        ANSWER_JUDGE_SYSTEM,
        "",
        generator_message,
        _answer_judge_input,
        CitedAnswer,
    )

    # Unpack the parsed answer output.
    output = retry_result[0]

    # Select the chunks that the answer cited.
    record = dict(question)
    cited_ids = output.cited_chunk_ids
    cited_chunks = [chunk for chunk in chunks if chunk.chunk_id in cited_ids]

    # Add the answer fields to the original question record.
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
