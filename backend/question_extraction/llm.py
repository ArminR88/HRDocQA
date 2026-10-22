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


def call_with_retry(
    primary_system: str,
    judge_system: str,
    user_builder: Callable[[str | None], str],
    judge_input_builder: Callable[[T], str],
    primary_schema: Type[T],
    max_attempts: int = 3,
) -> tuple[T | None, bool]:
    """
    Call a primary prompt and judge each result, retrying with judge feedback.

    Arguments:
        primary_system (str): System prompt of the primary call.
        judge_system (str): System prompt of the judge call.
        user_builder (Callable[[str | None], str]): Builds the primary user
            message from feedback. Receives None on the first attempt and, on
            retries, a string with the judge's failed criteria and feedback.
        judge_input_builder (Callable[[T], str]): Builds the judge user message
            from the parsed primary output.
        primary_schema (Type[T]): Pydantic model the primary output is parsed into.
        max_attempts (int): Maximum number of primary attempts.

    Returns:
        tuple[T | None, bool]: (output, True) on the first judged pass,
            otherwise (last_output, False) after max_attempts attempts.

    Example:
        >>> call_with_retry(TOPIC_SYSTEM, TOPIC_JUDGE_SYSTEM, build_user, build_judge, Topic_Classification)
        (Topic_Classification(topic='vacation'), True)
    """
    feedback = None
    for _ in range(max_attempts):
        user = user_builder(feedback)
        raw = _call(primary_system, user)
        output = _parse(raw, primary_schema)
        judge_input = judge_input_builder(output)
        judge_raw = _call(judge_system, judge_input)
        verdict = _parse(judge_raw, Question_Extraction_Judge_Output)
        if verdict.passed:
            passed_result = (output, True)
            return passed_result
        feedback = _format_feedback(verdict.failed_criteria, verdict.feedback)
    failed_result = (output, False)
    return failed_result
