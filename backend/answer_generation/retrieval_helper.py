import json
import numpy
from pathlib import Path

from sentence_transformers import SentenceTransformer

from .constants import EMBEDDING_MODEL, MIN_SIMILARITY, TOP_K
from .schema import Retrieval_Chunk

# Resolve the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Locate the knowledge-base index.
INDEX_GLOB = PROJECT_ROOT.glob("output_knowledge_base/*/kb_index.jsonl")
INDEX_PATHS = sorted(INDEX_GLOB)
INDEX_PATH = INDEX_PATHS[-1]

# Read the index text.
INDEX_TEXT = INDEX_PATH.read_text(encoding="utf-8")
INDEX_LINES = INDEX_TEXT.splitlines()

# Parse index rows.
INDEX_ROWS = []
for line in INDEX_LINES:
    row = json.loads(line)
    INDEX_ROWS.append(row)

# Pre-convert embeddings to numpy arrays for fast vector math.
for row in INDEX_ROWS:
    embedding_array = numpy.array(row["embedding"])
    row["embedding"] = embedding_array

# Initialize the embedding model.
EMBEDDING_MODEL_INSTANCE = SentenceTransformer(EMBEDDING_MODEL)


def embed_query(text: str) -> numpy.ndarray:
    """
    Description: Embed a query using the configured sentence-transformer model.

    Arguments:
        text (str): Query text to embed.

    Returns:
        numpy.ndarray: The query embedding.
    """
    # Encode the query.
    embedding = EMBEDDING_MODEL_INSTANCE.encode(text)

    # Return the query vector.
    return embedding


def _score_of(scored_row: tuple[dict, float]) -> float:
    """
    Description: Return the similarity score from a (row, score) pair.

    Arguments:
        scored_row (tuple[dict, float]): Index row paired with its score.

    Returns:
        float: The similarity score.
    """
    # Extract the score component.
    return scored_row[1]


def _cosine_similarity(query_vector: numpy.ndarray, chunk_vector: numpy.ndarray) -> float:
    """
    Description: Compute cosine similarity between two embedding vectors.

    Arguments:
        query_vector (numpy.ndarray): Query embedding vector.
        chunk_vector (numpy.ndarray): Indexed chunk embedding vector.

    Returns:
        float: Cosine similarity score; zero-length vectors are guarded by a
            small epsilon.
    """
    # Calculate the dot product.
    dot_product = numpy.dot(query_vector, chunk_vector)

    # Calculate the query norm.
    query_norm = numpy.linalg.norm(query_vector)

    # Calculate the chunk norm.
    chunk_norm = numpy.linalg.norm(chunk_vector)

    # Guard the denominator against division by zero for zero-length vectors.
    epsilon = 1.e-8
    denominator = query_norm * chunk_norm + epsilon

    # Calculate the similarity score.
    score = dot_product / denominator

    # Return the similarity score.
    return score


def retrieve_top_k(query_vector: numpy.ndarray, k: int = TOP_K) -> list[Retrieval_Chunk]:
    """
    Description: Return the highest-scoring indexed chunks above the threshold.

    Arguments:
        query_vector (numpy.ndarray): Query embedding vector.
        k (int): Maximum number of chunks to return.

    Returns:
        list[Retrieval_Chunk]: Retrieved chunks in descending similarity order.
    """
    # Score every index row.
    scored_rows = []
    for row in INDEX_ROWS:
        score = _cosine_similarity(query_vector, row["embedding"])
        scored_row = (row, score)
        scored_rows.append(scored_row)

    # Keep rows at or above the similarity threshold.
    matching_rows = []
    for scored_row in scored_rows:
        if scored_row[1] >= MIN_SIMILARITY:
            matching_rows.append(scored_row)

    # Rank matching rows by descending similarity.
    ranked_rows = sorted(matching_rows, key=_score_of, reverse=True)

    # Limit results to the requested number.
    selected_rows = ranked_rows[:k]

    # Build retrieval chunks from selected rows.
    chunks = []
    for row, score in selected_rows:
        chunk = Retrieval_Chunk(
            chunk_id=row["id"],
            file=row["source_path"],
            text=row["text"],
            score=score,
        )
        chunks.append(chunk)

    # Return the ranked chunks.
    return chunks
