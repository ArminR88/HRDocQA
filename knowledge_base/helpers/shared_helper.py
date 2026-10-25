import json
import logging
from pathlib import Path


def setup_logging(verbose: bool = False) -> None:
    """
    Description: Configure the root logger for pipeline execution.

    Arguments:
        verbose (bool): If True, enable DEBUG-level logs.

    Returns:
        None: No value is returned.

    Example:
        >>> setup_logging(verbose=True)
        None
    """

    # Select the configured log level.
    log_level = logging.INFO
    if verbose == True:
        log_level = logging.DEBUG

    # Configure root logging.
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def format_elapsed_seconds(seconds: float) -> str:
    """
    Description: Format elapsed seconds for human-readable logging.

    Arguments:
        seconds (float): Elapsed runtime in seconds.

    Returns:
        str: Formatted string with one decimal place and trailing "s".

    Example:
        >>> format_elapsed_seconds(3.14159)
        '3.1s'
    """
    # Format the duration to one decimal place.
    formatted = f"{seconds:.1f}s"
    return formatted


def write_json(path: Path, data: dict) -> None:
    """
    Description: Write a dictionary to JSON with UTF-8 encoding.

    Arguments:
        path (Path): Output JSON file path.
        data (dict): JSON-serializable dictionary.

    Returns:
        None: No value is returned.

    Example:
        >>> write_json(Path("summary.json"), {"stage": "chunking"})
        None
    """

    # Create the output directory.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize the dictionary as formatted JSON.
    serialized = json.dumps(data, ensure_ascii=False, indent=2)

    # Write the JSON text to disk.
    path.write_text(serialized, encoding="utf-8")


def write_jsonl(path: Path, rows) -> None:
    """
    Description: Write iterable rows as compact JSONL with one object per line.

    Arguments:
        path (Path): Output JSONL file path.
        rows: Iterable of JSON-serializable objects.

    Returns:
        None: No value is returned.

    Example:
        >>> write_jsonl(Path("rows.jsonl"), [{"id": "a"}, {"id": "b"}])
        None
    """

    # Create the output directory.
    path.parent.mkdir(parents=True, exist_ok=True)

    # Serialize each row as compact JSON.
    serialized_rows = []
    for row in rows:
        serialized_row = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
        serialized_rows.append(serialized_row)

    # Join serialized rows with newline separators.
    serialized = "\n".join(serialized_rows)

    # Write the JSONL text to disk.
    path.write_text(serialized, encoding="utf-8", newline="\n")
