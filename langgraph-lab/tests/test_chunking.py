"""عقد التقطيع: حتمي، واعٍ للعناوين، بحدود ثابتة."""

from app.knowledge.chunking import doc_key_for, split_markdown


def test_same_input_same_chunks() -> None:
    text = "# درس الكسور\n\nالبسط فوق المقام.\n\n## أمثلة\n\n1/2 نصف."
    first = split_markdown(text)
    second = split_markdown(text)
    assert first == second
    assert all(c.text for c in first)


def test_heading_starts_new_chunk_with_title() -> None:
    text = "# الكسور\n\nنص أول.\n\n# الجمع\n\nنص ثان."
    chunks = split_markdown(text, max_chars=500)
    assert [c.title for c in chunks] == ["الكسور", "الجمع"]
    assert chunks[0].index == 0 and chunks[1].index == 1


def test_long_section_splits_with_overlap() -> None:
    words = [f"كلمة{i}" for i in range(200)]
    chunks = split_markdown("# درس\n\n" + " ".join(words), max_chars=300, overlap_words=10)
    assert len(chunks) > 1
    assert all(len(c.text) <= 300 for c in chunks)
    first_tail = first_words = chunks[0].text.split()[-10:]
    assert first_words == chunks[1].text.split()[:10]
    assert first_tail


def test_empty_and_tiny_text() -> None:
    assert split_markdown("") == []
    assert split_markdown("   \n  ") == []
    chunks = split_markdown("نص بلا عنوان.")
    assert len(chunks) == 1 and chunks[0].title == ""


def test_token_count_is_word_count() -> None:
    (chunk,) = split_markdown("# ت\n\nأ ب ج")
    assert chunk.token_count == 3


def test_doc_key_stable_from_relpath() -> None:
    assert doc_key_for("textbook/primary/primary_4/x/part-01.md") == doc_key_for(
        "textbook\\primary\\primary_4\\x\\part-01.md"
    )
    assert len(doc_key_for("a/b.md")) == 64
