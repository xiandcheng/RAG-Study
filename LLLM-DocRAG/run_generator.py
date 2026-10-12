from app.retriever import Retriever
from app.prompt_builder import PromptBuilder
from app.embedding import EmbeddingModel
from app.vector_store import FAISSVectorStore
from pathlib import Path
from app.generator import LLMGenerator
import os

api_key=os.getenv("DEEPSEEK_API_KEY")
path = Path("data/vector_store")
base_url = "https://api.deepseek.com"
model_name = "deepseek-flash"
faiss_vectors = FAISSVectorStore(dimension=1024)
store = faiss_vectors.load(path)
embedding = EmbeddingModel()
prompt_builder = PromptBuilder()
generator = LLMGenerator(api_key,base_url,model_name)
retriever = Retriever(embedding,store)


query = "What is LoRA?"

results = retriever.retrieve(query, top_k=3)
messages = prompt_builder.build(query, results)
print(messages)
print('-'*30)
answer = generator.generate(messages)

print(answer)
