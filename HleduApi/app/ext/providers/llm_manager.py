from typing import Optional
from app.ext.providers.gemini import GeminiProvider
from app.ext.providers.grok import GrokProvider
from app.ext.providers.meta import MetaProvider
from app.ext.providers.openai import OpenAIProvider
from app.ext.providers.base import ProviderConfig, BaseProvider, LLmResponse
from app.resources import context as r
from app.service.provider import load_and_get_provider, get_cached_provider
from fastapi import HTTPException


class LLMManager:
    """
    LLM facade that calls underlying active provider with a given prompt.
    The active provider is obtained from service cache.
    """

    def __init__(self) -> None:
        self._provider: Optional[BaseProvider] = None

    async def _ensure_provider(self) -> BaseProvider:
        if self._provider is not None:
            return self._provider

        cached = await get_cached_provider()
        provider = cached.get() if cached else None
        if provider is None:
            result = await load_and_get_provider()
            provider = result.get() if result else None
        if provider is None:
            raise HTTPException(status_code=500, detail="No active provider configured")

        name = (provider.name or "").lower()
        model = None
        if provider.ai_models:
            active_models = [m for m in provider.ai_models if m.is_active]
            model = active_models[0].name if active_models else None

        config = ProviderConfig(
            provider_name=provider.name,
            api_key=provider.api_key,
            model=model,
        )

        if "openai" in name:
            self._provider = OpenAIProvider(config)
        elif "meta" in name or "llama" in name:
            self._provider = MetaProvider(config)
        elif "grok" in name or "groq" in name:
            self._provider = GrokProvider(config)
        elif "gemini" in name or "google" in name:
            self._provider = GeminiProvider(config)
        else:
            self._provider = OpenAIProvider(config)

        r.logger.debug(f"Initialized provider: {self._provider.__class__.__name__}")
        return self._provider

    async def generate(self, prompt: str) -> LLmResponse:
        provider = await self._ensure_provider()
        return await provider.generate_response(prompt)