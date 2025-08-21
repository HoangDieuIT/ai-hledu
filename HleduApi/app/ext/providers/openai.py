from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
import httpx
from app.resources import context as r
import json
from typing import Dict, Any, List

class OpenAIProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def generate_response(self, prompt_or_payload) -> LLmResponse:
        """
        Call OpenAI Chat Completions API with JSON mode.
        Based on official documentation: https://platform.openai.com/docs/api-reference/chat
        """
        logger = r.logger
        model = self.config.model or "gpt-4o"
        API_URL = "https://api.openai.com/v1"

        try:
            if isinstance(prompt_or_payload, dict):
                messages = prompt_or_payload["messages"]
            else:
                messages = [
                    {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                    {"role": "user", "content": str(prompt_or_payload)}
                ]

            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                resp = await client.post(
                    f"{API_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": self.config.temperature or 0.7,
                        "max_tokens": self.config.max_tokens or 2048,
                        "response_format": {"type": "json_object"}
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                content = ""
                if data and data.get("choices"):
                    msg = data["choices"][0]["message"]
                    content = msg.get("content", "")
                return LLmResponse(content=content, provider_name=self.config.provider_name, model=model)
                
        except Exception:
            logger.exception("OpenAI call failed")
            return LLmResponse(content="", provider_name=self.config.provider_name, model=model)

    def parse_writing_response(self, raw_content: str) -> Dict[str, Any]:
        """Parse OpenAI response for writing assessment."""
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
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            return self._error_response()
        except Exception as e:
            logger.error(f"Error parsing OpenAI writing response: {e}")
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

    def _coerce_optional_str_list(self, value: Any) -> List[str] | None:
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