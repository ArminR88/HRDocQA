import json
import logging
import time

from pydantic import ValidationError

from .llm import (
    _call,
    _format_feedback,
    _parse,
    _prepend_heading_to_question,
)
from .prompts import (
    POLISH_JUDGE_SYSTEM,
    POLISH_SYSTEM,
    SPEECH_ACT_JUDGE_SYSTEM,
    SPEECH_ACT_SYSTEM,
    TOPIC_JUDGE_SYSTEM,
    TOPIC_SYSTEM,
)
from .constants import ALLOWED_SPEECH_ACTS, ALLOWED_TOPICS
from .schema import (
    Question_Extraction_Judge_Output,
    Topic_Speech_Act_Labeled,
    Question_Extraction_State,
    Polished_Questions,
    Speech_Act_Classification,
    Topic_Classification,
)


def _build_polish_judge_message(
    raw_query: str,
    polished: Polished_Questions,
) -> str:
    """
    Description: Build the judge message for the polish stage.

    The payload carries the raw query and the polished questions so the judge
    can compare them.

    Arguments:
        raw_query (str): Original user query.
        polished (Polished_Questions): Parsed polish output.

    Returns:
        str: JSON text with the raw query and polished questions.

    Example:
        >>> _build_polish_judge_message(
        ...     "hi im [PERSON_NAME] emp id [EMPLOYEE_ID], how many wks parental leave r paid n can i split it?",
        ...     Polished_Questions(
        ...         status="ok",
        ...         questions=[
        ...             "How many weeks of parental leave are paid?",
        ...             "Can parental leave be split?",
        ...         ],
        ...     ),
        ... )
        '{"raw_query": "hi im [PERSON_NAME] emp id [EMPLOYEE_ID], how many wks parental leave r paid n can i split it?", "polished_questions": ["How many weeks of parental leave are paid?", "Can parental leave be split?"]}'
    """
    # Collect the raw query and the polished questions for comparison.
    payload = {}
    payload["raw_query"] = raw_query
    payload["polished_questions"] = polished.questions

    # Serialize the payload as JSON for the judge.
    comparison_payload = json.dumps(payload)

    return comparison_payload


def _build_topic_judge_message(
    polished_question: str,
    topic: Topic_Classification,
) -> str:
    """
    Description: Build the judge message for the topic stage.

    The payload carries the polished question, the allowed topics, and the
    assigned topic so the judge can compare them.

    Arguments:
        polished_question (str): Polished question.
        topic (Topic_Classification): Parsed topic output.

    Returns:
        str: JSON text with the question, allowed topics, and assigned topic.

    Example:
        >>> _build_topic_judge_message(
        ...     "Can I split my parental leave into two blocks?",
        ...     Topic_Classification(topic="parental_leave"),
        ... )
        '{"question": "Can I split my parental leave into two blocks?", "allowed_topics": ["vacation", "employee_change", "parental_leave", "unidentified"], "assigned_topic": "parental_leave"}'
    """
    # Collect the polished question, allowed topics, and assigned topic.
    payload = {}
    payload["question"] = polished_question
    payload["allowed_topics"] = ALLOWED_TOPICS
    payload["assigned_topic"] = topic.topic

    # Serialize the payload as JSON for the judge.
    comparison_payload = json.dumps(payload)

    return comparison_payload


def _build_speech_act_judge_message(
    polished_question: str,
    speech_act: Speech_Act_Classification,
) -> str:
    """
    Description: Build the judge message for the speech-act stage.

    Arguments:
        polished_question (str): Polished question.
        speech_act (Speech_Act_Classification): Parsed speech-act output.

    Returns:
        str: JSON text with the question, allowed speech acts, and assigned
            speech act.

    Example:
        >>> _build_speech_act_judge_message(
        ...     "How do I request parental leave?",
        ...     Speech_Act_Classification(speech_act="instruction"),
        ... )
        '{"question": "How do I request parental leave?", "allowed_speech_acts": ["instruction", "factual"], "assigned_speech_act": "instruction"}'
    """
    # Collect the question, allowed speech acts, and assigned speech act.
    payload = {}
    payload["question"] = polished_question
    payload["allowed_speech_acts"] = ALLOWED_SPEECH_ACTS
    payload["assigned_speech_act"] = speech_act.speech_act

    # Serialize the speech-act judge payload.
    judge_message = json.dumps(payload)

    return judge_message


def _polish_raw_query_with_judge(raw_query: str) -> dict:
    """
    Description: Polish a raw query with retry and judge.

    Arguments:
        raw_query (str): Original user query.

    Returns:
        dict: State update with polish_status and polished_questions.

    Example:
        >>> _polish_raw_query_with_judge("hi how do i req leave n is it paid")
        {'polish_status': 'ok', 'polished_questions': ['How do I request leave?', 'Is leave paid?']}
    """
    # Start with no feedback for the first attempt.
    feedback = None

    # Keep a failed result if every model response fails to parse.
    polished = Polished_Questions(status="failed", questions=[])

    # Track whether the judge passed the polish output.
    passed = False

    for _ in range(3):
        # Build the generator user message and call the polish prompt.
        user_message = _prepend_heading_to_question("Raw query", raw_query, feedback)
        raw_output = _call(POLISH_SYSTEM, user_message)

        # Parse the generator output into the polish schema.
        try:
            polished = _parse(raw_output, Polished_Questions)
        except (json.JSONDecodeError, ValidationError):
            # Retry when the model returns no JSON or malformed JSON.
            feedback = "Your previous response was not valid JSON matching the schema. Return only the JSON object."
            continue

        # Build the judge message from the raw query and the polished output.
        judge_message = _build_polish_judge_message(raw_query, polished)

        # Call the judge and parse its verdict.
        judge_raw = _call(POLISH_JUDGE_SYSTEM, judge_message)
        verdict = _parse(judge_raw, Question_Extraction_Judge_Output)

        # Stop when the judge passes the output.
        if verdict.passed == True:
            passed = True
            break

        # Otherwise, format the feedback for the next attempt.
        feedback = _format_feedback(verdict.failed_criteria, verdict.feedback)

    # Mark the result successful only when the judge passed it.
    polish_status = "failed"
    if passed == True:
        polish_status = "ok"

    # Preserve an explicit failure status from the polish output.
    if polished.status == "failed":
        polish_status = "failed"

    # Build the state update.
    state_update = {}
    state_update["polish_status"] = polish_status
    state_update["polished_questions"] = polished.questions

    return state_update


def question_polish_node(state: Question_Extraction_State) -> dict:
    """
    Description: Polish the raw query into standalone questions.

    Arguments:
        state (Question_Extraction_State): Current graph state with raw_query set.

    Returns:
        dict: State update with polish_status and polished_questions.

    Example:
        >>> question_polish_node({"raw_query": "hi how do i req leave n is it paid"})
        {'polish_status': 'ok', 'polished_questions': ['How do I request leave?', 'Is leave paid?']}
    """
    # Read the raw query from the state.
    raw_query = state["raw_query"]

    # Run the polish step.
    polish_result = _polish_raw_query_with_judge(raw_query)

    # Log a concise summary of the node result.
    status = polish_result["polish_status"]
    count = len(polish_result["polished_questions"])
    logging.info("[node:question_polish] status=%s questions=%d", status, count)

    return polish_result


def _classify_question_topic(
    polished_question: str,
    max_attempts: int = 3,
) -> str:
    """
    Description: Classify one polished question's topic with retry and judge.

    Arguments:
        polished_question (str): The polished question to classify.
        max_attempts (int): Maximum number of judge attempts (default: 3).

    Returns:
        str: Label from ALLOWED_TOPICS; `unidentified`
            when every attempt fails the judge.

    Example:
        >>> _classify_question_topic("How many vacation days do I have?")
        'vacation'
    """
    # Start with no feedback for the first attempt.
    feedback = None

    # Keep the unidentified fallback unless the judge accepts a topic.
    classified_topic = "unidentified"

    # Track whether the judge accepted a topic output.
    passed = False

    for _ in range(max_attempts):
        # Build the generator user message and call the topic prompt.
        user_message = _prepend_heading_to_question("Question", polished_question, feedback)
        raw_output = _call(TOPIC_SYSTEM, user_message)

        # Parse the generator output into the topic schema.
        try:
            topic_output = _parse(raw_output, Topic_Classification)
        except (json.JSONDecodeError, ValidationError):
            # Retry when the model returns no JSON or malformed JSON.
            feedback = "Your previous response was not valid JSON matching the schema. Return only the JSON object."
            continue

        # Build the judge message from the question and the topic output.
        judge_message = _build_topic_judge_message(polished_question, topic_output)

        # Call the judge and parse its verdict.
        judge_raw = _call(TOPIC_JUDGE_SYSTEM, judge_message)
        verdict = _parse(judge_raw, Question_Extraction_Judge_Output)

        # Stop when the judge passes the output.
        if verdict.passed == True:
            passed = True
            break

        # Otherwise, format the feedback for the next attempt.
        feedback = _format_feedback(verdict.failed_criteria, verdict.feedback)

    # Use the topic only when the judge accepted it.
    if passed == True:
        classified_topic = topic_output.topic

    return classified_topic


def _classify_question_speech_act_with_judge(
    polished_question: str,
    max_attempts: int = 3,
) -> str:
    """
    Description: Classify one polished question's speech act with retry and judge.

    Arguments:
        polished_question (str): The polished question to classify.
        max_attempts (int): Maximum number of judge attempts (default: 3).

    Returns:
        str: Label from ALLOWED_SPEECH_ACTS; "unverified" when every attempt
            fails the judge.

    Example:
        >>> _classify_question_speech_act_with_judge("How do I request leave?")
        'instruction'
    """
    # Start with no feedback for the first attempt.
    feedback = None

    # Keep the unverified fallback unless the judge accepts a speech act.
    classified_speech_act = "unverified"

    # Track whether the judge accepted a speech-act output.
    passed = False

    for _ in range(max_attempts):
        # Build the generator user message and call the speech-act prompt.
        user_message = _prepend_heading_to_question("Question", polished_question, feedback)
        raw_output = _call(SPEECH_ACT_SYSTEM, user_message)

        # Parse the generator output into the speech-act schema.
        try:
            speech_act_output = _parse(raw_output, Speech_Act_Classification)
        except (json.JSONDecodeError, ValidationError):
            # Retry when the model returns no JSON or malformed JSON.
            feedback = "Your previous response was not valid JSON matching the schema. Return only the JSON object."
            continue

        # Build the judge message from the question and speech-act output.
        judge_message = _build_speech_act_judge_message(polished_question, speech_act_output)

        # Call the judge and parse its verdict.
        judge_raw = _call(SPEECH_ACT_JUDGE_SYSTEM, judge_message)
        verdict = _parse(judge_raw, Question_Extraction_Judge_Output)

        # Stop when the judge accepts the speech-act output.
        if verdict.passed == True:
            passed = True
            break

        # Otherwise, format the feedback for the next attempt.
        feedback = _format_feedback(verdict.failed_criteria, verdict.feedback)

    # Use the speech act only when the judge accepted it.
    if passed == True:
        classified_speech_act = speech_act_output.speech_act

    return classified_speech_act


def topic_and_speech_act_node(state: Question_Extraction_State) -> dict:
    """
    Description: Assign a topic and speech act to every polished question.

    Arguments:
        state (Question_Extraction_State): Current graph state with
            polished_questions set.

    Returns:
        dict: State update whose topic_speech_act_labeled holds one
            Topic_Speech_Act_Labeled per question.

    Example:
        >>> topic_and_speech_act_node({"polished_questions": ["How do I request leave?", "Is leave paid?"]})
        {'topic_speech_act_labeled': [Topic_Speech_Act_Labeled(question='How do I request leave?', topic='unidentified', speech_act='instruction'), Topic_Speech_Act_Labeled(question='Is leave paid?', topic='parental_leave', speech_act='factual')]}
    """
    # Read the polished questions from the state.
    polished_questions = state["polished_questions"]

    # Label each question with its topic and speech act.
    labeled_questions = []
    for polished_question in polished_questions:
        topic_start = time.perf_counter()
        classified_topic = _classify_question_topic(polished_question)
        topic_ms = (time.perf_counter() - topic_start) * 1000
        speech_act_start = time.perf_counter()
        classified_speech_act = _classify_question_speech_act_with_judge(polished_question)
        speech_act_ms = (time.perf_counter() - speech_act_start) * 1000
        logging.info(
            "[timing] topic_ms=%.1f speech_act_ms=%.1f",
            topic_ms,
            speech_act_ms,
        )
        labeled_question = Topic_Speech_Act_Labeled(
            question=polished_question,
            topic=classified_topic,
            speech_act=classified_speech_act,
        )
        labeled_questions.append(labeled_question)

    # Log a concise summary of the node result.
    question_count = len(labeled_questions)
    logging.info(
        "[node:topic_and_speech_act] classified %d questions",
        question_count,
    )

    # Build the state update.
    state_update = {}
    state_update["topic_speech_act_labeled"] = labeled_questions

    return state_update
