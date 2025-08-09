from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
import httpx
from app.resources import context as r

class MetaProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.API_URL = "https://api.llama.meta.com/v1"

    async def generate_response(self, prompt: str) -> LLmResponse:
        """
        Call Meta Llama API via REST if api_url provided.
        """
        logger = r.logger
        model = self.config.model_name or "llama-3.1-8b-instruct"
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                resp = await client.post(
                    f"{self.API_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {self.config.api_key}"},
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
            logger.exception("Meta call failed")
            return LLmResponse(content="", provider_name=self.config.provider_name, model_name=model)
