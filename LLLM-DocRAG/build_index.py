from app.chunker import SectionChunker
from app.embedding import EmbeddingModel
from app.parser import MarkdownParser
from app.vector_store import FAISSVectorStore
from pathlib import Path

parser = MarkdownParser()
chunker = SectionChunker(chunk_size=2048, chunk_overlap=256)
paths = sorted(Path("data/raw").rglob("*.md"))
all_chunks = []
total_sections = 0
for path in paths:
    document = parser.parse(path)
    total_sections += len(document.sections)
    chunks = chunker.chunk_document(document, start_id=len(all_chunks) + 1)
    all_chunks.extend(chunks)


embedding_model = EmbeddingModel()
embeddings = embedding_model.encode_documents(all_chunks)


store = FAISSVectorStore()
store.add(embeddings, all_chunks)
store.save(Path("data/vector_store"))
