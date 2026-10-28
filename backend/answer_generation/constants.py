"""Answer-generation prompt data and constants."""

MIN_SIMILARITY = 0.5  # provisional; see experiments/calibrate_threshold.py - do not treat as final
TOP_K = 3
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
ANSWER_FAILURE_MESSAGE = "HRDocQA cannot provide an answer this time."

format_by_speech_act_criterion = (
    "A1 [rule]",
    'FORMAT BY SPEECH ACT — if speech_act is "instruction", the answer is a numbered or bulleted list of steps. If speech_act is "factual" or "unverified", the answer is one paragraph.',
)
supported_by_cited_chunks_criterion = (
    "A2 [judge]",
    "SUPPORTED BY CITED CHUNKS — every claim in the answer is supported by at least one chunk whose id appears in cited_chunk_ids.",
)
no_outside_facts_criterion = (
    "A3 [judge]",
    "NO OUTSIDE FACTS — the answer contains no facts not present in the cited chunks.",
)
citation_set_criterion = (
    "A4 [rule]",
    "CITATION SET — cited_chunk_ids is non-empty and is a subset of the retrieved chunk ids given in the prompt.",
)
no_pii_criterion = (
    "A5 [judge]",
    "NO PII — the answer contains no personal information (names, emails, phone numbers, employee IDs) beyond what is required to answer.",
)

ANSWER_PROMPT_CRITERIA = [
    format_by_speech_act_criterion,
    supported_by_cited_chunks_criterion,
    no_outside_facts_criterion,
    citation_set_criterion,
    no_pii_criterion,
]
