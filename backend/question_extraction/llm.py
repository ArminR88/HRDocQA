import json
import os
from typing import Callable, Type, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from .schema import Question_Extraction_Judge_Output

load_dotenv()

T = TypeVar("T", bound=BaseModel)

MODEL = "deepseek-flash"
BASE_URL = "https://api.deepseek.com"
TEMPERATURE = 0
def _call(system: str, user: str, model: str = MODEL) -> str:
    """
    Run a single JSON-mode chat completion.

    Arguments:
        system (str): System prompt.
        user (str): User message.
        model (str): DeepSeek model name.

    Returns:
        str: Raw JSON string returned by the model.

    Example:
        >>> _call("Return JSON.", '{"q": "hi"}')
        '{"ok": true}'
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    client = OpenAI(base_url=BASE_URL, api_key=api_key)
    system_message = {"role": "system", "content": system}
    user_message = {"role": "user", "content": user}
    messages = [system_message, user_message]
    response_format = {"type": "json_object"}
    completions = client.chat.completions
    response = completions.create(
        model=model,
        temperature=TEMPERATURE,
        response_format=response_format,
        messages=messages,
    )
    choice = response.choices[0]
    message = choice.message
    content = message.content
    return content


def _parse(raw: str, schema: Type[T]) -> T:
    """
    Parse a JSON string into a Pydantic model.

    Arguments:
        raw (str): JSON text.
        schema (Type[T]): Pydantic model class to validate against.

    Returns:
        T: Instance of the given schema.

    Example:
        >>> _parse('{"topic": "vacation"}', Topic_Classification)
        Topic_Classification(topic='vacation')
    """
    data = json.loads(raw)
    parsed = schema.model_validate(data)
    return parsed


def _format_feedback(failed_criteria: list[str], feedback: str) -> str:
    """
    Format judge results as a retry instruction.

    Arguments:
        failed_criteria (list[str]): IDs of the failed criteria.
        feedback (str): Judge feedback text.

    Returns:
        str: Text appended to the next attempt's user message.

    Example:
        >>> _format_feedback(["P1"], "Use English.")
        'Your previous attempt failed criteria: P1.\\nFeedback: Use English.\\nFix these issues.'
    """
    criteria = ", ".join(failed_criteria)
    text = (
        f"Your previous attempt failed criteria: {criteria}.\n"
        f"Feedback: {feedback}\n"
        f"Fix these issues."
    )
    return text


def _prepend_heading_to_question(
    heading: str,
    question: str,
    retry_feedback: str | None,
) -> str:
    """
    Prepend a heading to a question, appending retry feedback when present.

    Arguments:
        heading (str): Heading placed above the question, e.g. "Raw query".
        question (str): The user question to send, raw or polished.
        retry_feedback (str | None): None on the first attempt, else the
            judge feedback to append.

    Returns:
        str: User message.

    Example:
        >>> _prepend_heading_to_question("Raw query", "hi i wanna know abt parental leave n how many wks r paid?? also can i split it", None)
        'Raw query:\\nhi i wanna know abt parental leave n how many wks r paid?? also can i split it'

        >>> _prepend_heading_to_question("Question", "How many weeks of parental leave are paid?", "Fix P1.")
        'Question:\\nHow many weeks of parental leave are paid?\\n\\nFix P1.'

        >>> _prepend_heading_to_question("", '{"question": "Is leave paid?"}', None)
        '{"question": "Is leave paid?"}'
    """
    # Add a heading when one is provided.
    if heading == "":
        headed_question = question
    else:
        headed_question = f"{heading}:\n{question}"

    # Return the headed question when there is no retry feedback.
    if retry_feedback is None:
        return headed_question

    # Append retry feedback after a blank line.
    user_message = f"{headed_question}\n\n{retry_feedback}"
    return user_message


def call_with_retry(
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
        >>> call_with_retry(
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
