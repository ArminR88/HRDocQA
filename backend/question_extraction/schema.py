from typing import Literal, TypedDict

from pydantic import BaseModel, Field

from backend.shared.schema import Topic_Speech_Act_Labeled


class Polished_Questions(BaseModel):
    """
    Description:
        Output of the polish stage. Holds the success flag and the standalone
        questions produced from the raw query.

    Arguments:
        status (Literal["ok", "failed"]): "ok" when polishing produced usable
            questions, "failed" otherwise.
        questions (list[str]): standalone polished questions; empty when
            status is "failed".
    """
    status: Literal["ok", "failed"]
    questions: list[str] = Field(default_factory=list)


class Topic_Classification(BaseModel):
    """
    Description:
        Output of the topic labeler for one polished question. Carries the
        single topic label assigned to a question.

    Arguments:
        topic (str): one label from ALLOWED_TOPICS; "unidentified" when none fits.
    """
    topic: str


class Speech_Act_Classification(BaseModel):
    """
    Description:
        Output of the speech-act labeler for one polished question. Carries the
        single speech-act label assigned to a question.

    Arguments:
        speech_act (str): "instruction" for procedural/how-to, "factual" for
            a single fact, value, or yes/no answer.
    """
    speech_act: str


class Question_Extraction_State(TypedDict, total=False):
    """
    Description:
        Shared graph state of the question-extraction subgraph. Accumulates the
        raw query, the polish stage's output, parallel topic and speech-act
        labels consumed by the join node, joined labels, and an optional
        failure message.

    Arguments:
        raw_query (str): the original user input.
        polish_status (Literal["ok", "failed"]): set by the polish stage.
        polished_questions (list[str]): standalone questions produced by the
            polish stage.
        topic_labels (list[str]): topic labels produced by the topic classify
            node and consumed by the join node.
        speech_act_labels (list[str]): speech-act labels produced by the
            speech-act classify node and consumed by the join node.
        topic_speech_act_labeled (list[Topic_Speech_Act_Labeled]): classified
            questions produced by the join node.
        final_message (str): fixed failure text, set only on the failure branch.
    """
    raw_query: str
    polish_status: Literal["ok", "failed"]
    polished_questions: list[str]
    topic_labels: list[str]
    speech_act_labels: list[str]
    topic_speech_act_labeled: list[Topic_Speech_Act_Labeled]
    final_message: str