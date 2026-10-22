import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.question_extraction import build_extraction_graph
from backend.question_extraction.llm import MODEL

ROOT = Path(__file__).resolve().parent.parent
QUERY_PATH = ROOT / "experiments" / "experiment_queries.json"
RESULT_PATH = ROOT / "experiments" / "experiment_results.json"
MAX_ATTEMPTS = 3
EXPERIMENT_NAME = "baseline_v1"


def _run_query(graph: Any, query: dict[str, Any]) -> dict[str, Any]:
    """
    Invoke the graph once and record its output or raised exception.

    Arguments:
        graph (Any): Compiled HR analysis graph.
        query (dict[str, Any]): Query record with id and raw_query.

    Returns:
        dict[str, Any]: Result row with the experiment output or error.

    Example:
        >>> _run_query(graph, {"id": 1, "raw_query": "How many vacation days do I have?"})
        {"id": 1, "raw_query": "...", "polish_status": "ok", ...}
    """
    query_id = query["id"]
    raw_query = query["raw_query"]
    state = graph.invoke({"raw_query": raw_query})
    analyzed_state = state["analyzed"]
    analyzed = []
    for item in analyzed_state:
        analyzed_item = {}
        analyzed_item["text"] = item.text
        analyzed_item["topic"] = item.topic
        analyzed_item["speech_act"] = item.speech_act
        analyzed.append(analyzed_item)
    row = {}
    row["id"] = query_id
    row["raw_query"] = raw_query
    row["polish_status"] = state["polish_status"]
    row["polished_questions"] = state["polished_questions"]
    row["analyzed"] = analyzed
    row["final_message"] = state.get("final_message")
    row["error"] = None
    return row


def main() -> None:
    """
    Run the saved query set and write timestamped experiment results.

    Arguments:
        None

    Returns:
        None

    Example:
        >>> main()
    """
    query_text = QUERY_PATH.read_text()
    queries = json.loads(query_text)
    graph = build_extraction_graph()
    results = []
    for query in queries:
        row = _run_query(graph, query)
        results.append(row)
    current_time = datetime.now(timezone.utc)
    timestamp_utc = current_time.isoformat()
    metadata = {}
    metadata["timestamp_utc"] = timestamp_utc
    metadata["model"] = MODEL
    metadata["max_attempts"] = MAX_ATTEMPTS
    metadata["entrypoint"] = "build_extraction_graph"
    metadata["experiment"] = EXPERIMENT_NAME
    output = {}
    output["metadata"] = metadata
    output["results"] = results
    serialized = json.dumps(output, indent=2, ensure_ascii=False)
    RESULT_PATH.write_text(f"{serialized}\n")


if __name__ == "__main__":
    main()
