from typing import Literal, TypedDict

from pydantic import BaseModel, Field

TOPICS = ["vacation", "employee_change", "parental_leave", "unidentified"]
SPEECH_ACTS = ["instruction", "factual"]
FIXED_FAILURE_MESSAGE = "Sorry HRDocQA cannot polish the question."


class PolishedOutput(BaseModel):
    status: Literal["ok", "failed"]
    questions: list[str] = Field(default_factory=list)


class TopicOutput(BaseModel):
    topic: str


class SpeechActOutput(BaseModel):
    speech_act: str


class JudgeVerdict(BaseModel):
    passed: bool
    failed_criteria: list[str] = Field(default_factory=list)
    feedback: str = ""


class AnalyzedQuestion(BaseModel):
    text: str
    topic: str
    speech_act: str


class PipelineState(TypedDict, total=False):
    raw_query: str
    polish_status: Literal["ok", "failed"]
    polished_questions: list[str]
    analyzed: list[AnalyzedQuestion]
    final_message: str
