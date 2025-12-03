# backend/app/services/llm_client.py
import os
from typing import Optional

from openai import OpenAI


class LLMClient:
    def __init__(self, provider: str = "openai"):
        if provider != "openai":
            raise ValueError("Only 'openai' provider is supported in this setup.")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # No key: run in "disabled" mode; callers must handle gracefully.
            self.client: Optional[OpenAI] = None
            self.model = None
            self.enabled = False
        else:
            self.client = OpenAI(api_key=api_key)
            self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.enabled = True

    def generate(self, prompt: str) -> str:
        """
        Generate LLM output.

        Behaviour:
        - If no API key: return a static explanatory string.
        - If OpenAI throws (rate limit, network error, etc.): return a
          human-readable fallback instead of raising, so the API never 500s.
        """
        if not self.enabled or not self.client or not self.model:
            return (
                "LLM analysis is disabled (no OPENAI_API_KEY configured on server). "
                "Core risk scoring and dashboards still work."
            )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fraud risk and behavior analysis assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            # Fallback for rate limits, network errors, etc.
            # We DON'T raise, we just return a text explanation that the caller
            # can display to the analyst instead of blowing up the endpoint.
            err_type = e.__class__.__name__
            return (
                f"LLM analysis temporarily unavailable ({err_type}). "
                "This usually means rate limiting or a transient API error. "
                "You can retry later; core fraud scores are still valid."
            )
