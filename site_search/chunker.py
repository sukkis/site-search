def chunk_text(text: str, target_size: int = 800, max_size: int = 1200) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    paragraphs = [p for p in paragraphs if p]

    chunks: list[str] = []
    current: list[str] = []
    current_len: int = 0

    for para in paragraphs:
        if len(para) > max_size:
            if current:
                chunks.append("\n\n".join(current))
                current = []
                current_len = 0
            chunks.extend(_split_long_paragraph(para, max_size))
        elif current_len + len(para) > target_size and current:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def _split_long_paragraph(text: str, max_size: int) -> list[str]:
    if len(text) <= max_size:
        return [text]

    split_pos = text.rfind(". ", 0, max_size)

    if split_pos == -1:
        return [text[:max_size]] + _split_long_paragraph(text[max_size:], max_size)

    first = text[: split_pos + 1]
    rest = text[split_pos + 2 :].strip()
    return [first] + _split_long_paragraph(rest, max_size)
