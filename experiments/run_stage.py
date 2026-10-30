import argparse
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, NoReturn

from backend.answer_generation import build_answer_graph
from backend.question_extraction import build_extraction_graph


ROOT = Path(__file__).resolve().parent.parent
QUERY_PATH = ROOT / "experiments" / "test_queries" / "experiment_queries.json"
QUESTION_CLEANING_DIR = ROOT / "experiments" / "question_cleaning_exp_results"
ANSWER_GENERATION_DIR = ROOT / "experiments" / "answer_generation_exp_results"


def _json_value(value: Any) -> Any:
    """
    Description:
        Convert graph output values into JSON-serializable Python values.

    Arguments:
        value (Any): A graph state value, including nested model instances.

    Returns:
        Any: The value represented using dictionaries and JSON-compatible values.
    """
    # Convert Pydantic models to dicts; other values pass through.
    if hasattr(value, "model_dump"):
        model_value = value.model_dump(mode="json")
        return model_value
    return value


def _extraction_record(query: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """
    Description:
        Build the extraction-stage record for one query.

    Arguments:
        query (dict[str, Any]): Input query record with id and raw_query.
        state (dict[str, Any]): Extraction or answer graph state.

    Returns:
        dict[str, Any]: Record of extraction outputs for the query.
    """
    labeled_questions = state.get("topic_speech_act_labeled", [])
    labeled_records = []
    topic_labels = []
    speech_act_labels = []
    for item in labeled_questions:
        labeled_item = _json_value(item)
        labeled_record = {}
        labeled_record["question"] = labeled_item["question"]
        labeled_record["topic"] = labeled_item["topic"]
        labeled_record["speech_act"] = labeled_item["speech_act"]
        labeled_records.append(labeled_record)
        topic_labels.append(labeled_record["topic"])
        speech_act_labels.append(labeled_record["speech_act"])

    record = {}
    record["id"] = query["id"]
    record["raw_query"] = query["raw_query"]
    record["polish_status"] = state.get("polish_status")
    record["polished_questions"] = _json_value(state.get("polished_questions", []))
    record["topic_labels"] = topic_labels
    record["speech_act_labels"] = speech_act_labels
    record["topic_speech_act_labeled"] = labeled_records
    return record


def _report_query_error(query_id: Any) -> NoReturn:
    """
    Description:
        Print the active query id and traceback after a graph invocation fails.

    Arguments:
        query_id (Any): Id of the query whose graph invocation failed.

    Returns:
        None: Exits with a failure status after printing the traceback.
    """
    print(f"Query {query_id} failed; stopping the run.", file=sys.stderr)
    traceback.print_exc()
    raise SystemExit(1)


def run_question_cleaning(queries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Description:
        Run only the extraction graph for each supplied query.

    Arguments:
        queries (list[dict[str, Any]]): Query records to process.

    Returns:
        list[dict[str, Any]]: Extraction records in query order.
    """
    graph = build_extraction_graph()
    records = []
    for query in queries:
        query_id = query["id"]
        raw_query = query["raw_query"]
        try:
            state = graph.invoke({"raw_query": raw_query})
        except Exception:
            _report_query_error(query_id)
        record = _extraction_record(query, state)
        records.append(record)
    return records


def run_answer_generation(
    queries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Description:
        Run the answer graph once for each supplied query.

    Arguments:
        queries (list[dict[str, Any]]): Query records to process.

    Returns:
        tuple[list[dict[str, Any]], list[dict[str, Any]]]: Extraction records
            and full answer-generation records, in query order.
    """
    graph = build_answer_graph()
    extraction_records = []
    answer_records = []
    for query in queries:
        query_id = query["id"]
        raw_query = query["raw_query"]
        try:
            state = graph.invoke({"raw_query": raw_query})
        except Exception:
            _report_query_error(query_id)
        extraction_record = _extraction_record(query, state)
        extraction_records.append(extraction_record)

        answer_record = dict(extraction_record)
        answer_record["answer_results"] = _json_value(state.get("answer_results", []))
        answer_record["no_match_results"] = _json_value(state.get("no_match_results", []))
        answer_record["final_message"] = state.get("final_message")
        answer_record["topic_speech_act_labeled"] = _json_value(
            state.get("topic_speech_act_labeled", [])
        )
        answer_records.append(answer_record)
    return extraction_records, answer_records


def write_results(path: Path, records: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    """
    Description:
        Exclusively create a JSON result file without overwriting existing data.

    Arguments:
        path (Path): Destination file path in an existing output directory.
        records (list[dict[str, Any]]): Result records to write.
        metadata (dict[str, Any]): Run metadata written alongside the records.

    Returns:
        None: Writes the serialized result to path.
    """
    output = {}
    output["metadata"] = metadata
    output["results"] = records
    serialized = json.dumps(output, indent=2, ensure_ascii=False)
    with open(path, "x", encoding="utf-8") as result_file:
        result_file.write(f"{serialized}\n")


def _parse_query_ids(value: str) -> list[str]:
    """
    Description:
        Parse a comma-separated query-id option.

    Arguments:
        value (str): Comma-separated ids supplied to --query-ids.

    Returns:
        list[str]: Non-empty ids in their original order.
    """
    query_ids = []
    for item in value.split(","):
        query_id = item.strip()
        if query_id == "":
            raise argparse.ArgumentTypeError("--query-ids must contain comma-separated ids")
        query_ids.append(query_id)
    return query_ids


def main() -> None:
    """
    Description:
        Load selected queries, dispatch the requested pipeline stage, and save results.

    Arguments:
        None.

    Returns:
        None: Writes stage result files or exits with an explicit error.
    """
    parser = argparse.ArgumentParser(description="Run an HRDocQA experiment stage.")
    parser.add_argument(
        "--stage",
        choices=["question_cleaning", "answer_generation", "both"],
        default="question_cleaning",
    )
    parser.add_argument(
        "--query-ids",
        type=_parse_query_ids,
        help="Comma-separated query ids; defaults to all queries.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable INFO logging to capture [timing] lines.")
    args = parser.parse_args()
    if args.verbose == True:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING, format="%(asctime)s | %(levelname)s | %(message)s")

    all_queries = json.loads(QUERY_PATH.read_text(encoding="utf-8"))

    if args.query_ids is None:
        queries = all_queries
    else:
        queries = []
        for query in all_queries:
            if str(query["id"]) in args.query_ids:
                queries.append(query)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    metadata = {}
    metadata["timestamp"] = timestamp
    metadata["stage"] = args.stage
    metadata["query_ids"] = []
    for query in queries:
        metadata["query_ids"].append(query["id"])

    if args.stage == "question_cleaning":
        records = run_question_cleaning(queries)
        path = QUESTION_CLEANING_DIR / f"run_{timestamp}.json"
        write_results(path, records, metadata)
    elif args.stage == "answer_generation":
        answer_records = run_answer_generation(queries)[1]
        path = ANSWER_GENERATION_DIR / f"run_{timestamp}.json"
        write_results(path, answer_records, metadata)
    else:
        extraction_path = QUESTION_CLEANING_DIR / f"run_{timestamp}_from_both.json"
        answer_path = ANSWER_GENERATION_DIR / f"run_{timestamp}_from_both.json"
        extraction_records, answer_records = run_answer_generation(queries)
        write_results(extraction_path, extraction_records, metadata)
        write_results(answer_path, answer_records, metadata)


if __name__ == "__main__":
    main()
