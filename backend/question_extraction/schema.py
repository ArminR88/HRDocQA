from typing import Literal, TypedDict

from pydantic import BaseModel, Field

TOPICS = ["vacation", "employee_change", "parental_leave", "unidentified"]
SPEECH_ACTS = ["instruction", "factual"]
FIXED_FAILURE_MESSAGE = "Sorry HRDocQA cannot polish the question."

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


class Question_Extraction_Judge_Output(BaseModel):
    """
    Description:
        Verdict returned by the question-extraction judges. Shared by the polish
        and topic judges; carries the pass flag, the failed criteria, and retry
        feedback.

    Arguments:
        passed (bool): true only when every criterion held.
        failed_criteria (list[str]): IDs of failed criteria (e.g. "P1", "T2");
            empty on pass.
        feedback (str): actionable instruction for the retry attempt.
    """
    passed: bool
    failed_criteria: list[str] = Field(default_factory=list)
    feedback: str = ""


class Topic_Speech_Act_Labeled(BaseModel):
    """
    Description:
        One polished question with its topic and speech-act labels. The unit
        produced by classify_node and stored in
        Question_Extraction_State.topic_speech_act_labeled.

    Arguments:
        question (str): the polished question text.
        topic (str): its topic label from ALLOWED_TOPICS.
        speech_act (str): its speech-act label, "instruction" or "factual".
    """
    question: str
    topic: str
    speech_act: str


class Question_Extraction_State(TypedDict, total=False):
    """
    Description:
        Shared graph state of the question-extraction subgraph. Accumulates the
        raw query, the polish stage's output, the classify stage's output, and
        an optional failure message.

    Arguments:
        raw_query (str): the original user input.
        polish_status (Literal["ok", "failed"]): set by the polish stage.
        polished_questions (list[str]): standalone questions produced by the
            polish stage.
        topic_speech_act_labeled (list[Topic_Speech_Act_Labeled]): classified
            questions produced by classify_node.
        final_message (str): fixed failure text, set only on the failure branch.
    """
    raw_query: str
    polish_status: Literal["ok", "failed"]
    polished_questions: list[str]
    topic_speech_act_labeled: list[Topic_Speech_Act_Labeled]
    final_message: str