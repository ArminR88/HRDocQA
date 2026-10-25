import json
import logging
import time
from datetime import datetime

from knowledge_base.helpers.embedding_helper import EMBEDDING_DIM, EMBEDDING_MODEL, load_embedding_model
from knowledge_base.helpers.output_helper import build_output_directories
from knowledge_base.helpers.shared_helper import format_elapsed_seconds, write_json


def _build_banner(model_name: str, dim: int, vector_count: int) -> str:
    """
    Description: Build the Stage 2 embedding banner.

    Arguments:
        model_name (str): Name of the embedding model.
        dim (int): Embedding dimension.
        vector_count (int): Number of vectors generated.

    Returns:
        str: Formatted embedding-stage banner.

    Example:
        >>> _build_banner(model_name="all-MiniLM-L6-v2", dim=384, vector_count=10)
        '------------------------------------------------------------\\n################ Stage 2: Embedding ########################\\n------------------------------------------------------------\\nModel: all-MiniLM-L6-v2\\nDim: 384\\nVectors: 10\\n------------------------------------------------------------'
    """
    # Collect the banner lines.
    lines = []

    # Add the top border.
    lines.append("------------------------------------------------------------")

    # Add the stage title.
    lines.append("################ Stage 2: Embedding ########################")

    # Add the title divider.
    lines.append("------------------------------------------------------------")

    # Add the model name.
    lines.append(f"Model: {model_name}")

    # Add the embedding dimension.
    lines.append(f"Dim: {dim}")

    # Add the vector count.
    lines.append(f"Vectors: {vector_count}")

    # Add the bottom border.
    lines.append("------------------------------------------------------------")

    # Join the banner lines.
    banner = "\n".join(lines)

    # Return the formatted banner.
    return banner


def _iter_chunk_batches(chunks_path, batch_size: int = 32):
    """
    Description: Yield chunk records from a JSONL file in bounded batches.

    Arguments:
        chunks_path (Path): Path to the chunks JSONL file.
        batch_size (int): Maximum number of records in each batch.

    Returns:
        Iterator[list[dict]]: Generator yielding batches of chunk records.

    Example:
        >>> list(_iter_chunk_batches(Path("chunks.jsonl"), batch_size=2))
        # Yields batches of up to two chunk dictionaries.
    """
    # Initialize the current batch.
    batch = []

    # Open the chunk file and read each JSONL record.
    with chunks_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = line.strip()
            chunk = json.loads(row)

            # Append the chunk to the current batch.
            batch.append(chunk)

            # Yield each complete batch and start a fresh one.
            if len(batch) == batch_size:
                yield batch
                batch = []

    # Yield any final partial batch.
    if len(batch) > 0:
        yield batch


def run_stage() -> dict:
    """
    Description: Execute stage 2 embedding and write vector outputs and summary.

    Arguments:
        None

    Returns:
        dict: Embedding stage summary statistics.

    Example:
        >>> stats = run_stage()  # requires chunks.jsonl from stage 1
    """
    # Start timing and log the stage start.
    logging.info("[Stage 2] embedding started")
    start_time = time.time()

    # Resolve the output directories.
    directories = build_output_directories()
    run_root = directories["run_root"]
    summary_dir = directories["pipeline_summary"]
    banners_dir = directories["banners"]

    # Resolve input and output paths.
    chunks_path = run_root / "chunks.jsonl"
    embeddings_path = run_root / "embeddings.jsonl"

    # Load the embedding model.
    model = load_embedding_model(EMBEDDING_MODEL)
    vector_count = 0
    dim = EMBEDDING_DIM
    embedding_rows = []

    # Process chunks in batches.
    for chunk_batch in _iter_chunk_batches(chunks_path, batch_size=32):
        # Collect text for batch encoding.
        texts = []
        for chunk_row in chunk_batch:
            chunk_text = chunk_row["text"]
            texts.append(chunk_text)

        # Encode the batch texts.
        vectors = model.encode(texts, convert_to_numpy=False, show_progress_bar=False)

        # Build an embedding record for each encoded chunk.
        for chunk_row, vector in zip(chunk_batch, vectors):
            dim = len(vector)

            # Convert vector values to native floats.
            embedding = []
            for value in vector:
                float_value = float(value)
                embedding.append(float_value)

            # Populate the embedding record fields.
            out_row = {}
            out_row["id"] = chunk_row["id"]
            out_row["content_hash"] = chunk_row["content_hash"]
            out_row["embedding"] = embedding

            # Serialize and append the embedding record.
            serialized = json.dumps(out_row, ensure_ascii=False, separators=(",", ":"))
            embedding_rows.append(serialized)
            vector_count += 1

    # Write the embeddings JSONL file.
    embedding_text = "\n".join(embedding_rows)
    embeddings_path.write_text(embedding_text, encoding="utf-8", newline="\n")

    # Construct the stage summary.
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

    # Write the stage summary.
    write_json(summary_dir / "02_embedding.json", summary)

    # Construct the stage banner.
    banner = _build_banner(model_name=EMBEDDING_MODEL, dim=dim, vector_count=vector_count)

    # Print the stage banner.
    print(banner)

    # Write the stage banner file.
    (banners_dir / "stage_2.txt").write_text(f"{banner}\n", encoding="utf-8")

    # Log the elapsed stage time.
    formatted_elapsed = format_elapsed_seconds(elapsed_s)
    logging.info("[Stage 2] embedding finished (%s)", formatted_elapsed)

    # Return the stage summary.
    return summary
