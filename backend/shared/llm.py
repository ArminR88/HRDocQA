import json
import os
from dataclasses import dataclass
from typing import Type, TypeVar

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

T = TypeVar("T", bound=BaseModel)

@dataclass(frozen=True)
class LLM_Config:
    """
    Description: Configuration for an LLM provider.

    Arguments:
        base_url (str): API base URL for the OpenAI-compatible client.
        model (str): Model name to send in each request.
        temperature (float): Sampling temperature.
        api_key_env (str): Name of the environment variable holding the
            API key.
    """
    base_url: str
    model: str
    temperature: float
    api_key_env: str


DEEPSEEK_FLASH = LLM_Config(
    base_url="https://api.deepseek.com",
    model="deepseek-flash",
    temperature=0,
    api_key_env="DEEPSEEK_API_KEY",
)

ACTIVE_CONFIG = DEEPSEEK_FLASH


def _call_llm_returning_json(
    system: str,
    user: str,
    config: LLM_Config = ACTIVE_CONFIG,
) -> str:
    """
    Description: Call the active LLM provider and return the raw JSON response.

    Arguments:
        system (str): System prompt.
        user (str): User message.
        config (LLM_Config): Active provider configuration.

    Returns:
        str: Raw JSON string returned by the model.

    Example:
        >>> _call_llm_returning_json("Return JSON.", '{"q": "hi"}')
        '{"ok": true}'
    """
    api_key = os.environ.get(config.api_key_env)
    client = OpenAI(base_url=config.base_url, api_key=api_key)
    system_message = {"role": "system", "content": system}
    user_message = {"role": "user", "content": user}
    messages = [system_message, user_message]
    # DeepSeek accepts JSON-object mode; schema enforcement is deferred
    # until a native provider path is added.
    response_format = {"type": "json_object"}
    completions = client.chat.completions
    response = completions.create(
        model=config.model,
        temperature=config.temperature,
        response_format=response_format,
        messages=messages,
    )
    choice = response.choices[0]
    message = choice.message
    content = message.content
    return content


def _parse_json_into_pydantic_instance(raw: str, schema: Type[T]) -> T:
    """
    Description: Parse a JSON string into an instance of the given Pydantic schema.

    Arguments:
        raw (str): JSON text.
        schema (Type[T]): Pydantic model class to validate against.

    Returns:
        T: Instance of the given schema.

    Example:
        >>> _parse_json_into_pydantic_instance('{"topic": "vacation"}', Topic_Classification)
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
