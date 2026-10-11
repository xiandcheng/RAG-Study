from app.embedding import EmbeddingModel
from app.vector_store import FAISSVectorStore
from app.schemas import DocumentChunk


class Retriever:

    def __init__(self, embedding_model: EmbeddingModel, vector_store: FAISSVectorStore):
        self.model = embedding_model
        self.vector_store = vector_store

    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[DocumentChunk, float]]:
        query_embedding = self.model.encode_query(query)
        return self.vector_store.search(query_embedding, top_k=top_k)

