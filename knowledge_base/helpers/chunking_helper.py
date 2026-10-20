import re

CHUNK_SIZE = 400
CHUNK_OVERLAP = 60
SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", " "]

_ABBREVIATIONS = {"e.g", "i.e", "etc", "dr", "mr", "nr", "no", "vs"}


def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences with abbreviation and decimal guards.

    Arguments:
        text (str): Input text.

    Returns:
        list[str]: Sentence list.

    Example:
        >>> split_sentences("Dr. Smith arrived. He spoke.")
        ['Dr. Smith arrived.', 'He spoke.']
    """
    stripped = text.strip()
    if not stripped:
        sentences = []
        return sentences

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

    if not boundaries:
        sentences = [stripped]
        return sentences

    sentences: list[str] = []
    start = 0
    for end in boundaries:
        raw_part = stripped[start:end]
        part = raw_part.strip()
        sentences.append(part)
        start = end

    raw_remainder = stripped[start:]
    remainder = raw_remainder.strip()
    sentences.append(remainder)
    return sentences


def _split_keep_separator(text: str, separator: str) -> list[str]:
    raw_parts = text.split(separator)
    pieces: list[str] = []
    for idx, piece in enumerate(raw_parts):
        if not piece:
            continue
        if idx < len(raw_parts) - 1:
            joined_piece = f"{piece}{separator}"
            cleaned_piece = joined_piece.strip()
            pieces.append(cleaned_piece)
        else:
            cleaned_piece = piece.strip()
            pieces.append(cleaned_piece)
    return pieces


def _recursive_split(text: str, chunk_size: int, separators: list[str], index: int) -> list[str]:
    stripped = text.strip()
    if not stripped:
        chunks = []
        return chunks
    if len(stripped) <= chunk_size:
        chunks = [stripped]
        return chunks
    if index >= len(separators):
        chunks = [stripped]
        return chunks

    separator = separators[index]
    pieces = _split_keep_separator(stripped, separator)
    if len(pieces) == 1 and pieces[0] == stripped:
        recursive_chunks = _recursive_split(stripped, chunk_size, separators, index + 1)
        return recursive_chunks

    split_pieces: list[str] = []
    for piece in pieces:
        current = piece.strip()
        if not current:
            continue
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
    return merged


def _build_sentence_overlap(previous_chunk: str, chunk_overlap: int) -> str:
    sentences = split_sentences(previous_chunk)
    tail_parts: list[str] = []
    # Grow overlap from sentence boundaries while staying within overlap budget.
    for sentence in reversed(sentences):
        if not tail_parts:
            candidate = sentence
        else:
            joined_tail = " ".join(tail_parts)
            candidate = f"{joined_tail} {sentence}"
        if len(candidate) <= chunk_overlap:
            tail_parts.insert(0, sentence)
        else:
            break
    joined_tail = " ".join(tail_parts)
    overlap = joined_tail.strip()
    return overlap


def split_recursive(
    text: str, chunk_size: int, chunk_overlap: int, separators: list[str]
) -> list[str]:
    """
    Recursively split text by separators, merge greedily, and apply overlap.

    Arguments:
        text (str): Input text.
        chunk_size (int): Maximum chunk length.
        chunk_overlap (int): Overlap length limit in characters.
        separators (list[str]): Ordered list of separators.

    Returns:
        list[str]: Final chunk list.

    Example:
        >>> split_recursive("A. B. C.", 6, 2, [". ", " "])
        ['A. B.', 'C.']
    """
    chunks = _recursive_split(text=text, chunk_size=chunk_size, separators=separators, index=0)
    if not chunks:
        return chunks
    chunk_count = len(chunks)

    with_overlap: list[str] = [chunks[0]]
    chunk_indices = range(1, chunk_count)
    for idx in chunk_indices:
        overlap_tail = _build_sentence_overlap(chunks[idx - 1], chunk_overlap)
        current = chunks[idx]
        if overlap_tail:
            candidate = f"{overlap_tail} {current}"
            if len(candidate) <= chunk_size:
                current = candidate
        with_overlap.append(current)
    return with_overlap


def chunk_section(paragraphs: list[str], chunk_size: int, chunk_overlap: int) -> list[str]:
    """
    Chunk a single section by joining paragraphs with a hard boundary.

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
    if not section_text:
        chunks = []
        return chunks
    chunks = split_recursive(
        text=section_text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=SEPARATORS,
    )
    return chunks
