import json
import logging
import time
from datetime import datetime

from knowledge_base.helpers.assembling_helper import assemble_record
from knowledge_base.helpers.embedding_helper import EMBEDDING_DIM
from knowledge_base.helpers.output_helper import build_output_directories
from knowledge_base.helpers.shared_helper import format_elapsed_seconds, write_json


def _build_banner(joined_count: int, skipped_count: int, dim: int) -> str:
    """
    Description: Build the assembling-stage banner.

    Arguments:
        joined_count (int): Number of chunks joined with embeddings.
        skipped_count (int): Number of skipped chunks.
        dim (int): Embedding dimension.

    Returns:
        str: Formatted assembling-stage banner.

    Example:
        >>> _build_banner(joined_count=10, skipped_count=0, dim=384)
        '------------------------------------------------------------\\n################ Stage 3: Assembling #######################\\n------------------------------------------------------------\\nJoined: 10\\nSkipped: 0\\nDim: 384\\n------------------------------------------------------------'
    """
    # Collect the banner lines.
    lines = []

    # Add the top border.
    lines.append("------------------------------------------------------------")

    # Add the stage title.
    lines.append("################ Stage 3: Assembling #######################")

    # Add the title divider.
    lines.append("------------------------------------------------------------")

    # Add the joined-count statistic.
    lines.append(f"Joined: {joined_count}")

    # Add the skipped-count statistic.
    lines.append(f"Skipped: {skipped_count}")

    # Add the embedding-dimension statistic.
    lines.append(f"Dim: {dim}")

    # Add the bottom border.
    lines.append("------------------------------------------------------------")

    # Join the banner lines.
    banner = "\n".join(lines)

    # Return the formatted banner.
    return banner


def run_stage() -> dict:
    """
    Description: Execute stage 3 assembling by joining chunks and embeddings.

    Arguments:
        None

    Returns:
        dict: Assembling stage summary statistics.

    Example:
        >>> stats = run_stage()  # requires prior stages' output files
    """
    # Start timing and log the stage start.
    logging.info("[Stage 3] assembling started")
    start_time = time.time()

    # Resolve the run and output directories.
    directories = build_output_directories()
    run_root = directories["run_root"]
    summary_dir = directories["pipeline_summary"]
    banners_dir = directories["banners"]

    # Resolve the input and output file paths.
    chunks_path = run_root / "chunks.jsonl"
    embeddings_path = run_root / "embeddings.jsonl"
    assembled_path = run_root / "kb_index.jsonl"

    # Build the embedding map from embeddings.jsonl.
    embedding_map: dict[str, tuple[str, list[float]]] = {}
    with embeddings_path.open("r", encoding="utf-8") as reader:
        for line in reader:
            row = line.strip()
            entry = json.loads(row)
            embedding_map[entry["id"]] = (entry["content_hash"], entry["embedding"])

    # Build assembled rows from chunks.jsonl.
    joined_count = 0
    skipped_count = 0
    assembled_rows = []

    with chunks_path.open("r", encoding="utf-8") as chunk_reader:
        for line in chunk_reader:
            row = line.strip()
            chunk = json.loads(row)

            # Retrieve the stored content-hash and embedding tuple.
            embedding_hit = embedding_map[chunk["id"]]
            embedding_vector = embedding_hit[1]

            assembled = assemble_record(chunk=chunk, embedding=embedding_vector)
            serialized = json.dumps(assembled, ensure_ascii=False, separators=(",", ":"))
            assembled_rows.append(serialized)
            joined_count += 1

    # Write the assembled kb_index.jsonl file.
    assembled_text = "\n".join(assembled_rows)
    assembled_path.write_text(assembled_text, encoding="utf-8", newline="\n")

    # Construct the run summary.
    elapsed_s = time.time() - start_time
    generated_at = datetime.now()
    generated_at_text = generated_at.isoformat()
    summary = {}
    summary["stage"] = "assembling"
    summary["joined_count"] = joined_count
    summary["skipped_count"] = skipped_count
    summary["dim"] = EMBEDDING_DIM
    summary["elapsed_s"] = elapsed_s
    summary["generated_at"] = generated_at_text

    # Write the summary file.
    write_json(summary_dir / "03_assembling.json", summary)

    # Construct the stage banner.
    banner = _build_banner(joined_count=joined_count, skipped_count=skipped_count, dim=EMBEDDING_DIM)

    # Print the stage banner.
    print(banner)

    # Write the stage banner file.
    (banners_dir / "stage_3.txt").write_text(f"{banner}\n", encoding="utf-8")

    # Log the elapsed stage time.
    formatted_elapsed = format_elapsed_seconds(elapsed_s)
    logging.info("[Stage 3] assembling finished (%s)", formatted_elapsed)

    # Return the summary statistics.
    return summary
