from app.chunker import SectionChunker
from app.schemas import DocumentSection


def test_split_long_section():
    chunker = SectionChunker(chunk_size=128, chunk_overlap=32)

    section = DocumentSection(
        title="Test",
        level=1,
        content="LoRA is a fine-tuning method. " * 100,
        heading_path=["PEFT", "LoRA", "Test"]
    )

    chunks = chunker._split_section(section)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(chunker._count_tokens(chunk) <= 128 for chunk in chunks)
