from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
import httpx
from app.resources import context as r

class OpenAIProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def generate_response(self, prompt: str) -> LLmResponse:
        """
        Call OpenAI Chat Completions API using the official SDK.
        """
        logger = r.logger
        model = self.config.model_name or "gpt-4o-mini"
        API_URL = "https://api.openai.com/v1"

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                resp = await client.post(
                    f"{API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = ""
                if data and data.get("choices"):
                    msg = data["choices"][0]["message"]
                    content = msg.get("content", "")
                return LLmResponse(content=content, provider_name=self.config.provider_name, model_name=model)
        except Exception:
            logger.exception("OpenAI call failed")
            return LLmResponse(content="", provider_name=self.config.provider_name, model_name=model)