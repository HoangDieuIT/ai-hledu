from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
from typing import Optional
import httpx
from app.resources import context as r

class GeminiProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def generate_response(self, prompt: str) -> LLmResponse:
        """
        Call Google GenAI client (google-genai).
        """
        logger = r.logger
        model = self.config.model_name or "gemini-2.0-flash"
        BASE = "https://generativelanguage.googleapis.com/v1beta"
        endpoint = f"{BASE}/models/{model}:generateContent"

        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                resp = await client.post(
                    endpoint,
                    headers={"Content-Type": "application/json"},
                    params={"key": self.config.api_key},
                    json={
                        "contents": [
                            {
                                "role": "user",
                                "parts": [{"text": prompt}],
                            }
                        ],
                        "generationConfig": {
                            "temperature": self.config.temperature,
                            "maxOutputTokens": self.config.max_tokens,
                        },
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = ""
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    texts = [p.get("text", "") for p in parts]
                    content = "\n".join([t for t in texts if t])
                return LLmResponse(content=content, provider_name=self.config.provider_name, model_name=model)
        except Exception:
            logger.exception("Gemini call failed")
            return LLmResponse(content="", provider_name=self.config.provider_name, model_name=model)