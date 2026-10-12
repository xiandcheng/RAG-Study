from openai import OpenAI


class LLMGenerator:

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(messages = messages ,model = self.model_name)
        return response.choices[0].message.content or ""
