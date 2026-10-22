import json
import math
from pathlib import Path

from sentence_transformers import SentenceTransformer

from .schema import EMBEDDING_MODEL, MIN_SIMILARITY, RetrievedChunk, TOP_K

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = sorted(PROJECT_ROOT.glob("output_knowledge_base/*/kb_index.jsonl"))[-1]
INDEX_ROWS = [
    json.loads(line)
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines()
]
EMBEDDING_MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL)


def embed_query(text: str) -> list[float]:
    """Summary: Embed a query using the configured sentence-transformer model.

    Arguments:
        text: Query text to embed.

    Returns:
        The query embedding as a list of floats.

    Example:
        >>> len(embed_query("How do I request leave?"))
        384
    """
    embedding = EMBEDDING_MODEL_INSTANCE.encode(text)
    vector = embedding.tolist()
    return vector


def _cosine_similarity(query_vector: list[float], chunk_vector: list[float]) -> float:
    """Summary: Compute cosine similarity between two embedding vectors.

    Arguments:
        query_vector: Query embedding vector.
        chunk_vector: Indexed chunk embedding vector.

    Returns:
        Cosine similarity score.

    Example:
        >>> _cosine_similarity([1.0, 0.0], [0.0, 1.0])
        0.0
    """
    paired_values = zip(query_vector, chunk_vector)
    dot_product = sum(pair[0] * pair[1] for pair in paired_values)
    query_norm = math.sqrt(sum(value * value for value in query_vector))
    chunk_norm = math.sqrt(sum(value * value for value in chunk_vector))
    score = dot_product / (query_norm * chunk_norm)
    return score


def retrieve_top_k(query_vector: list[float], k: int = TOP_K) -> list[RetrievedChunk]:
    """Summary: Return the highest-scoring indexed chunks above the threshold.

    Arguments:
        query_vector: Query embedding vector.
        k: Maximum number of chunks to return.

    Returns:
        Retrieved chunks in descending similarity order.

    Example:
        >>> retrieve_top_k([0.1, 0.2, 0.3], k=3)
        [...]
    """
    scored_rows = [
        (row, _cosine_similarity(query_vector, row["embedding"]))
        for row in INDEX_ROWS
    ]
    matching_rows = [item for item in scored_rows if item[1] >= MIN_SIMILARITY]
    ranked_rows = sorted(matching_rows, key=lambda item: item[1], reverse=True)
    selected_rows = ranked_rows[:k]
    chunks = [
        RetrievedChunk(
            chunk_id=selected_row[0]["id"],
            file=selected_row[0]["source_path"],
            text=selected_row[0]["text"],
            score=selected_row[1],
        )
        for selected_row in selected_rows
    ]
    return chunks
