import json
import logging
import time
from datetime import datetime

from knowledge_base.helpers.assembling_helper import assemble_record
from knowledge_base.helpers.embedding_helper import EMBEDDING_DIM
from knowledge_base.helpers.output_helper import build_output_directories
from knowledge_base.helpers.shared_helper import format_elapsed_seconds, write_json


def _build_banner(joined_count: int, skipped_count: int, dim: int) -> str:
    lines = []
    lines.append("------------------------------------------------------------")
    lines.append("################ Stage 3: Assembling #######################")
    lines.append("------------------------------------------------------------")
    lines.append(f"Joined: {joined_count}")
    lines.append(f"Skipped: {skipped_count}")
    lines.append(f"Dim: {dim}")
    lines.append("------------------------------------------------------------")
    banner = "\n".join(lines)
    return banner


def run_stage() -> dict:
    """
    Execute stage 3 assembling by joining chunks and embeddings.

    Arguments:
        None

    Returns:
        dict: Assembling stage summary statistics.

    Example:
        >>> stats = run_stage()
    """
    logging.info("[Stage 3] assembling started")
    start_time = time.time()

    directories = build_output_directories()
    run_root = directories["run_root"]
    summary_dir = directories["pipeline_summary"]
    banners_dir = directories["banners"]

    chunks_path = run_root / "chunks.jsonl"
    embeddings_path = run_root / "embeddings.jsonl"
    assembled_path = run_root / "kb_index.jsonl"

    embedding_map: dict[str, tuple[str, list[float]]] = {}
    with embeddings_path.open("r", encoding="utf-8") as reader:
        for line in reader:
            row = line.strip()
            entry = json.loads(row)
            embedding_map[entry["id"]] = (entry["content_hash"], entry["embedding"])

    joined_count = 0
    skipped_count = 0

    with chunks_path.open("r", encoding="utf-8") as chunk_reader, assembled_path.open(
        "w", encoding="utf-8", newline="\n"
    ) as writer:
        first = True
        for line in chunk_reader:
            row = line.strip()
            chunk = json.loads(row)
            embedding_hit = embedding_map[chunk["id"]]
            _, embedding_vector = embedding_hit
            assembled = assemble_record(chunk=chunk, embedding=embedding_vector)
            if first == False:
                writer.write("\n")
            serialized = json.dumps(assembled, ensure_ascii=False, separators=(",", ":"))
            writer.write(serialized)
            first = False
            joined_count += 1

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
    write_json(summary_dir / "03_assembling.json", summary)

    banner = _build_banner(joined_count=joined_count, skipped_count=skipped_count, dim=EMBEDDING_DIM)
    print(banner)
    (banners_dir / "stage_3.txt").write_text(f"{banner}\n", encoding="utf-8")

    formatted_elapsed = format_elapsed_seconds(elapsed_s)
    logging.info("[Stage 3] assembling finished (%s)", formatted_elapsed)
    return summary
