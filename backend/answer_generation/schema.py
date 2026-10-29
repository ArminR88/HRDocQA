"""Answer-generation schemas; constants live in constants.py."""

from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from backend.shared.schema import Topic_Speech_Act_Labeled


class Retrieval_Chunk(BaseModel):
    """
    Description:
        One knowledge-base chunk returned by retrieval.

    Arguments:
        chunk_id (str): Stable identifier of the retrieved chunk.
        file (str): Source file for the chunk.
        text (str): Text content of the chunk.
        score (float): Similarity score between the query and the chunk.
    """
    chunk_id: str
    file: str
    text: str
    score: float


class Cited_Answer(BaseModel):
    """
    Description:
        Generated answer and the identifiers of its cited chunks.

    Arguments:
        answer (str): The generated response.
        cited_chunk_ids (list[str]): Identifiers of chunks cited by the answer.
    """
    answer: str
    cited_chunk_ids: list[str]


class Answer_Record(BaseModel):
    """
    Description:
        Complete record of one question and its answer-generation results.

    Arguments:
        question (str): The question being answered.
        topic (str): Topic label assigned to the question.
        speech_act (str): Speech-act label assigned to the question.
        question_index (int): Position of the question in the input.
        retrieved_chunks (list[Retrieval_Chunk]): Chunks found for the question.
        answer (str): Generated answer text.
        cited_chunk_ids (list[str]): Identifiers of chunks cited by the answer.
        sources (list[Retrieval_Chunk]): Retrieved chunks cited as sources.
        case (str): Outcome of answer generation.
    """
    question: str = ""
    topic: str = ""
    speech_act: str = ""
    question_index: int = 0
    retrieved_chunks: list[Retrieval_Chunk] = Field(default_factory=list)
    answer: str = ""
    cited_chunk_ids: list[str] = Field(default_factory=list)
    sources: list[Retrieval_Chunk] = Field(default_factory=list)
    case: str = ""


class Answer_State(TypedDict, total=False):
    """
    Description:
        Shared graph state for answer generation, including analysis,
        retrieval, answer, and no-match results.

    Arguments:
        raw_query (str): The original user input.
        polish_status (Literal["ok", "failed"]): Result of query polishing.
        polished_questions (list[str]): Standalone questions from polishing.
        topic_speech_act_labeled (list[Topic_Speech_Act_Labeled]): Questions
            labeled with topic and speech act.
        final_message (str): User-facing result or failure message.
        answer_results (list[Answer_Record]): Results for answered questions.
        no_match_results (list[Answer_Record]): Results for questions without
            matching retrieval evidence.
    """
    raw_query: str
    polish_status: Literal["ok", "failed"]
    polished_questions: list[str]
    topic_speech_act_labeled: list[Topic_Speech_Act_Labeled]
    final_message: str
    answer_results: list[Answer_Record]
    no_match_results: list[Answer_Record]
