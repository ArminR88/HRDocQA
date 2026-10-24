"""Build question-extraction prompts from centralized prompt data."""

from .constants import (
    POLISH_DESIGN_NOTES,
    POLISH_PROMPT_CRITERIA,
    POLISH_TEST_GATE_SPEC,
    TOPIC_DEFINITIONS,
)


def _render_criteria_block() -> str:
    """
    Description: Render polish criteria as a bullet list.

    Arguments: None.

    Returns:
        str: The rendered polish criteria block.
    """
    # Render each criterion as a labeled bullet.
    rendered_lines = []
    for criterion_id, criterion_text in POLISH_PROMPT_CRITERIA:
        rendered_line = f"- {criterion_id}: {criterion_text}"
        rendered_lines.append(rendered_line)

    # Join the criterion bullets into a prompt block.
    rendered_criteria = "\n".join(rendered_lines)
    return rendered_criteria


def _render_topic_definitions_block() -> str:
    """
    Description: Render topic definitions as a bullet list.

    Arguments: None.

    Returns:
        str: The rendered topic definitions block.
    """
    # Render each topic definition as a labeled bullet.
    rendered_lines = []
    for topic_label, topic_definition in TOPIC_DEFINITIONS.items():
        rendered_line = f"- {topic_label}: {topic_definition}"
        rendered_lines.append(rendered_line)

    # Join the topic bullets into a prompt block.
    rendered_definitions = "\n".join(rendered_lines)
    return rendered_definitions


def build_polish_prompt() -> str:
    """
    Description: Build the system prompt for polishing raw HR queries.

    Arguments: None.

    Returns:
        str: The polish system prompt.
    """
    # Render the shared polish criteria.
    rendered_criteria = _render_criteria_block()

    # Preserve the existing polish prompt wording.
    prompt = f"""You polish a raw HR user query for a question-answering pipeline.
Return ONLY JSON: {{"status": "ok" | "failed", "questions": ["..."]}}.
Apply these criteria:
{rendered_criteria}
"""
    return prompt


def build_polish_judge_prompt() -> str:
    """
    Description: Build the system prompt for judging polished HR queries.

    Arguments: None.

    Returns:
        str: The polish-judge system prompt.
    """
    # Render the shared polish criteria.
    rendered_criteria = _render_criteria_block()

    # Preserve the existing polish-judge prompt wording.
    prompt = f"""You are a strict judge of a polishing step.
You receive a raw query and the polishing output. Judge the output against these criteria:
{rendered_criteria}
Return ONLY JSON: {{"passed": true|false, "failed_criteria": ["<criterion_id>", ...], "feedback": "..."}}.
"passed" is true only if all criteria hold; otherwise list the failed IDs and give actionable feedback.
"""
    return prompt


def build_topic_prompt() -> str:
    """
    Description: Build the system prompt for classifying question topics.

    Arguments: None.

    Returns:
        str: The topic-classification system prompt.
    """
    # Render the allowed topics and their definitions.
    rendered_topic_definitions = _render_topic_definitions_block()

    # Preserve the existing topic prompt and add the definitions block.
    prompt = f"""You classify one HR question into a topic.
Return ONLY JSON: {{"topic": "<label>"}}.

Criteria:
T1: Output a single label.
T2: The label must come from the closed set above.
T3: If no topic fits, use "unidentified".
T4: The label must match the primary intent of the question.
Allowed labels and their definitions:
{rendered_topic_definitions}
"""
    return prompt


def build_topic_judge_prompt() -> str:
    """
    Description: Build the system prompt for judging topic classifications.

    Arguments: None.

    Returns:
        str: The topic-judge system prompt.
    """
    # Render the allowed topics and their definitions.
    rendered_topic_definitions = _render_topic_definitions_block()

    # Preserve the existing topic-judge prompt and add the definitions block.
    prompt = f"""You are a strict judge of a topic classification.
You receive a question, the allowed topics, and the assigned topic. Judge against:
    T1: A single label was assigned.
    T2: The label is in the allowed set.
    T3: "unidentified" is used when no topic fits (and only then).
    T4: The label matches the primary intent of the question.
    Allowed labels and their definitions:
    {rendered_topic_definitions}
Return ONLY JSON: {{"passed": true|false, "failed_criteria": ["T1", ...], "feedback": "..."}}.
"passed" is true only if all criteria hold; otherwise list the failed IDs and give actionable feedback.
"""
    return prompt


def build_speech_act_prompt() -> str:
    """
    Description: Build the system prompt for classifying speech acts.

    Arguments: None.

    Returns:
        str: The speech-act system prompt.
    """
    # Preserve the existing speech-act prompt wording.
    prompt = """You classify the speech act of one HR question.
Return ONLY JSON: {"speech_act": "<instruction|factual>"}.
- instruction: procedural / how-to question.
- factual: asks for a single fact, value, or a yes/no answer.

Criteria:
S1: Output a single value.
S2: The value must be "instruction" or "factual".
S3: Use "instruction" only when a step-by-step or list answer is natural.
"""
    return prompt


POLISH_SYSTEM = build_polish_prompt()
POLISH_JUDGE_SYSTEM = build_polish_judge_prompt()
TOPIC_SYSTEM = build_topic_prompt()
TOPIC_JUDGE_SYSTEM = build_topic_judge_prompt()
SPEECH_ACT_SYSTEM = build_speech_act_prompt()
