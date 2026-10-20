import json
import logging
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """
    Configure root logger for pipeline execution.

    Arguments:
        verbose (bool): If True, enable DEBUG-level logs.

    Returns:
        None

    Example:
        >>> setup_logging(verbose=True)
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def format_elapsed_seconds(seconds: float) -> str:
    """
    Format elapsed seconds for human-readable logging.

    Arguments:
        seconds (float): Elapsed runtime in seconds.

    Returns:
        str: Formatted string with one decimal place and trailing "s".

    Example:
        >>> format_elapsed_seconds(3.14159)
        '3.1s'
    """
    formatted = f"{seconds:.1f}s"
    return formatted


def write_json(path: Path, data: dict) -> None:
    """
    Write a dictionary to JSON with UTF-8 encoding.

    Arguments:
        path (Path): Output JSON file path.
        data (dict): JSON-serializable dictionary.

    Returns:
        None

    Example:
        >>> write_json(Path("summary.json"), {"stage": "chunking"})
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_text(serialized, encoding="utf-8")


def write_jsonl(path: Path, rows) -> None:
    """
    Write iterable rows as compact JSONL (one object per line).

    Arguments:
        path (Path): Output JSONL file path.
        rows: Iterable of JSON-serializable objects.

    Returns:
        None

    Example:
        >>> write_jsonl(Path("rows.jsonl"), [{"id": "a"}, {"id": "b"}])
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        first = True
        for row in rows:
            if first == False:
                handle.write("\n")
            serialized = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
            handle.write(serialized)
            first = False
