import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from app.schemas import DocumentChunk

class EmbeddingModel:

    def __init__(self, model_name: str = "BAAI/bge-m3", device: str | None = None, batch_size: int = 16):
        """
        加载模型、选择设备
        :param model_name:
        :param device:
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SentenceTransformer(model_name,device=self.device)
        self.batch_size = batch_size

    def encode_documents(self, chunks: list[DocumentChunk]) -> np.ndarray:
        """
        批量编码 Chunk
        :param chunks:
        :return:
        """
        if not chunks:
            dim = self.model.get_embedding_dimension()
            return np.empty((0, dim), dtype=np.float32)
        texts: list[str] = []
        for chunk in chunks:
            heading = " > ".join(chunk.metadata.get("heading_path", []))
            text = f"{heading}\n\n{chunk.content}" if heading else chunk.content
            texts.append(text)
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        return embeddings

    def encode_query(self, query: str) -> np.ndarray:
        """
        编码用户问题
        :param query:
        :return:
        """
        if not query.strip():
            raise ValueError("query 不能为空")
        embeddings = self.model.encode(
            query,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return embeddings

