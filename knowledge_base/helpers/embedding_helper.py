EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


def load_embedding_model(model_name: str = EMBEDDING_MODEL):
    """
    Description: Load and return the sentence-transformers embedding model.

    Arguments:
        model_name (str): Model name to load.

    Returns:
        SentenceTransformer: Loaded embedding model instance.

    Example:
        >>> model = load_embedding_model()
        # returns a SentenceTransformer instance
    """

    # Import sentence-transformers lazily to avoid loading the model at
    # module import time.
    from sentence_transformers import SentenceTransformer

    # Load the model instance.
    model = SentenceTransformer(model_name)
    return model
