import asyncio
import json
import random
from typing import Dict, Any
import httpx
from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
from app.resources import context as r

class GrokProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.API_URL = "https://api.groq.com/openai/v1"

    async def generate_response(self, prompt_or_payload) -> LLmResponse:
        """
        Call Groq API with JSON mode support.
        Based on official documentation: https://console.groq.com/docs/api-reference
        """
        logger = r.logger
        model = self.config.model or "llama-3.3-70b-versatile"
        timeout = httpx.Timeout(self.config.timeout_seconds)
        headers = {"Authorization": f"Bearer {self.config.api_key}", "Content-Type": "application/json"}
        
        if isinstance(prompt_or_payload, dict):
            messages = prompt_or_payload["messages"]
        else:
            messages = [
                {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                {"role": "user", "content": str(prompt_or_payload)}
            ]

        body = {
            "model": model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(f"{self.API_URL}/chat/completions", headers=headers, json=body)
                resp.raise_for_status()
                data = resp.json()
                msg = data.get("choices", [{}])[0].get("message", {})
                content = msg.get("content", "")
                return LLmResponse(content=content, provider_name=self.config.provider_name, model=model)
            except httpx.HTTPStatusError as e:
                code = e.response.status_code if e.response is not None else None
                if code in (429, 500, 502, 503, 504):
                    await asyncio.sleep((2 ** attempt) + random.random())
                    continue
                logger.exception("Grok HTTP error")
                break
            except Exception:
                logger.exception("Grok call failed")
                await asyncio.sleep((2 ** attempt) + random.random())
                continue
        return LLmResponse(content="", provider_name=self.config.provider_name, model=model)

    def parse_writing_response(self, raw_content: str) -> Dict[str, Any]:
        logger = r.logger
        try:
            data = json.loads(raw_content) if isinstance(raw_content, str) else raw_content
            return {
                "overall_score": self._parse_score(data.get("overall_score")),
                "grammar_score": self._parse_score(data.get("grammar_score")),
                "vocabulary_score": self._parse_score(data.get("vocabulary_score")),
                "coherence_score": self._parse_score(data.get("coherence_score")),
                "content_score": self._parse_score(data.get("content_score")),
                "general_feedback": data.get("general_feedback", ""),
                "detailed_feedback": data.get("detailed_feedback", ""),
                "grammar_errors": data.get("grammar_errors"),
                "grammar_improvements": self._coerce_optional_str_list(data.get("grammar_improvements")),
                "vocabulary_suggestions": data.get("vocabulary_suggestions"),
                "vocabulary_improvements": self._coerce_optional_str_list(data.get("vocabulary_improvements")),
                "improvement_suggestions": self._coerce_optional_str_list(data.get("improvement_suggestions")),
                "suggested": data.get("suggested")
            }
        except json.JSONDecodeError:
            logger.error("Failed to parse Grok JSON response")
            return self._error_response()
        except Exception:
            logger.exception("Error parsing Grok writing response")
            return self._error_response()

    def _parse_score(self, value: Any) -> float:
        try:
            if isinstance(value, str):
                text = value.strip()
                if "/" in text:
                    text = text.split("/", 1)[0]
                parsed = float(text)
            elif isinstance(value, (int, float)):
                parsed = float(value)
            else:
                parsed = 0.0
        except Exception:
            parsed = 0.0
        return max(0.0, min(10.0, parsed))

    def _coerce_optional_str_list(self, value: Any):
        if value is None:
            return None
        if isinstance(value, str):
            t = value.strip()
            return [t] if t else None
        if isinstance(value, list):
            out = [str(item) for item in value if item is not None]
            return out if out else None
        return None


    def _error_response(self) -> Dict[str, Any]:
        return {
            "overall_score": 0.0,
            "grammar_score": 0.0,
            "vocabulary_score": 0.0,
            "coherence_score": 0.0,
            "content_score": 0.0,
            "general_feedback": "Failed to parse AI response.",
            "detailed_feedback": "There was an error processing the assessment response.",
            "grammar_errors": [],
            "grammar_improvements": [],
            "vocabulary_suggestions": [],
            "vocabulary_improvements": [],
            "improvement_suggestions": [],
            "suggested": ""
        }