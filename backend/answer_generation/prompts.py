"""Build answer-generation prompts from centralized prompt data."""

from .constants import ANSWER_PROMPT_CRITERIA


def _render_criteria_block() -> str:
    """
    Description: Render answer criteria as a bullet list.

    Arguments: None.

    Returns:
        str: The rendered answer criteria block.
    """
    # Render each criterion as a labeled bullet.
    rendered_lines = []
    for criterion_id, criterion_text in ANSWER_PROMPT_CRITERIA:
        rendered_line = f"- {criterion_id}: {criterion_text}"
        rendered_lines.append(rendered_line)

    # Join the criterion bullets into a prompt block.
    rendered_criteria = "\n".join(rendered_lines)
    return rendered_criteria


def build_answer_prompt() -> str:
    """
    Description: Build the system prompt for answering HR questions.

    Arguments: None.

    Returns:
        str: The answer-generation system prompt.
    """
    # Render the shared answer criteria.
    rendered_criteria = _render_criteria_block()

    # Restore the original criteria formatting.
    criteria_without_bullets = rendered_criteria.replace("- ", "")
    prompt_criteria = criteria_without_bullets.replace(": ", " ")

    # Preserve the existing answer prompt wording.
    prompt = f"""You answer HR questions only from the retrieved chunks supplied in the user message.
Return ONLY JSON with this shape: {{"answer": "...", "cited_chunk_ids": ["..."]}}.

Criteria:
{prompt_criteria}
"""
    return prompt


def build_answer_judge_prompt() -> str:
    """
    Description: Build the system prompt for judging generated answers.

    Arguments: None.

    Returns:
        str: The answer-judge system prompt.
    """
    # Render the shared answer criteria.
    rendered_criteria = _render_criteria_block()

    # Restore the original criteria formatting.
    criteria_without_bullets = rendered_criteria.replace("- ", "")
    prompt_criteria = criteria_without_bullets.replace(": ", " ")

    # Preserve the existing answer-judge prompt wording.
    prompt = f"""You are a strict judge of an HR answer.
You receive the question, speech_act, retrieved chunks, produced answer, and cited_chunk_ids.
Judge the answer against these criteria:
{prompt_criteria}
Return ONLY JSON: {{"passed": true|false, "failed_criteria": ["A1", ...], "feedback": "..."}}.
"passed" is true only if all criteria hold; otherwise list every failed criterion ID and give actionable feedback.
"""
    return prompt


# Build the prompts once at module import.
ANSWER_SYSTEM = build_answer_prompt()
ANSWER_JUDGE_SYSTEM = build_answer_judge_prompt()
