import json
import logging
from functools import partial

from .llm import _call, _parse, call_with_retry
from .prompts import (
    POLISH_JUDGE_SYSTEM,
    POLISH_SYSTEM,
    SPEECH_ACT_SYSTEM,
    TOPIC_JUDGE_SYSTEM,
    TOPIC_SYSTEM,
)
from .schema import (
    FIXED_FAILURE_MESSAGE,
    TOPICS,
    Topic_Speech_Act_Labeled,
    Question_Extraction_State,
    Polished_Questions,
    Speech_Act_Classification,
    Topic_Classification,
)


def _build_user(label: str, text: str, feedback: str | None) -> str:
    """
    Build a primary user message, appending retry feedback when present.

    Arguments:
        label (str): Heading for the text, e.g. "Question".
        text (str): Raw query or question.
        feedback (str | None): None on the first attempt, else retry feedback.

    Returns:
        str: User message.

    Example:
        >>> _build_user("Question", "Is leave paid?", None)
        'Question:\\nIs leave paid?'
    """
    base = f"{label}:\n{text}"
    if feedback is None:
        return base
    user = f"{base}\n\n{feedback}"
    return user


def _polish_judge_input(raw_query: str, output: Polished_Questions) -> str:
    """
    Build the polish judge user message.

    Arguments:
        raw_query (str): Original user query.
        output (Polished_Questions): Parsed polish output.

    Returns:
        str: JSON text with the raw query and polished questions.

    Example:
        >>> _polish_judge_input("Hi?", Polished_Questions(status="ok", questions=["Hi?"]))
        '{"raw_query": "Hi?", "polished_questions": ["Hi?"]}'
    """
    payload = {}
    payload["raw_query"] = raw_query
    payload["polished_questions"] = output.questions
    judge_input = json.dumps(payload)
    return judge_input


def _topic_judge_input(question: str, output: Topic_Classification) -> str:
    """
    Build the topic judge user message.

    Arguments:
        question (str): Polished question.
        output (Topic_Classification): Parsed topic output.

    Returns:
        str: JSON text with the question, allowed topics and assigned topic.

    Example:
        >>> _topic_judge_input("Is leave paid?", Topic_Classification(topic="parental_leave"))
        '{"question": "Is leave paid?", "allowed_topics": [...], "assigned_topic": "parental_leave"}'
    """
    payload = {}
    payload["question"] = question
    payload["allowed_topics"] = TOPICS
    payload["assigned_topic"] = output.topic
    judge_input = json.dumps(payload)
    return judge_input


def _polish_query(raw_query: str) -> dict:
    """
    Polish a raw query with retry and judge.

    Arguments:
        raw_query (str): Original user query.

    Returns:
        dict: State update with polish_status and polished_questions.

    Example:
        >>> _polish_query("How do I request leave?")
        {'polish_status': 'ok', 'polished_questions': ['How do I request leave?']}
    """
    user_builder = partial(_build_user, "Raw query", raw_query)
    judge_input_builder = partial(_polish_judge_input, raw_query)
    retry_result = call_with_retry(
        POLISH_SYSTEM,
        POLISH_JUDGE_SYSTEM,
        user_builder,
        judge_input_builder,
        Polished_Questions,
        max_attempts=3,
    )
    output = retry_result[0]
    success = {}
    success["polish_status"] = "ok"
    success["polished_questions"] = output.questions
    return success


def polish_node(state: Question_Extraction_State) -> dict:
    """
    Polish the raw query into standalone questions.

    Arguments:
        state (Question_Extraction_State): Current graph state with raw_query set.

    Returns:
        dict: State update with polish_status and polished_questions.

    Example:
        >>> polish_node({"raw_query": "How do I request leave?"})
        {'polish_status': 'ok', 'polished_questions': ['How do I request leave?']}
    """
    raw_query = state["raw_query"]
    update = _polish_query(raw_query)
    status = update["polish_status"]
    count = len(update["polished_questions"])
    logging.info("[node:polish] status=%s questions=%d", status, count)
    return update


def emit_fixed_message_node(state: Question_Extraction_State) -> dict:
    """
    Emit the fixed failure message.

    Arguments:
        state (Question_Extraction_State): Current graph state.

    Returns:
        dict: State update with final_message set to FIXED_FAILURE_MESSAGE.

    Example:
        >>> emit_fixed_message_node({"polish_status": "failed"})
        {'final_message': 'Sorry HRDocQA cannot polish the question.'}
    """
    update = {}
    update["final_message"] = FIXED_FAILURE_MESSAGE
    return update


def _topic_for(question: str) -> str:
    """
    Classify one question's topic with retry and judge.

    Arguments:
        question (str): Polished question.

    Returns:
        str: Label from TOPICS; "unidentified" on judge failure or invalid label.

    Example:
        >>> _topic_for("How many vacation days do I have?")
        'vacation'
    """
    user_builder = partial(_build_user, "Question", question)
    judge_input_builder = partial(_topic_judge_input, question)
    retry_result = call_with_retry(
        TOPIC_SYSTEM,
        TOPIC_JUDGE_SYSTEM,
        user_builder,
        judge_input_builder,
        Topic_Classification,
        max_attempts=3,
    )
    output = retry_result[0]
    topic = output.topic
    return topic


def _speech_act_for(question: str) -> str:
    """
    Classify one question's speech act with a single call, no judge or retry.

    Arguments:
        question (str): Polished question.

    Returns:
        str: The returned value if in SPEECH_ACTS, otherwise "factual".
            A response that cannot be parsed raises.

    Example:
        >>> _speech_act_for("How do I request leave?")
        'instruction'
    """
    user = f"Question:\n{question}"
    raw = _call(SPEECH_ACT_SYSTEM, user)
    output = _parse(raw, Speech_Act_Classification)
    speech_act = output.speech_act
    return speech_act


def classify_node(state: Question_Extraction_State) -> dict:
    """
    Summary:
        Classify the topic and speech act for every polished question.

    Arguments:
        state (Question_Extraction_State): Current graph state with polished_questions set.

    Returns:
        dict: State update whose topic_speech_act_labeled holds complete Topic_Speech_Act_Labeled objects.

    Example:
        >>> classify_node({"polished_questions": ["Is leave paid?"]})
        {'topic_speech_act_labeled': [Topic_Speech_Act_Labeled(question='Is leave paid?', topic='parental_leave', speech_act='factual')]}
    """
    questions = state["polished_questions"]
    labeled_questions = []
    for question in questions:
        topic = _topic_for(question)
        speech_act = _speech_act_for(question)
        entry = Topic_Speech_Act_Labeled(question=question, topic=topic, speech_act=speech_act)
        labeled_questions.append(entry)
    count = len(labeled_questions)
    logging.info("[node:classify] classified %d questions", count)
    return {"topic_speech_act_labeled": labeled_questions}
