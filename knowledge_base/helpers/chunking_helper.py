import re

CHUNK_SIZE = 400
CHUNK_OVERLAP = 60
SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " "]

_ABBREVIATIONS = {"e.g", "i.e", "etc", "dr", "mr", "nr", "no", "vs"}


def split_sentences(text: str) -> list[str]:
    """
    Description: Split text into sentences while guarding decimals and abbreviations.

    Arguments:
        text (str): Input text.

    Returns:
        list[str]: Sentence list.

    Example:
        >>> split_sentences("Dr. Smith arrived. He spoke.")
        ['Dr. Smith arrived.', 'He spoke.']
    """
    # Normalize the input text.
    stripped = text.strip()

    # Find sentence-boundary punctuation candidates.
    boundaries: list[int] = []
    for match in re.finditer(r"[.!?]", stripped):
        idx = match.start()
        mark = match.group(0)

        # Guard decimal numbers like 1.5 from sentence splitting.
        if mark == "." and idx > 0 and idx < len(stripped) - 1:
            if stripped[idx - 1].isdigit() and stripped[idx + 1].isdigit():
                continue

        # Guard known abbreviations from sentence splitting.
        token_match = re.search(r"([A-Za-z]+)\.$", stripped[: idx + 1])
        if token_match is not None:
            token = token_match.group(1)
            normalized_token = token.lower()
            if normalized_token in _ABBREVIATIONS:
                continue

        # Split only when punctuation is followed by whitespace and capital start.
        trailing = stripped[idx + 1 :]
        if re.match(r'^\s+(?:["\')\]]\s*)?[A-Z]', trailing):
            boundaries.append(idx + 1)

    # Build sentences from the detected boundaries.
    sentences: list[str] = []
    start = 0
    for end in boundaries:
        raw_part = stripped[start:end]
        part = raw_part.strip()
        sentences.append(part)
        start = end

    # Append the final remainder.
    raw_remainder = stripped[start:]
    remainder = raw_remainder.strip()
    sentences.append(remainder)

    # Return the sentence list.
    return sentences


def _split_keep_separator(text: str, separator: str) -> list[str]:
    """
    Description: Split text while keeping each separator on its preceding part.

    Arguments:
        text (str): Text to split.
        separator (str): Separator to retain.

    Returns:
        list[str]: Split text parts with separators retained.

    Example:
        >>> _split_keep_separator("A. B.", ". ")
        ['A.', 'B.']
    """
    # Split text at each separator.
    raw_parts = text.split(separator)

    # Reattach separators to all non-final parts.
    pieces: list[str] = []
    for index, piece in enumerate(raw_parts):
        if index < len(raw_parts) - 1:
            joined_piece = f"{piece}{separator}"
            cleaned_piece = joined_piece.strip()
            pieces.append(cleaned_piece)
        else:
            cleaned_piece = piece.strip()
            pieces.append(cleaned_piece)

    # Return the split parts.
    return pieces


def _recursive_split(text: str, chunk_size: int, separators: list[str], index: int) -> list[str]:
    """
    Description: Recursively split oversized text using ordered separators.

    Arguments:
        text (str): Text to split.
        chunk_size (int): Maximum chunk length.
        separators (list[str]): Ordered separators to try.
        index (int): Index of the next separator to use.

    Returns:
        list[str]: Text chunks no longer than the configured size when possible.

    Example:
        >>> _recursive_split("A. B.", 3, [". ", " "], 0)
        ['A.', 'B.']
    """
    # Normalize the input and handle text that already fits.
    stripped = text.strip()
    if len(stripped) <= chunk_size:
        chunks = [stripped]
        return chunks

    # Split using the current separator.
    separator = separators[index]
    pieces = _split_keep_separator(stripped, separator)

    # Advance to the next separator if splitting made no progress.
    if len(pieces) == 1 and pieces[0] == stripped:
        recursive_chunks = _recursive_split(stripped, chunk_size, separators, index + 1)
        return recursive_chunks

    # Recursively split any oversized pieces.
    split_pieces: list[str] = []
    for piece in pieces:
        current = piece.strip()
        if len(current) <= chunk_size:
            split_pieces.append(current)
        else:
            # Recurse with the next separator for oversized pieces.
            recursive_pieces = _recursive_split(current, chunk_size, separators, index + 1)
            split_pieces.extend(recursive_pieces)

    # Merge adjacent pieces greedily while respecting chunk_size.
    merged: list[str] = []
    for piece in split_pieces:
        if not merged:
            merged.append(piece)
            continue
        candidate = f"{merged[-1]} {piece}"
        if len(candidate) <= chunk_size:
            merged[-1] = candidate
        else:
            merged.append(piece)

    # Return the merged chunks.
    return merged


def _build_sentence_overlap(previous_chunk: str, chunk_overlap: int) -> str:
    """
    Description: Build a sentence-aligned overlap from the previous chunk.

    Arguments:
        previous_chunk (str): Previous chunk to draw overlap from.
        chunk_overlap (int): Maximum overlap length in characters.

    Returns:
        str: Sentence-aligned overlap text within the configured limit.

    Example:
        >>> _build_sentence_overlap("One. Two.", 4)
        'Two.'
    """
    # Split the previous chunk into sentences.
    sentences = split_sentences(previous_chunk)

    # Collect trailing sentences within the overlap budget.
    tail_parts: list[str] = []
    for sentence in reversed(sentences):
        candidate_parts = list(tail_parts)
        candidate_parts.append(sentence)
        candidate = " ".join(candidate_parts)
        if len(candidate) <= chunk_overlap:
            tail_parts.insert(0, sentence)
        else:
            break

    # Join the selected overlap sentences.
    joined_tail = " ".join(tail_parts)
    overlap = joined_tail.strip()

    # Return the overlap text.
    return overlap


def split_recursive(
    text: str, chunk_size: int, chunk_overlap: int, separators: list[str]
) -> list[str]:
    """
    Description: Recursively split text, merge greedily, and apply overlap.

    Arguments:
        text (str): Input text.
        chunk_size (int): Maximum chunk length.
        chunk_overlap (int): Overlap length limit in characters.
        separators (list[str]): Ordered list of separators.

    Returns:
        list[str]: Final chunk list.

    Example:
        >>> split_recursive("A. B. C.", 6, 2, [". ", " "])
        ['A. B.', 'B. C.']
    """
    # Split the input text into chunks.
    chunks = _recursive_split(text=text, chunk_size=chunk_size, separators=separators, index=0)
    chunk_count = len(chunks)

    # Initialize overlap output with the first chunk.
    with_overlap: list[str] = [chunks[0]]
    chunk_indices = range(1, chunk_count)

    # Add sentence overlap to each subsequent chunk when it fits.
    for idx in chunk_indices:
        overlap_tail = _build_sentence_overlap(chunks[idx - 1], chunk_overlap)
        current = chunks[idx]
        candidate = f"{overlap_tail} {current}".strip()
        if len(candidate) <= chunk_size:
            current = candidate
        with_overlap.append(current)

    # Return the chunks with overlap.
    return with_overlap


def chunk_section(paragraphs: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Description: Chunk a section after joining paragraphs with hard boundaries.

    Arguments:
        paragraphs (list[str]): Section paragraphs.
        chunk_size (int): Maximum chunk length.
        chunk_overlap (int): Overlap length limit in characters.

    Returns:
        list[str]: Chunks for the section.

    Example:
        >>> chunk_section(["A", "B"], 20, 0)
        ['A\\n\\nB']
    """
    # Join section paragraphs with hard section boundaries preserved.
    joined_text = "\n\n".join(paragraphs)
    section_text = joined_text.strip()

    # Split the section text and apply overlap.
    chunks = split_recursive(
        text=section_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
    )

    # Return the section chunks.
    return chunks
