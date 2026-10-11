import tiktoken
import torch
from sentence_transformers import SentenceTransformer
from app.chunker import SectionChunker
from app.schemas import DocumentChunk
from app.storage import EmbeddingModel
from app.parser import MarkdownParser
import numpy as np
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
embeddings = embedding_model.encode_documents(all_chunks[:3])

print("Shape:", embeddings.shape)
print("Dtype:", embeddings.dtype)
print("Norm:", np.linalg.norm(embeddings, axis=1))
