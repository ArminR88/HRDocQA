EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def load_embedding_model(model_name: str = EMBEDDING_MODEL):
    """
    Load and return the sentence-transformers embedding model.

    Arguments:
        model_name (str): Model name to load.

    Returns:
        SentenceTransformer: Loaded embedding model instance.

    Example:
        >>> model = load_embedding_model()
    """
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    return model
