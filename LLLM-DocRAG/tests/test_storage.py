import numpy as np
from app.storage import EmbeddingModel
import tiktoken
import torch
from sentence_transformers import SentenceTransformer
from app.chunker import SectionChunker
from app.schemas import DocumentChunk
from app.storage import EmbeddingModel
from app.parser import MarkdownParser
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
model = EmbeddingModel()

document_vectors = model.encode_documents(all_chunks[:3])
query_vector = model.encode_query("What is LoRA?")

print("Document Embeddings:", document_vectors.shape)
print("Query Embedding:", query_vector.shape)

print("Document Norms:", np.linalg.norm(document_vectors, axis=1))
print("Query Norm:", np.linalg.norm(query_vector))

scores = document_vectors @ query_vector
print("Similarity Scores:", scores)

assert document_vectors.shape == (3, 1024)
assert query_vector.shape == (1024,)
assert np.allclose(np.linalg.norm(document_vectors, axis=1), 1.0, atol=1e-5)
assert np.isclose(np.linalg.norm(query_vector), 1.0, atol=1e-5)
