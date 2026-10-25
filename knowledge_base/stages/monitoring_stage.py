import csv
import json
from pathlib import Path

from knowledge_base.helpers.output_helper import build_output_directories


def _read_summary(path: Path) -> dict:
    """
    Description: Read one stage summary JSON when present.

    Arguments:
        path (Path): Summary file path.

    Returns:
        dict: Parsed summary data or an empty dictionary.

    Example:
        >>> _read_summary(Path("01_chunking.json"))  # returns the parsed JSON dict
    """
    # Read the summary file text.
    summary_text = path.read_text(encoding="utf-8")

    # Parse the summary JSON.
    summary = json.loads(summary_text)

    # Return the parsed summary.
    return summary


def _build_banner(rows: list[dict], totals: dict) -> str:
    """
    Description: Build the Stage 4 monitoring banner text.

    Arguments:
        rows (list[dict]): Per-stage display rows.
        totals (dict): Totals row display values.

    Returns:
        str: Formatted banner string.

    Example:
        >>> _build_banner(
        ...     rows=[
        ...         {"stage": "Chunking", "files": "    2", "chunks": "   10",
        ...          "vectors": "      —", "joined": "     —", "dim": "   —",
        ...          "skipped": "      —", "elapsed": "    0.5s"},
        ...     ],
        ...     totals={"files": "    2", "chunks": "   10", "vectors": "      —",
        ...             "joined": "     —", "dim": "   —", "skipped": "      —",
        ...             "elapsed": "    0.5s"},
        ... )
        # Returns the formatted Stage 4 banner.
    """
    # Initialize the banner lines.
    lines = []

    # Add the top border.
    lines.append("------------------------------------------------------------------")

    # Add the stage title.
    lines.append("################ Stage 4: Monitoring ##############################")

    # Add the title divider.
    lines.append("------------------------------------------------------------------")

    # Add the column header.
    lines.append("Stage         | Files | Chunks | Vectors | Joined |  Dim | Skipped | Elapsed")

    # Add the column-header divider.
    lines.append("------------------------------------------------------------------------------")

    # Render each per-stage row.
    for row in rows:

        # Append the formatted per-stage row.
        lines.append(
            f"{row['stage']:<13} | "
            f"{row['files']:>5} | "
            f"{row['chunks']:>6} | "
            f"{row['vectors']:>7} | "
            f"{row['joined']:>6} | "
            f"{row['dim']:>4} | "
            f"{row['skipped']:>7} | "
            f"{row['elapsed']}"
        )

    # Add the footer border.
    lines.append("------------------------------------------------------------------------------")

    # Build the totals line.
    total_line = (
        f"{'Total':<13} | "
        f"{totals['files']:>5} | "
        f"{totals['chunks']:>6} | "
        f"{totals['vectors']:>7} | "
        f"{totals['joined']:>6} | "
        f"{totals['dim']:>4} | "
        f"{totals['skipped']:>7} | "
        f"{totals['elapsed']}"
    )

    # Append the totals line.
    lines.append(total_line)

    # Add the bottom border.
    lines.append("------------------------------------------------------------------")

    # Join the banner lines.
    banner = "\n".join(lines)

    # Return the formatted banner.
    return banner


def run_stage() -> None:
    """
    Execute stage 4 monitoring from summary JSON files only.

    Arguments:
        None

    Returns:
        None

    Example:
        >>> run_stage()  # requires summaries, embeddings.jsonl, and kb_index.jsonl from stages 1-3
    """
    directories = build_output_directories()
    summary_dir = directories["pipeline_summary"]
    monitoring_dir = directories["monitoring"]
    banners_dir = directories["banners"]

    chunking_summary = _read_summary(summary_dir / "01_chunking.json")
    embedding_summary = _read_summary(summary_dir / "02_embedding.json")
    assembling_summary = _read_summary(summary_dir / "03_assembling.json")

    # Write per-file chunk counts from the chunking summary.
    chunks_csv_path = monitoring_dir / "01_chunks.csv"
    chunks_fieldnames = ["source_path", "chunk_count"]
    with chunks_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=chunks_fieldnames)
        writer.writeheader()
        per_file_rows = chunking_summary["per_file"]
        for row in per_file_rows:
            output_row = {}
            output_row["source_path"] = row["source_path"]
            output_row["chunk_count"] = row["chunk_count"]
            writer.writerow(output_row)

    # Stream embeddings JSONL to write one monitoring row per vector.
    embeddings_csv_path = monitoring_dir / "02_embeddings.csv"
    embeddings_fieldnames = ["id", "content_hash", "dim"]
    with embeddings_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=embeddings_fieldnames)
        writer.writeheader()
        embeddings_path = directories["run_root"] / "embeddings.jsonl"
        with embeddings_path.open("r", encoding="utf-8") as reader:
            for line in reader:
                record = json.loads(line)
                output_row = {}
                output_row["id"] = record["id"]
                output_row["content_hash"] = record["content_hash"]
                output_row["dim"] = len(record["embedding"])
                writer.writerow(output_row)

    # Stream assembled index JSONL to write one monitoring row per joined record.
    assembly_csv_path = monitoring_dir / "03_assembly.csv"
    assembly_fieldnames = ["id", "source_path", "chunk_index"]
    with assembly_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=assembly_fieldnames)
        writer.writeheader()
        kb_index_path = directories["run_root"] / "kb_index.jsonl"
        with kb_index_path.open("r", encoding="utf-8") as reader:
            for line in reader:
                record = json.loads(line)
                output_row = {}
                output_row["id"] = record["id"]
                output_row["source_path"] = record["source_path"]
                output_row["chunk_index"] = record["chunk_index"]
                writer.writerow(output_row)

    chunking_elapsed_value = chunking_summary["elapsed_s"]
    chunking_elapsed = float(chunking_elapsed_value)
    embedding_elapsed_value = embedding_summary["elapsed_s"]
    embedding_elapsed = float(embedding_elapsed_value)
    assembling_elapsed_value = assembling_summary["elapsed_s"]
    assembling_elapsed = float(assembling_elapsed_value)

    chunking_file_count_value = chunking_summary["file_count"]
    chunking_file_count = int(chunking_file_count_value)
    chunking_chunk_count_value = chunking_summary["chunk_count"]
    chunking_chunk_count = int(chunking_chunk_count_value)
    embedding_vector_count_value = embedding_summary["vector_count"]
    embedding_vector_count = int(embedding_vector_count_value)
    embedding_dim_value = embedding_summary["dim"]
    embedding_dim = int(embedding_dim_value)
    embedding_skipped_count_value = embedding_summary["skipped_count"]
    embedding_skipped_count = int(embedding_skipped_count_value)
    assembling_joined_count_value = assembling_summary["joined_count"]
    assembling_joined_count = int(assembling_joined_count_value)
    assembling_dim_value = assembling_summary["dim"]
    assembling_dim = int(assembling_dim_value)
    assembling_skipped_count_value = assembling_summary["skipped_count"]
    assembling_skipped_count = int(assembling_skipped_count_value)

    # Build the chunking row.
    chunking_banner_row = {}
    chunking_banner_row["stage"] = "Chunking"
    chunking_banner_row["files"] = f"{chunking_file_count:>5}"
    chunking_banner_row["chunks"] = f"{chunking_chunk_count:>6}"
    chunking_banner_row["vectors"] = "      —"
    chunking_banner_row["joined"] = "     —"
    chunking_banner_row["dim"] = "   —"
    chunking_banner_row["skipped"] = "      —"
    chunking_banner_row["elapsed"] = f"{chunking_elapsed:>7.1f}s"

    # Build the embedding row.
    embedding_banner_row = {}
    embedding_banner_row["stage"] = "Embedding"
    embedding_banner_row["files"] = "    —"
    embedding_banner_row["chunks"] = "     —"
    embedding_banner_row["vectors"] = f"{embedding_vector_count:>7}"
    embedding_banner_row["joined"] = "     —"
    embedding_banner_row["dim"] = f"{embedding_dim:>4}"
    embedding_banner_row["skipped"] = f"{embedding_skipped_count:>7}"
    embedding_banner_row["elapsed"] = f"{embedding_elapsed:>7.1f}s"

    # Build the assembling row.
    assembling_banner_row = {}
    assembling_banner_row["stage"] = "Assembling"
    assembling_banner_row["files"] = "    —"
    assembling_banner_row["chunks"] = "     —"
    assembling_banner_row["vectors"] = "      —"
    assembling_banner_row["joined"] = f"{assembling_joined_count:>6}"
    assembling_banner_row["dim"] = f"{assembling_dim:>4}"
    assembling_banner_row["skipped"] = f"{assembling_skipped_count:>7}"
    assembling_banner_row["elapsed"] = f"{assembling_elapsed:>7.1f}s"

    # Collect the banner rows.
    monitoring_rows = []
    monitoring_rows.append(chunking_banner_row)
    monitoring_rows.append(embedding_banner_row)
    monitoring_rows.append(assembling_banner_row)

    total_files = chunking_file_count
    total_chunks = chunking_chunk_count
    total_vectors = embedding_vector_count
    total_joined = assembling_joined_count
    total_dim = embedding_dim
    total_skipped = embedding_skipped_count + assembling_skipped_count
    total_elapsed = chunking_elapsed + embedding_elapsed + assembling_elapsed

    # Write compact monitoring totals table with one row per stage.
    monitoring_csv_path = monitoring_dir / "monitoring_all.csv"
    monitoring_fieldnames = [
        "stage",
        "files",
        "chunks",
        "vectors",
        "joined",
        "dim",
        "skipped",
        "elapsed_s",
    ]
    with monitoring_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=monitoring_fieldnames,
        )
        writer.writeheader()
        chunking_row = {}
        chunking_row["stage"] = "chunking"
        chunking_row["files"] = total_files
        chunking_row["chunks"] = total_chunks
        chunking_row["vectors"] = 0
        chunking_row["joined"] = 0
        chunking_row["dim"] = 0
        chunking_row["skipped"] = 0
        chunking_row["elapsed_s"] = round(chunking_elapsed, 4)
        writer.writerow(chunking_row)

        embedding_row = {}
        embedding_row["stage"] = "embedding"
        embedding_row["files"] = 0
        embedding_row["chunks"] = 0
        embedding_row["vectors"] = total_vectors
        embedding_row["joined"] = 0
        embedding_row["dim"] = embedding_dim
        embedding_row["skipped"] = embedding_skipped_count
        embedding_row["elapsed_s"] = round(embedding_elapsed, 4)
        writer.writerow(embedding_row)

        assembling_row = {}
        assembling_row["stage"] = "assembling"
        assembling_row["files"] = 0
        assembling_row["chunks"] = 0
        assembling_row["vectors"] = 0
        assembling_row["joined"] = total_joined
        assembling_row["dim"] = assembling_dim
        assembling_row["skipped"] = assembling_skipped_count
        assembling_row["elapsed_s"] = round(assembling_elapsed, 4)
        writer.writerow(assembling_row)

    # Build the totals row.
    totals = {}
    totals["files"] = f"{total_files:>5}"
    totals["chunks"] = f"{total_chunks:>6}"
    totals["vectors"] = f"{total_vectors:>7}"
    totals["joined"] = f"{total_joined:>6}"
    totals["dim"] = f"{total_dim:>4}"
    totals["skipped"] = f"{total_skipped:>7}"
    totals["elapsed"] = f"{total_elapsed:>7.1f}s"
    banner = _build_banner(rows=monitoring_rows, totals=totals)
    print(banner)
    banner_path = banners_dir / "stage_4.txt"
    banner_text = f"{banner}\n"
    banner_path.write_text(banner_text, encoding="utf-8")
