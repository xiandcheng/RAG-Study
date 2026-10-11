import faiss
import numpy as np
from app.schemas import DocumentChunk
from pathlib import Path
import json
from dataclasses import asdict
class FAISSVectorStore:

    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.chunks : list[DocumentChunk] = []

    def add(self, embeddings: np.ndarray, chunks: list[DocumentChunk]) -> None:
        if embeddings.shape != (len(chunks), self.dimension):
            raise ValueError("Embedding Shape 与 Chunk 数量或向量维度不匹配")

        if not chunks:
            return

        embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        self.index.add(embeddings)
        self.chunks.extend(chunks)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[tuple[DocumentChunk, float]]:

        if top_k <=0:
            raise ValueError("top_k不能小于等于0")
        if self.index.ntotal == 0:
            return []
        results: list[tuple[DocumentChunk, float]] = []
        query_vectors = np.asarray(query_embedding, dtype=np.float32).reshape(1, -1)
        query_vectors = np.ascontiguousarray(query_vectors)
        if query_vectors.shape != (1, self.dimension):
            raise ValueError("query_embedding 形状不正确")
        k = min(top_k, self.index.ntotal)
        scores,indices = self.index.search(query_vectors, k)
        for index_id, score in zip(indices[0], scores[0]):
            chunk = self.chunks[int(index_id)]
            results.append((chunk, float(score)))

        return results

    def save(self, path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))
        data = [asdict(chunk) for chunk in self.chunks]

        json_text = json.dumps(data, ensure_ascii=False, indent=2)
        (path / "chunks.json").write_text(json_text, encoding="utf-8")


    @classmethod
    def load(cls, path: Path) -> "FAISSVectorStore":
        index = faiss.read_index(str(path / "index.faiss"))
        json_text = (path / "chunks.json").read_text(encoding="utf-8")
        data = json.loads(json_text)
        chunks = [DocumentChunk(**item) for item in data]

        store = cls(dimension=index.d)
        store.index = index
        store.chunks = chunks
        if store.index.ntotal != len(store.chunks):
            raise ValueError("FAISS 向量数量与 Chunk 数量不一致")
        return store

