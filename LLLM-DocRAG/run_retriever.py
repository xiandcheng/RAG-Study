from pathlib import Path
from app.embedding import EmbeddingModel
from app.vector_store import FAISSVectorStore
from app.retriever import Retriever
from app.prompt_builder import PromptBuilder

model = EmbeddingModel()
store = FAISSVectorStore.load(Path("data/vector_store"))
retriever = Retriever(model, store)

builder = PromptBuilder()

results = retriever.retrieve("What is LoRA?", top_k=3)
messages = builder.build("What is LoRA?", results)

assert len(messages) == 2
assert messages[0]["role"] == "system"
assert messages[1]["role"] == "user"

print("========== SYSTEM ==========")
print(messages[0]["content"])

print("\n========== USER ==========")
print(messages[1]["content"])
