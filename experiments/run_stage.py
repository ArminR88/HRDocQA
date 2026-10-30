import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

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


def stream_graph_with_timings(
    graph: Any,
    raw_query: str,
) -> tuple[dict[str, Any], dict[str, float]]:
    """
    Description:
        Stream the graph for one query and record elapsed time per node.

    Arguments:
        graph (Any): Compiled graph to run.
        raw_query (str): The raw query to process.

    Returns:
        tuple[dict[str, Any], dict[str, float]]: Final state and per-node
            timings in seconds.
    """
    # Record the start time and initialise the accumulators.
    timings = {}
    previous_time = time.perf_counter()
    state = {}
    # Stream node updates; measure the gap between consecutive events.
    for chunk in graph.stream({"raw_query": raw_query}, stream_mode="updates"):
        now = time.perf_counter()
        elapsed = now - previous_time
        for node_name in chunk:
            timings[node_name] = timings.get(node_name, 0.0) + elapsed
        previous_time = now
        for node_name, node_update in chunk.items():
            state.update(node_update)

    # Return the accumulated state and timings.
    return state, timings


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


def write_timing(path: Path, metadata: dict[str, Any]) -> None:
    """
    Description:
        Exclusively create a JSON timing file without overwriting existing data.

    Arguments:
        path (Path): Destination file path in an existing output directory.
        metadata (dict[str, Any]): Timing data written to the file.

    Returns:
        None: Writes the serialized timing record to path.
    """
    serialized = json.dumps(metadata, indent=2, ensure_ascii=False)
    with open(path, "x", encoding="utf-8") as timing_file:
        timing_file.write(f"{serialized}\n")


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


def _stage_totals(
    run_timings: dict[str, float],
    stage: str,
) -> tuple[dict[str, float], float]:
    """
    Description:
        Compute per-stage totals and the run total from per-node timings.

    Arguments:
        run_timings (dict[str, float]): Accumulated per-node seconds
            across all queries.
        stage (str): The `--stage` value that produced the run.

    Returns:
        tuple[dict[str, float], float]: Stage totals in seconds, and the
            run total in seconds.
    """
    stage_totals = {}
    if stage == "question_cleaning":
        total_seconds = 0.0
        for node_name in run_timings:
            total_seconds = total_seconds + run_timings[node_name]
        stage_totals["question_extraction"] = round(total_seconds, 2)
        return stage_totals, round(total_seconds, 2)

    question_extraction_seconds = run_timings.get("question_extraction", 0.0)
    answer_generation_seconds = 0.0
    for node_name in ("retrieval", "answer", "no_match", "join", "failure"):
        answer_generation_seconds = answer_generation_seconds + run_timings.get(node_name, 0.0)
    stage_totals["question_extraction"] = round(question_extraction_seconds, 2)
    stage_totals["answer_generation"] = round(answer_generation_seconds, 2)
    total_seconds = question_extraction_seconds + answer_generation_seconds
    return stage_totals, round(total_seconds, 2)


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
    result_metadata = {}
    result_metadata["timestamp"] = timestamp
    result_metadata["stage"] = args.stage
    result_metadata["query_ids"] = []
    for query in queries:
        result_metadata["query_ids"].append(query["id"])

    timing_metadata = {}
    timing_metadata["metadata"] = {}
    timing_metadata["metadata"]["timestamp"] = timestamp
    timing_metadata["metadata"]["stage"] = args.stage
    timing_metadata["metadata"]["query_ids"] = []
    for query in queries:
        timing_metadata["metadata"]["query_ids"].append(query["id"])

    query_timings = []
    extraction_records = []
    answer_records = []
    if args.stage == "question_cleaning":
        graph = build_extraction_graph()
    else:
        graph = build_answer_graph()

    for query in queries:
        state, timings = stream_graph_with_timings(graph, query["raw_query"])

        entry = {}
        entry["query_id"] = query["id"]
        for node_name, seconds in timings.items():
            entry[node_name] = round(seconds, 2)
        query_timings.append(entry)

        extraction_record = _extraction_record(query, state)
        extraction_records.append(extraction_record)
        if args.stage != "question_cleaning":
            answer_record = dict(extraction_record)
            answer_record["answer_results"] = _json_value(state.get("answer_results", []))
            answer_record["no_match_results"] = _json_value(state.get("no_match_results", []))
            answer_record["final_message"] = state.get("final_message")
            answer_record["topic_speech_act_labeled"] = _json_value(state.get("topic_speech_act_labeled", []))
            answer_records.append(answer_record)

    run_timings = {}
    for entry in query_timings:
        for node_name, seconds in entry.items():
            if node_name == "query_id":
                continue
            run_timings[node_name] = run_timings.get(node_name, 0.0) + seconds

    timing_metadata["query_timings_seconds"] = query_timings
    timing_metadata["totals_seconds"] = {}
    for node_name, seconds in run_timings.items():
        timing_metadata["totals_seconds"][node_name] = round(seconds, 2)
    stage_totals, total_seconds = _stage_totals(run_timings, args.stage)
    timing_metadata["stage_totals_seconds"] = stage_totals
    timing_metadata["total_seconds"] = total_seconds

    if args.stage == "question_cleaning":
        result_path = QUESTION_CLEANING_DIR / f"run_{timestamp}.json"
        timing_path = QUESTION_CLEANING_DIR / f"run_{timestamp}_timing.json"
        write_results(result_path, extraction_records, result_metadata)
        write_timing(timing_path, timing_metadata)
    elif args.stage == "answer_generation":
        result_path = ANSWER_GENERATION_DIR / f"run_{timestamp}.json"
        timing_path = ANSWER_GENERATION_DIR / f"run_{timestamp}_timing.json"
        write_results(result_path, answer_records, result_metadata)
        write_timing(timing_path, timing_metadata)
    else:
        extraction_result_path = QUESTION_CLEANING_DIR / f"run_{timestamp}_from_both.json"
        extraction_timing_path = QUESTION_CLEANING_DIR / f"run_{timestamp}_from_both_timing.json"
        answer_result_path = ANSWER_GENERATION_DIR / f"run_{timestamp}_from_both.json"
        answer_timing_path = ANSWER_GENERATION_DIR / f"run_{timestamp}_from_both_timing.json"
        write_results(extraction_result_path, extraction_records, result_metadata)
        write_timing(extraction_timing_path, timing_metadata)
        write_results(answer_result_path, answer_records, result_metadata)
        write_timing(answer_timing_path, timing_metadata)


if __name__ == "__main__":
    main()
