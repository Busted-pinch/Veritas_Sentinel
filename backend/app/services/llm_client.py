import os
import requests
from openai import OpenAI


class LLMClient:
    def __init__(self, provider="openai"):
        self.provider = provider

        if provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        elif provider == "ollama":
            self.model = os.getenv("OLLAMA_MODEL", "llama3")
            self.url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")

        else:
            raise ValueError("Unknown LLM provider")

    def generate(self, prompt: str):
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a fraud speculation AI."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return response.choices[0].message.content.strip()

        if self.provider == "ollama":
            response = requests.post(
                self.url,
                json={"model": self.model, "prompt": prompt, "temperature": 0.2},
                timeout=60
            )
            return response.json()["response"]
