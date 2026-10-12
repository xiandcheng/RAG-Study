from app.pipeline import RAGPipeline
from app.prompt_builder import PromptBuilder
from app.generator import LLMGenerator
from app.retriever import Retriever
from pathlib import Path
from app.vector_store import FAISSVectorStore
from app.embedding import EmbeddingModel
import os


api_key=os.getenv("DEEPSEEK_API_KEY")
path = Path("data/vector_store")
base_url = "https://api.deepseek.com"
model_name = "deepseek-flash"
store= FAISSVectorStore.load(path)
embedding = EmbeddingModel()
prompt_builder = PromptBuilder()
retriever = Retriever(embedding,store)
generator = LLMGenerator(api_key,base_url,model_name)

rag = RAGPipeline(retriever,prompt_builder,generator)
answer = rag.ask("LoRA 为什么能够减少模型的可训练参数？", top_k=3)
print(answer)
