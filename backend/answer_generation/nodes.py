import json
from typing import Any

from backend.shared.llm import (
    _call_llm_returning_json,
    _format_feedback,
    _parse_json_into_pydantic_instance,
    _prepend_heading_to_question,
)
from backend.shared.schema import Judge_Output, Topic_Speech_Act_Labeled

from .prompts import ANSWER_JUDGE_SYSTEM, ANSWER_SYSTEM
from .retrieval_helper import embed_query, retrieve_top_k
from .constants import ANSWER_FAILURE_MESSAGE
from .schema import Answer_Record, Answer_State, Cited_Answer, Retrieval_Chunk


def _retrieve_question(question: Topic_Speech_Act_Labeled | dict[str, Any], question_index: int) -> dict[str, Any]:
    """Description: Add retrieval results and routing metadata to one labeled question.

    Arguments:
        question: Question emitted by the analysis subgraph.
        question_index: Position of the question in the labeled list.

    Returns:
        Question record with retrieved chunks and a case marker.

    Example:
        >>> _retrieve_question(Topic_Speech_Act_Labeled(question="Is leave paid?", topic="parental_leave", speech_act="factual"), 0)
        {"question": "Is leave paid?", ...}
    """
    # Convert the labeled question to a record.
    question_record = question.model_dump()

    # Retrieve chunks for the question text.
    question_text = question_record["question"]
    query_vector = embed_query(question_text)
    retrieved_chunks = retrieve_top_k(query_vector)

    # Mark the question according to whether retrieval found chunks.
    case = "retrieved"
    if len(retrieved_chunks) == 0:
        case = "no_match"

    # Add retrieval metadata to the question record.
    record = dict(question_record)
    record["question_index"] = question_index
    record["retrieved_chunks"] = retrieved_chunks
    record["case"] = case

    # Return the retrieved question record.
    return record


def question_retrieval_node(state: Answer_State) -> dict[str, Any]:
    """Description: Retrieve matching chunks for every labeled question.

    Arguments:
        state: Pipeline state after the analysis subgraph.

    Returns:
        State update containing retrieved question records.

    Example:
        >>> question_retrieval_node({"topic_speech_act_labeled": [...]})
        {"topic_speech_act_labeled": [...]}
    """
    # Read the labeled questions.
    labeled_questions = state["topic_speech_act_labeled"]

    # Retrieve chunks for each labeled question.
    retrieved_questions = []
    for question_index, question in enumerate(labeled_questions):
        retrieved_question = _retrieve_question(question, question_index)
        retrieved_questions.append(retrieved_question)

    # Return the retrieval results.
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

    # Collect the chunk records.
    retrieved_chunks = []
    for chunk in chunks:
        chunk_record = chunk.model_dump()
        retrieved_chunks.append(chunk_record)
    payload["retrieved_chunks"] = retrieved_chunks

    # Serialize the generator message as JSON.
    generator_message = json.dumps(payload)
    return generator_message


def _build_answer_judge_message(
    question_text: str,
    speech_act: str,
    chunks: list[Retrieval_Chunk],
    output: Cited_Answer,
) -> str:
    """
    Description: Build the answer judge's input from structured answer fields.

    Arguments:
        question_text (str): The question being answered.
        speech_act (str): The question's speech-act label.
        chunks (list[Retrieval_Chunk]): Retrieved chunks supplied to the generator.
        output (Cited_Answer): Candidate answer and citations.

    Returns:
        str: The serialized judge input.
    """
    # Collect the question, speech act, retrieved chunks, and candidate answer.
    judge_payload = {}
    judge_payload["question"] = question_text
    judge_payload["speech_act"] = speech_act
    retrieved_chunks = []
    for chunk in chunks:
        chunk_record = chunk.model_dump()
        retrieved_chunks.append(chunk_record)
    judge_payload["retrieved_chunks"] = retrieved_chunks
    judge_payload["answer"] = output.answer
    judge_payload["cited_chunk_ids"] = output.cited_chunk_ids

    # Serialize the judge message as JSON.
    judge_message = json.dumps(judge_payload)
    return judge_message


def _answer_question_with_judge(question: dict[str, Any]) -> dict[str, Any]:
    """
    Description: Generate, judge, and record one answer attempt sequence.

    Arguments:
        question (dict[str, Any]): A labeled question with retrieved chunks.

    Returns:
        dict[str, Any]: The answer record. If judging exhausts all attempts,
            answer is ANSWER_FAILURE_MESSAGE and case is "answer_failed".
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

    # Run the retry-and-judge loop.
    feedback = None
    passed = False
    for _ in range(3):
        # Build the generator user message and call the answer prompt.
        user_message = _prepend_heading_to_question("", generator_message, feedback)
        raw_output = _call_llm_returning_json(ANSWER_SYSTEM, user_message)

        # Parse the generator output into the cited-answer schema.
        output = _parse_json_into_pydantic_instance(raw_output, Cited_Answer)

        # Build the judge message from the same fields the generator saw.
        judge_message = _build_answer_judge_message(question_text, speech_act, chunks, output)

        # Call the judge and parse its verdict.
        judge_raw = _call_llm_returning_json(ANSWER_JUDGE_SYSTEM, judge_message)
        verdict = _parse_json_into_pydantic_instance(
            judge_raw,
            Judge_Output,
        )

        # Stop when the judge passes the answer.
        if verdict.passed == True:
            passed = True
            break

        # Format feedback for the next attempt.
        feedback = _format_feedback(verdict.failed_criteria, verdict.feedback)

    # Select the chunks that the answer cited.
    cited_ids = output.cited_chunk_ids
    cited_chunks = []
    for chunk in chunks:
        if chunk.chunk_id in cited_ids:
            cited_chunks.append(chunk)

    # Choose the case and answer text from the pass flag.
    answer_text = ANSWER_FAILURE_MESSAGE
    case = "answer_failed"
    if passed == True:
        answer_text = output.answer
        case = "answered"

    # Build and dump the record.
    answer_record = Answer_Record(
        question=question_text,
        topic=question["topic"],
        speech_act=speech_act,
        question_index=question["question_index"],
        retrieved_chunks=chunks,
        answer=answer_text,
        cited_chunk_ids=cited_ids,
        sources=cited_chunks,
        case=case,
    )

    # Return the record as a dictionary for downstream graph nodes.
    return answer_record.model_dump()


def answer_generation_node(state: Answer_State) -> dict[str, Any]:
    """Description: Generate answers for questions with retrieved evidence.

    Arguments:
        state: Pipeline state after retrieval.

    Returns:
        State update containing results from the answer branch.

    Example:
        >>> answer_generation_node({"topic_speech_act_labeled": [...]})
        {"answer_results": [...]}
    """
    # Read questions with retrieval matches.
    labeled_questions = state["topic_speech_act_labeled"]

    # Select questions eligible for answer generation.
    eligible_questions = []
    for question in labeled_questions:
        if question["case"] == "retrieved":
            eligible_questions.append(question)

    # Generate answers for eligible questions.
    answer_results = []
    for question in eligible_questions:
        answer_result = _answer_question_with_judge(question)
        answer_results.append(answer_result)

    # Return the answer results.
    update = {"answer_results": answer_results}
    return update


def _build_no_match_record(question: dict[str, Any]) -> dict[str, Any]:
    """Description: Record the no-match failure for one question.

    Arguments:
        question: Analyzed question with no chunks above threshold.

    Returns:
        Question record populated with the no-match failure result.

    Example:
        >>> _build_no_match_record({"question": "Is leave paid?", "question_index": 0})
        {"answer": "HRDocQA cannot provide an answer this time.", ...}
    """
    # Construct and validate the no-match answer record.
    answer_record = Answer_Record(
        question=question["question"],
        topic=question["topic"],
        speech_act=question["speech_act"],
        question_index=question["question_index"],
        retrieved_chunks=question["retrieved_chunks"],
        answer=ANSWER_FAILURE_MESSAGE,
        cited_chunk_ids=[],
        sources=[],
        case="no_match",
    )

    # Return the record as a dictionary for downstream graph nodes.
    return answer_record.model_dump()


def no_match_record_node(state: Answer_State) -> dict[str, Any]:
    """Description: Record the no-match failure for questions without evidence.

    Arguments:
        state: Pipeline state after retrieval.

    Returns:
        State update containing results from the no-match branch.

    Example:
        >>> no_match_record_node({"topic_speech_act_labeled": [...]})
        {"no_match_results": [...]}
    """
    # Read questions without retrieval matches.
    labeled_questions = state["topic_speech_act_labeled"]

    # Select questions that require no-match results.
    unmatched_questions = []
    for question in labeled_questions:
        if question["case"] == "no_match":
            unmatched_questions.append(question)

    # Build no-match results for the selected questions.
    no_match_results = []
    for question in unmatched_questions:
        no_match_result = _build_no_match_record(question)
        no_match_results.append(no_match_result)

    # Return the no-match results.
    update = {"no_match_results": no_match_results}
    return update


def join_answer_results_node(state: Answer_State) -> dict[str, Any]:
    """Description: Join answer and no-match branch results in question order.

    Arguments:
        state: Pipeline state containing branch results.

    Returns:
        State update with final labeled question records and final message.

    Example:
        >>> join_answer_results_node({"topic_speech_act_labeled": [...], "answer_results": [...], "no_match_results": [...]})
        {"topic_speech_act_labeled": [...], "final_message": "..."}
    """
    # Collect answer and no-match results.
    results = []
    if "answer_results" in state:
        results.extend(state["answer_results"])
    if "no_match_results" in state:
        results.extend(state["no_match_results"])

    # Index results by question position.
    results_by_index = {}
    for result in results:
        question_index = result["question_index"]
        results_by_index[question_index] = result

    # Restore the labeled-question order.
    labeled_questions = []
    for question in state["topic_speech_act_labeled"]:
        question_index = question["question_index"]
        labeled_question = results_by_index[question_index]
        labeled_questions.append(labeled_question)

    # Join answers into the final message.
    answers = []
    for question in labeled_questions:
        answer = question["answer"]
        answers.append(answer)
    final_message = "\n\n".join(answers)

    # Return the joined state update.
    update = {"topic_speech_act_labeled": labeled_questions, "final_message": final_message}
    return update


def answer_failure_node(state: Answer_State) -> dict[str, Any]:
    """
    Description: Emit the universal answer failure message.

    Arguments:
        state (Answer_State): Current graph state.

    Returns:
        dict[str, Any]: State update with final_message set.
    """
    # Build the failure update.
    state_update = {}
    state_update["final_message"] = ANSWER_FAILURE_MESSAGE

    return state_update
