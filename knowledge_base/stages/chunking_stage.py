import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from knowledge_base.helpers.chunking_helper import CHUNK_OVERLAP, CHUNK_SIZE, chunk_section
from knowledge_base.helpers.output_helper import build_output_directories
from knowledge_base.helpers.shared_helper import format_elapsed_seconds, write_json, write_jsonl

SOURCE_GLOB = "Dummy_Docs/HR_dummy_docs/*.json"


def _build_banner(per_file: list[dict], total_chunks: int) -> str:
    """
    Description: Build the Stage 1 chunking banner.

    Arguments:
        per_file (list[dict]): Per-file source paths and chunk counts.
        total_chunks (int): Total number of chunks produced.

    Returns:
        str: Formatted chunking-stage banner.

    Example:
        >>> _build_banner(per_file=[{"source_path": "a.json", "chunk_count": 3}], total_chunks=3)
        # Returns the Stage 1 banner for one file with three chunks.
    """
    # Build the banner header block.
    lines = [
        "------------------------------------------------------------",
        "################ Stage 1: Chunking #########################",
        "------------------------------------------------------------",
        "Source file                    | Chunks",
        "------------------------------------------------------------",
    ]

    # Add one row for each source file.
    for row in per_file:
        lines.append(f"{row['source_path']:<30} | {row['chunk_count']:>6}")

    # Build and append the totals block.
    total_lines = [
        "------------------------------------------------------------",
        f"{'Total':<30} | {total_chunks:>6}",
        "------------------------------------------------------------",
    ]
    lines.extend(total_lines)

    # Join the banner lines.
    banner = "\n".join(lines)

    # Return the formatted banner.
    return banner


def run_stage() -> dict:
    """
    Description: Execute stage 1 chunking and write chunks and summary outputs.

    Arguments:
        None

    Returns:
        dict: Chunking stage summary statistics.

    Example:
        >>> stats = run_stage()  # requires source files under Dummy_Docs/
    """
    # Start timing and log the stage start.
    logging.info("[Stage 1] chunking started")
    start_time = time.time()

    # Resolve the output directories.
    directories = build_output_directories()
    run_root = directories["run_root"]
    summary_dir = directories["pipeline_summary"]
    banners_dir = directories["banners"]

    # Resolve and filter source paths.
    module_path = Path(__file__)
    resolved_path = module_path.resolve()
    project_root = resolved_path.parents[2]
    source_paths = project_root.glob(SOURCE_GLOB)
    chunkable_paths = []
    for source_path in source_paths:
        if source_path.name != "eval_qa_pairs.json":
            chunkable_paths.append(source_path)
    source_files = sorted(chunkable_paths)

    # Resolve the chunks output path.
    chunks_path = run_root / "chunks.jsonl"
    all_chunks: list[dict] = []
    per_file: list[dict] = []

    # Process each source file.
    for source_file in source_files:
        # Read the source JSON and initialize per-file counters.
        source_text = source_file.read_text(encoding="utf-8")
        doc_items = json.loads(source_text)
        file_chunk_count = 0
        chunk_index = 0

        # Resolve the source path relative to the project root.
        relative_path = source_file.relative_to(project_root)
        source_path = relative_path.as_posix()

        # Process each document section.
        for section in doc_items:
            # Extract chunks from the section paragraphs.
            section_chunks = chunk_section(
                paragraphs=section["paragraphs"],
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
            )

            # Build a record for each extracted chunk.
            for text in section_chunks:
                stem = source_file.stem
                chunk_id = f"{stem}__{chunk_index:04d}"
                encoded_text = text.encode("utf-8")
                hash_object = hashlib.sha1(encoded_text)
                hash_digest = hash_object.hexdigest()
                content_hash = hash_digest[:16]

                # Populate the chunk record fields.
                chunk = {}
                chunk["id"] = chunk_id
                chunk["content_hash"] = content_hash
                chunk["source_path"] = source_path
                chunk["text"] = text
                chunk["chunk_index"] = chunk_index

                # Append the chunk and increment the counts.
                all_chunks.append(chunk)
                chunk_index += 1
                file_chunk_count += 1

        # Record the source file's chunk count.
        file_summary = {}
        file_summary["source_path"] = source_path
        file_summary["chunk_count"] = file_chunk_count
        per_file.append(file_summary)

    # Write chunks.jsonl.
    write_jsonl(chunks_path, all_chunks)

    # Construct the stage summary.
    elapsed_s = time.time() - start_time
    generated_at = datetime.now()
    generated_at_text = generated_at.isoformat()
    summary = {}
    summary["stage"] = "chunking"
    summary["file_count"] = len(source_files)
    total_chunks = len(all_chunks)
    summary["chunk_count"] = total_chunks
    summary["per_file"] = per_file
    summary["chunk_size"] = CHUNK_SIZE
    summary["chunk_overlap"] = CHUNK_OVERLAP
    summary["elapsed_s"] = elapsed_s
    summary["generated_at"] = generated_at_text

    # Write the stage summary.
    write_json(summary_dir / "01_chunking.json", summary)

    # Construct the stage banner.
    banner = _build_banner(per_file=per_file, total_chunks=total_chunks)

    # Print the stage banner.
    print(banner)

    # Write the stage banner file.
    banner_path = banners_dir / "stage_1.txt"
    banner_text = f"{banner}\n"
    banner_path.write_text(banner_text, encoding="utf-8")

    # Log the elapsed stage time.
    formatted_elapsed = format_elapsed_seconds(elapsed_s)
    logging.info("[Stage 1] chunking finished (%s)", formatted_elapsed)

    # Return the stage summary.
    return summary
