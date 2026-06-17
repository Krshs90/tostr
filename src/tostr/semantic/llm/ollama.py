from __future__ import annotations
from pydantic import BaseModel
from tostr.semantic.llm.base import LLMStrategy
from typing import Type

class OllamaStrategy(LLMStrategy):
    def __init__(self, api_key: str = "", model_name: str = "llama3", base_url: str = "http://localhost:11434", max_concurrent_requests: int = 10):
        import ollama
        super().__init__(api_key, model_name, max_concurrent_requests)
        self.client = ollama.AsyncClient(host=base_url)
        self.model_name = model_name

    async def generate(self, input_data_string: str, system_instruction: str, response_schema: Type[BaseModel]):
        try:
            # Note: LLMClient handles retries and semaphore
            response = await self.client.chat(
                model=self.model_name,
                messages=[
                    {'role': 'system', 'content': system_instruction},
                    {'role': 'user', 'content': input_data_string}
                ],
                format=response_schema.model_json_schema(),
                options={
                    "temperature": 0.2,
                    "num_ctx": 8192
                }
            )

            return response_schema.model_validate_json(response['message']['content'])
        except Exception as e:
            # Re-raise to let LLMClient handle retries
            raise e
