def assemble_record(chunk: dict, embedding: list[float]) -> dict:
    """
    Description: Join one chunk record with its embedding.

    Arguments:
        chunk (dict): Chunk object from chunks.jsonl.
        embedding (list[float]): Embedding vector.

    Returns:
        dict: Assembled record for kb_index.jsonl.

    Example:
        >>> assemble_record(
        ...     {"id": "x", "text": "a", "content_hash": "h",
        ...      "source_path": "p", "chunk_index": 0},
        ...     [0.1],
        ... )
        {'id': 'x', 'content_hash': 'h', 'source_path': 'p',
         'text': 'a', 'chunk_index': 0, 'embedding': [0.1]}
    """
    # Construct the assembled record.
    record = {}

    # Add chunk fields in the required key order.
    record["id"] = chunk["id"]
    record["content_hash"] = chunk["content_hash"]
    record["source_path"] = chunk["source_path"]
    record["text"] = chunk["text"]
    record["chunk_index"] = chunk["chunk_index"]

    # Add the embedding vector.
    record["embedding"] = embedding

    # Return the assembled record.
    return record
