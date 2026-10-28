"""Polish, topic, and speech-act prompt data for question extraction."""

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

speech_act_single_label_criterion = (
    "S1",
    "Output a single value.",
)

speech_act_allowed_value_criterion = (
    "S2",
    'The value must be "instruction" or "factual".',
)

speech_act_definition_criterion = (
    "S3",
    'Use "instruction" only when a step-by-step or list answer is natural.',
)

SPEECH_ACT_PROMPT_CRITERIA = [
    speech_act_single_label_criterion,
    speech_act_allowed_value_criterion,
    speech_act_definition_criterion,
]

TOPIC_DEFINITIONS = {
    "vacation": "Vacation leave, paid time off, accrual, balances, carryover, scheduling, and payout.",
    "employee_change": "Changes to an employee's personal or employment records, role, payroll, or work arrangement.",
    "parental_leave": "Leave related to the birth or adoption of a child, including eligibility, duration, and pay.",
    "unidentified": "No allowed topic applies to the question.",
}

ALLOWED_TOPICS = list(TOPIC_DEFINITIONS.keys())
# "unverified" is used when the classifier could not produce a
# judge-approved label (parse failure or repeated judge rejection).
ALLOWED_SPEECH_ACTS = ["instruction", "factual", "unverified"]

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
