english_criterion = (
    "english",
    "Write each question in English. Keep non-English names, system names, legal terms, and user-provided values unchanged when translating them would lose meaning.",
)

keep_operational_details_criterion = (
    "keep_operational_details",
    "Remove greetings, signatures, emotional language, and direct personal identifiers, including names, email addresses, phone numbers, and employee IDs. Preserve non-identifying operational context within the request's scope (i.e., context the user explicitly included as part of the request, such as role, employment status, eligibility, deadlines, relevant dates, location scope, codes, and system state; not context the model infers is relevant). Do not remove an operational fact explicitly provided in the request merely because it could be sensitive.",
)

remove_filler_criterion = (
    "remove_filler",
    "Remove filler, repetition, and irrelevant template text. Preserve concrete constraints and evidence that affect execution or interpretation.",
)

preserve_intent_criterion = (
    "preserve_intent",
    "Preserve the original actionable intent and target. Rewrite only for clarity. Resolve pronouns and references so each question stands alone. Preserve whether the user is requesting an action or seeking information; do not change one into the other.",
)

merge_or_split_criterion = (
    "merge_or_split",
    "(a) Merge near-duplicate asks that share the same target and information need. Treat a hypothesis followed by a corrective rephrase of the same target (e.g. 'Is it X? If not, what is it?') as one ask. (b) Split asks that seek distinct outcomes or answers, even when connected by 'if not' (e.g. 'Can I carry over vacation? If not, can I cash it out?'). (c) After checking (a) and (b), if unsure whether two asks share the same information need, keep them separate. Copy only the specific context required to make each split question standalone; do not duplicate preamble that is not needed to answer that specific question. (d) Never split obvious paraphrases. Each item must represent exactly one ask. Never invent asks.",
)

output_contract_criterion = (
    "output_contract",
    "Return valid JSON with keys status and questions. If status is 'ok', questions must be a non-empty list of non-empty, grammatical, meaningful, standalone strings. If the input contains no actionable request or policy question, return {\"status\": \"failed\", \"questions\": []}. Keep each question concise but complete, preserving all context needed for independent retrieval and answering.",
)

precedence_criterion = (
    "precedence",
    "If criteria conflict, apply this order: (1) preserve intent, (2) remove direct personal identifiers according to keep_operational_details, (3) preserve necessary operational details, (4) satisfy the output contract, (5) optimize style and readability. Minimize retained personal data without sacrificing the intent or necessary non-identifying context.",
)

POLISH_PROMPT_CRITERIA = [
    english_criterion,
    keep_operational_details_criterion,
    remove_filler_criterion,
    preserve_intent_criterion,
    merge_or_split_criterion,
    output_contract_criterion,
    precedence_criterion,
]


def _render_criteria(criteria: list[tuple[str, str]]) -> str:
    return "\n".join(f"- {criterion_id}: {criterion_text}" for criterion_id, criterion_text in criteria)


POLISH_SYSTEM_TEMPLATE = """You polish a raw HR user query for a question-answering pipeline.
Return ONLY JSON: {{"status": "ok" | "failed", "questions": ["..."]}}.
Apply these criteria:
{criteria}
"""

POLISH_SYSTEM = POLISH_SYSTEM_TEMPLATE.format(
    criteria=_render_criteria(POLISH_PROMPT_CRITERIA)
)


POLISH_JUDGE_SYSTEM_TEMPLATE = """You are a strict judge of a polishing step.
You receive a raw query and the polishing output. Judge the output against these criteria:
{criteria}
Return ONLY JSON: {{"passed": true|false, "failed_criteria": ["<criterion_id>", ...], "feedback": "..."}}.
"passed" is true only if all criteria hold; otherwise list the failed IDs and give actionable feedback.
"""

POLISH_JUDGE_SYSTEM = POLISH_JUDGE_SYSTEM_TEMPLATE.format(
    criteria=_render_criteria(POLISH_PROMPT_CRITERIA)
)


POLISH_DESIGN_NOTES = """Privacy: This version prioritizes privacy without an authorization mechanism. If downstream requires employee-specific lookup using identifiers, that must be handled by system design, not inferred by the polishing model.

Pipeline assumption: This prompt assumes the downstream retriever tolerates repeated shared context across independent questions. If it requires reference-by-index or strictly non-redundant payloads, schema changes must be made at the orchestrator layer, not in this prompt."""


POLISH_TEST_GATE_SPEC = """1. Segmentation Gate:
   - Initial Gate: minimum 100 queries (50 same-target, 50 different-target). Requires >= 90% exact agreement per category with adjudicated human labels.
   - Continuous Expansion: add verified production segmentation failures to the test set continuously.
   - Retesting: evaluate prompt adjustments on the full expanded dataset.

2. Speech-Act Form Preservation Gate:
   - Pass threshold: 100% form preservation on the action-vs-information axis (zero conversions permitted).
   - Operational requests (action asks) must remain action requests; information-seeking requests must remain question forms, across all items in the test set.
   - Exclusion: queries where human reviewers disagree on the correct form are excluded from the gate before scoring; the 100% applies to adjudicated cases only.

3. Evaluation set: both gates use the same held-out set; each query is scored under both gates."""


TOPIC_SYSTEM = """You classify one HR question into a topic.
Return ONLY JSON: {"topic": "<label>"}.
Allowed labels: vacation, employee_change, parental_leave, unidentified.

Criteria:
T1: Output a single label.
T2: The label must come from the closed set above.
T3: If no topic fits, use "unidentified".
T4: The label must match the primary intent of the question.
"""

SPEECH_ACT_SYSTEM = """You classify the speech act of one HR question.
Return ONLY JSON: {"speech_act": "<instruction|factual>"}.
- instruction: procedural / how-to question.
- factual: asks for a single fact, value, or a yes/no answer.

Criteria:
S1: Output a single value.
S2: The value must be "instruction" or "factual".
S3: Use "instruction" only when a step-by-step or list answer is natural.
"""


TOPIC_JUDGE_SYSTEM = """You are a strict judge of a topic classification.
You receive a question, the allowed topics, and the assigned topic. Judge against:
T1: A single label was assigned.
T2: The label is in the allowed set.
T3: "unidentified" is used when no topic fits (and only then).
T4: The label matches the primary intent of the question.
Return ONLY JSON: {"passed": true|false, "failed_criteria": ["T1", ...], "feedback": "..."}.
"passed" is true only if all criteria hold; otherwise list the failed IDs and give actionable feedback.
"""
