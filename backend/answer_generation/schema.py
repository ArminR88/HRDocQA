from typing import Any, TypedDict

from pydantic import BaseModel

MIN_SIMILARITY = 0.5  # provisional; see experiments/calibrate_threshold.py - do not treat as final
TOP_K = 3
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
ANSWER_FAILURE_MESSAGE = "HRDocQA cannot provide an answer this time."


class RetrievedChunk(BaseModel):
    chunk_id: str
    file: str
    text: str
    score: float


class CitedAnswer(BaseModel):
    answer: str
    cited_chunk_ids: list[str]


class AnswerVerdict(BaseModel):
    passed: bool
    failed_criteria: list[str]
    feedback: str


class AnswerState(TypedDict, total=False):
    raw_query: str
    polish_status: str
    polished_questions: list[str]
    analyzed: list[dict[str, Any]]
    final_message: str
    answer_results: list[dict[str, Any]]
    no_match_results: list[dict[str, Any]]
