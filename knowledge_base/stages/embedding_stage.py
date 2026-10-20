import json
import logging
import time
from datetime import datetime

from knowledge_base.helpers.embedding_helper import EMBEDDING_DIM, EMBEDDING_MODEL, load_embedding_model
from knowledge_base.helpers.output_helper import build_output_directories
from knowledge_base.helpers.shared_helper import format_elapsed_seconds, write_json


def _build_banner(model_name: str, dim: int, vector_count: int) -> str:
    lines = []
    lines.append("------------------------------------------------------------")
    lines.append("################ Stage 2: Embedding ########################")
    lines.append("------------------------------------------------------------")
    lines.append(f"Model: {model_name}")
    lines.append(f"Dim: {dim}")
    lines.append(f"Vectors: {vector_count}")
    lines.append("------------------------------------------------------------")
    banner = "\n".join(lines)
    return banner


def _iter_chunk_batches(chunks_path, batch_size: int = 32):
    batch = []
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = line.strip()
            chunk = json.loads(row)
            batch.append(chunk)
            if len(batch) == batch_size:
                yield batch
                batch = []
    if batch:
        yield batch


def run_stage() -> dict:
    """
    Execute stage 2 embedding and write vector outputs and summary.

    Arguments:
        None

    Returns:
        dict: Embedding stage summary statistics.

    Example:
        >>> stats = run_stage()
    """
    logging.info("[Stage 2] embedding started")
    start_time = time.time()

    directories = build_output_directories()
    run_root = directories["run_root"]
    summary_dir = directories["pipeline_summary"]
    banners_dir = directories["banners"]

    chunks_path = run_root / "chunks.jsonl"
    embeddings_path = run_root / "embeddings.jsonl"

    model = load_embedding_model(EMBEDDING_MODEL)
    vector_count = 0
    dim = EMBEDDING_DIM

    with embeddings_path.open("w", encoding="utf-8", newline="\n") as writer:
        first = True
        for chunk_batch in _iter_chunk_batches(chunks_path, batch_size=32):
            texts = [row["text"] for row in chunk_batch]
            vectors = model.encode(texts, convert_to_numpy=False, show_progress_bar=False)

            for chunk_row, vector in zip(chunk_batch, vectors):
                dim = len(vector)
                embedding = [float(value) for value in vector]
                out_row = {}
                out_row["id"] = chunk_row["id"]
                out_row["content_hash"] = chunk_row["content_hash"]
                out_row["embedding"] = embedding
                if first == False:
                    writer.write("\n")
                serialized = json.dumps(out_row, ensure_ascii=False, separators=(",", ":"))
                writer.write(serialized)
                first = False
                vector_count += 1

    elapsed_s = time.time() - start_time
    generated_at = datetime.now()
    generated_at_text = generated_at.isoformat()
    summary = {}
    summary["stage"] = "embedding"
    summary["model"] = EMBEDDING_MODEL
    summary["dim"] = EMBEDDING_DIM
    summary["vector_count"] = vector_count
    summary["skipped_count"] = 0
    summary["elapsed_s"] = elapsed_s
    summary["generated_at"] = generated_at_text
    write_json(summary_dir / "02_embedding.json", summary)

    banner = _build_banner(model_name=EMBEDDING_MODEL, dim=dim, vector_count=vector_count)
    print(banner)
    (banners_dir / "stage_2.txt").write_text(f"{banner}\n", encoding="utf-8")

    formatted_elapsed = format_elapsed_seconds(elapsed_s)
    logging.info("[Stage 2] embedding finished (%s)", formatted_elapsed)
    return summary
