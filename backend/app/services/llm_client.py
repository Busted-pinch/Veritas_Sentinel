# backend/app/services/llm_client.py
import os
from openai import OpenAI

class LLMClient:
    def __init__(self, provider: str = "openai"):
        if provider != "openai":
            raise ValueError("Only 'openai' provider is supported in this setup.")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment.")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a fraud risk and behavior analysis assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
