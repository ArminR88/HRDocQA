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
    SPEECH_ACTS,
    TOPICS,
    AnalyzedQuestion,
    PipelineState,
    PolishedOutput,
    SpeechActOutput,
    TopicOutput,
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


def _polish_judge_input(raw_query: str, output: PolishedOutput) -> str:
    """
    Build the polish judge user message.

    Arguments:
        raw_query (str): Original user query.
        output (PolishedOutput): Parsed polish output.

    Returns:
        str: JSON text with the raw query and polished questions.

    Example:
        >>> _polish_judge_input("Hi?", PolishedOutput(status="ok", questions=["Hi?"]))
        '{"raw_query": "Hi?", "polished_questions": ["Hi?"]}'
    """
    payload = {}
    payload["raw_query"] = raw_query
    payload["polished_questions"] = output.questions
    judge_input = json.dumps(payload)
    return judge_input


def _topic_judge_input(question: str, output: TopicOutput) -> str:
    """
    Build the topic judge user message.

    Arguments:
        question (str): Polished question.
        output (TopicOutput): Parsed topic output.

    Returns:
        str: JSON text with the question, allowed topics and assigned topic.

    Example:
        >>> _topic_judge_input("Is leave paid?", TopicOutput(topic="parental_leave"))
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
    output, passed = call_with_retry(
        POLISH_SYSTEM,
        POLISH_JUDGE_SYSTEM,
        user_builder,
        judge_input_builder,
        PolishedOutput,
        max_attempts=3,
    )
    failure = {"polish_status": "failed", "polished_questions": []}
    if passed == False:
        return failure
    if output.status != "ok":
        return failure
    if not output.questions:
        return failure
    success = {}
    success["polish_status"] = "ok"
    success["polished_questions"] = output.questions
    return success


def polish_node(state: PipelineState) -> dict:
    """
    Polish the raw query into standalone questions.

    Arguments:
        state (PipelineState): Current graph state with raw_query set.

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


def emit_fixed_message_node(state: PipelineState) -> dict:
    """
    Emit the fixed failure message.

    Arguments:
        state (PipelineState): Current graph state.

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
    output, passed = call_with_retry(
        TOPIC_SYSTEM,
        TOPIC_JUDGE_SYSTEM,
        user_builder,
        judge_input_builder,
        TopicOutput,
        max_attempts=3,
    )
    if passed == False:
        return "unidentified"
    topic = output.topic
    if topic not in TOPICS:
        return "unidentified"
    return topic


def _label_topics(questions: list[str]) -> list[dict]:
    """
    Attach a topic to each question.

    Arguments:
        questions (list[str]): Polished questions.

    Returns:
        list[dict]: One {"text", "topic"} dict per question.

    Example:
        >>> _label_topics(["Is leave paid?"])
        [{'text': 'Is leave paid?', 'topic': 'parental_leave'}]
    """
    labelled = []
    for question in questions:
        topic = _topic_for(question)
        item = {"text": question, "topic": topic}
        labelled.append(item)
    return labelled


def topic_node(state: PipelineState) -> dict:
    """
    Assign a topic to every polished question.

    Arguments:
        state (PipelineState): Current graph state with polished_questions set.

    Returns:
        dict: State update whose analyzed holds {"text", "topic"} dicts.

    Example:
        >>> topic_node({"polished_questions": ["Is leave paid?"]})
        {'analyzed': [{'text': 'Is leave paid?', 'topic': 'parental_leave'}]}
    """
    questions = state["polished_questions"]
    labelled = _label_topics(questions)
    count = len(labelled)
    logging.info("[node:topic] labelled %d questions", count)
    update = {}
    update["analyzed"] = labelled
    return update


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
    output = _parse(raw, SpeechActOutput)
    speech_act = output.speech_act
    if speech_act not in SPEECH_ACTS:
        return "factual"
    return speech_act


def _complete_analysis(labelled: list[dict]) -> list[AnalyzedQuestion]:
    """
    Build the full AnalyzedQuestion for each topic-labelled question.

    Arguments:
        labelled (list[dict]): {"text", "topic"} dicts.

    Returns:
        list[AnalyzedQuestion]: One complete entry per question.

    Example:
        >>> _complete_analysis([{"text": "Is leave paid?", "topic": "parental_leave"}])
        [AnalyzedQuestion(text='Is leave paid?', topic='parental_leave', speech_act='factual')]
    """
    analyzed = []
    for item in labelled:
        text = item["text"]
        topic = item["topic"]
        speech_act = _speech_act_for(text)
        entry = AnalyzedQuestion(text=text, topic=topic, speech_act=speech_act)
        analyzed.append(entry)
    return analyzed


def speech_act_node(state: PipelineState) -> dict:
    """
    Assign a speech act to every topic-labelled question.

    Arguments:
        state (PipelineState): Current graph state with analyzed topic dicts.

    Returns:
        dict: State update whose analyzed holds complete AnalyzedQuestion objects.

    Example:
        >>> speech_act_node({"analyzed": [{"text": "Is leave paid?", "topic": "parental_leave"}]})
        {'analyzed': [AnalyzedQuestion(text='Is leave paid?', topic='parental_leave', speech_act='factual')]}
    """
    labelled = state["analyzed"]
    analyzed = _complete_analysis(labelled)
    count = len(analyzed)
    logging.info("[node:speech_act] classified %d questions", count)
    update = {}
    update["analyzed"] = analyzed
    return update
