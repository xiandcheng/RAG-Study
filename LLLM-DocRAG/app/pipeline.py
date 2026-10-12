from app.prompt_builder import PromptBuilder
from app.generator import LLMGenerator
from app.retriever import Retriever


class RAGPipeline:

    def __init__(self, retriever: Retriever, prompt_builder: PromptBuilder, generator: LLMGenerator):
        self.retriever = retriever
        self.prompt_builder = prompt_builder
        self.generator = generator


    def ask(self, query: str, top_k: int = 3) -> str:
        results = self.retriever.retrieve(query, top_k=top_k)
        messages = self.prompt_builder.build(query, results)
        answer = self.generator.generate(messages)

        return answer
