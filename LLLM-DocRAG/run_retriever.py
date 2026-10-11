from pathlib import Path
from app.embedding import EmbeddingModel
from app.vector_store import FAISSVectorStore
from app.retriever import Retriever

model = EmbeddingModel()
store = FAISSVectorStore.load(Path("data/vector_store"))
retriever = Retriever(model, store)

query = "LoRA 如何减少可训练参数？"

for k in [1, 3, 5]:
    results = retriever.retrieve(query, top_k=k)
    print(f"Top-{k}: {len(results)} 条")
    assert len(results) == k
