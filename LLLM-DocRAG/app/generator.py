from openai import OpenAI
from collections.abc import Iterator

class LLMGenerator:

    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate(self, messages: list[dict[str, str]]) -> str:
        response = self.client.chat.completions.create(messages = messages ,model = self.model_name)
        return response.choices[0].message.content or ""

    def generate_stream(self, messages: list[dict[str, str]]) -> Iterator[str]:
        stream = self.client.chat.completions.create(model=self.model_name,messages=messages,stream=True)
        for event in stream:
            if not event.choices:
                continue

            content = event.choices[0].delta.content

            if content:
                yield content
