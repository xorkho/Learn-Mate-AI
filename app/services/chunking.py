def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    """
    Simple recursive-style chunking without LangChain.
    Splits on paragraphs first, then falls back to raw character slicing with overlap.
    """
    # Pehle paragraphs pe split karo
    paragraphs = text.split("\n\n")
    
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Agar current chunk + naya paragraph limit se bada ho jaye
        if len(current_chunk) + len(para) > chunk_size:
            if current_chunk:
                chunks.append(current_chunk.strip())
            # Overlap ke liye last kuch characters rakho
            overlap_text = current_chunk[-chunk_overlap:] if current_chunk else ""
            current_chunk = overlap_text + " " + para
        else:
            current_chunk += " " + para

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Agar koi chunk bhi chunk_size se bohot bada reh gaya (long paragraph), usko aur todo
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= chunk_size * 1.5:  # thoda tolerance
            final_chunks.append(chunk)
        else:
            # Simple character-based split with overlap
            start = 0
            while start < len(chunk):
                end = start + chunk_size
                final_chunks.append(chunk[start:end])
                start += chunk_size - chunk_overlap

    return final_chunks