from site_search.chunker import chunk_text


def test_empty_text_returns_empty_list() -> None:
    assert chunk_text("") == []


def test_whitespace_only_text_returns_empty_list() -> None:
    assert chunk_text("   \n\n   \n\n  ") == []


def test_single_short_paragraph_produces_one_chunk() -> None:
    text = "The Kenyan court halted deportation flights on Thursday."
    result = chunk_text(text)
    assert len(result) == 1
    assert result[0] == text


def test_multiple_short_paragraphs_accumulate_into_one_chunk() -> None:
    para_a = "A" * 300
    para_b = "B" * 300
    text = f"{para_a}\n\n{para_b}"
    result = chunk_text(text, target_size=800)
    assert len(result) == 1
    assert para_a in result[0]
    assert para_b in result[0]


def test_paragraphs_split_across_chunks_when_exceeding_target() -> None:
    para_a = "A" * 500
    para_b = "B" * 500
    text = f"{para_a}\n\n{para_b}"
    result = chunk_text(text, target_size=800)
    assert len(result) == 2
    assert para_a in result[0]
    assert para_b in result[1]


def test_long_paragraph_split_at_sentence_boundary() -> None:
    first = "X" * 1100 + "."
    second = "Y" * 200 + "."
    para = first + " " + second  # 1303 chars, exceeds max_size=1200
    result = chunk_text(para, target_size=800, max_size=1200)
    assert len(result) >= 2
    assert any("X" in chunk for chunk in result)
    assert any("Y" in chunk for chunk in result)
    for chunk in result:
        assert len(chunk) <= 1200


def test_long_paragraph_hard_split_when_no_sentence_boundary() -> None:
    para = "A" * 1500  # no sentence boundary, exceeds max_size=1200
    result = chunk_text(para, target_size=800, max_size=1200)
    assert len(result) >= 2
    for chunk in result:
        assert len(chunk) <= 1200


def test_no_chunk_exceeds_max_size() -> None:
    parts = ["Normal paragraph. " * 10] * 3 + ["A" * 1500] + ["Short bit."] * 5
    text = "\n\n".join(parts)
    result = chunk_text(text, target_size=800, max_size=1200)
    for chunk in result:
        assert len(chunk) <= 1200
