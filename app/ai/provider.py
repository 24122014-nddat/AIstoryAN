from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod

from app.config import get_settings


class TextProvider(ABC):
    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        raise NotImplementedError


class MockProvider(TextProvider):
    async def generate_text(self, prompt: str) -> str:
        return (
            "Màn sương mở ra trên một vùng đất xa lạ. Bạn tỉnh dậy giữa tiếng gió, "
            "trong tay còn giữ một vật nhỏ mà chính bạn cũng chưa hiểu vì sao nó quan trọng.\n\n"
            "Bạn có thể quan sát xung quanh, gọi thử xem có ai đáp lại, hoặc tự chọn một hướng để đi."
        )


class OpenAIProvider(TextProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("Missing OPENAI_API_KEY in .env")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.text_model

    async def generate_text(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
        return response.choices[0].message.content or ""


class GeminiProvider(TextProvider):
    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("Missing GEMINI_API_KEY in .env")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.text_model

    async def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(model=self.model, contents=prompt)
        return response.text or ""


class OllamaProvider(TextProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.text_model

    async def generate_text(self, prompt: str) -> str:
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data.get("response", "")
class GroqProvider(TextProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI

        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY in .env")

        # Groq dùng OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = settings.text_model

    async def generate_text(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
        return response.choices[0].message.content or ""


def get_text_provider() -> TextProvider:
    provider = get_settings().text_provider.lower().strip()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "ollama":
        return OllamaProvider()
    if provider == "groq": 
        return GroqProvider()
    return MockProvider()
