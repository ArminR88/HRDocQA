from pydantic import BaseModel, Field


class Judge_Output(BaseModel):
    """
    Description:
        Verdict returned by the judges. Shared by the polish, topic, and
        speech-act judges in extraction and by the answer judge; carries the
        pass flag, the failed criteria, and retry feedback.

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
        produced by join_labels_node and stored in
        Question_Extraction_State.topic_speech_act_labeled.

    Arguments:
        question (str): the polished question text.
        topic (str): its topic label from ALLOWED_TOPICS.
        speech_act (str): its speech-act label, "instruction" or "factual".
    """
    question: str
    topic: str
    speech_act: str
