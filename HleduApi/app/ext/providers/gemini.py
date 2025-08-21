import json
from typing import Dict, Any
import httpx
from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
from app.resources import context as r

class GeminiProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def generate_response(self, prompt_or_payload) -> LLmResponse:
        """
        Call Google Gemini API with JSON mode.
        """
        logger = r.logger
        model = self.config.model or "gemini-2.0-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        timeout = httpx.Timeout(self.config.timeout_seconds)
        params = {"key": self.config.api_key}
        headers = {"Content-Type": "application/json"}
        
        if isinstance(prompt_or_payload, dict):
            messages = prompt_or_payload["messages"]
            user_texts = [m["content"] for m in messages if m["role"] == "user"]
            text = "\n".join(user_texts) if user_texts else ""
            response_schema = {
                "type": "OBJECT",
                "properties": {
                    "overall_score": {"type": "NUMBER"},
                    "grammar_score": {"type": "NUMBER"},
                    "vocabulary_score": {"type": "NUMBER"},
                    "coherence_score": {"type": "NUMBER"},
                    "content_score": {"type": "NUMBER"},
                    "general_feedback": {"type": "STRING"},
                    "detailed_feedback": {"type": "STRING"},
                    "grammar_errors": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "error_type": {"type": "STRING"},
                                "original_text": {"type": "STRING"},
                                "corrected_text": {"type": "STRING"},
                                "explanation": {"type": "STRING"},
                                "line_number": {"type": "NUMBER"}
                            },
                            "required": ["error_type", "original_text", "corrected_text", "explanation"]
                        }
                    },
                    "grammar_improvements": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "vocabulary_suggestions": {
                        "type": "ARRAY",
                        "items": {
                            "type": "OBJECT",
                            "properties": {
                                "original_word": {"type": "STRING"},
                                "suggested_word": {"type": "STRING"},
                                "reason": {"type": "STRING"},
                                "line_number": {"type": "NUMBER"}
                            },
                            "required": ["original_word", "suggested_word", "reason"]
                        }
                    },
                    "vocabulary_improvements": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "improvement_suggestions": {"type": "ARRAY", "items": {"type": "STRING"}},
                    "suggested": {"type": "STRING"}
                },
                "required": [
                    "overall_score",
                    "grammar_score",
                    "vocabulary_score",
                    "coherence_score",
                    "content_score",
                    "general_feedback",
                    "detailed_feedback"
                ]
            }
            payload = {
                "contents": [{"role": "user", "parts": [{"text": text}]}],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens,
                    "responseMimeType": "application/json",
                    "responseSchema": response_schema
                }
            }
        else:
            payload = {
                "contents": [{"role": "user", "parts": [{"text": str(prompt_or_payload)}]}],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens,
                    "responseMimeType": "application/json"
                }
            }

        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(endpoint, headers=headers, params=params, json=payload)
                resp.raise_for_status()
                data = resp.json()
                
                candidates = data.get("candidates", [])
                if not candidates:
                    logger.warning("No candidates in Gemini response")
                    return LLmResponse(content="", provider_name=self.config.provider_name, model=model)
                
                candidate = candidates[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [])
                
                if not parts:
                    logger.warning("No parts in Gemini response content")
                    return LLmResponse(content="", provider_name=self.config.provider_name, model=model)
                
                text_content = ""
                for part in parts:
                    if "text" in part:
                        text_content += part["text"]

                return LLmResponse(
                    content=text_content,
                    provider_name=self.config.provider_name,
                    model=model)
            except Exception as e:
                logger.error(f"Gemini call failed with unexpected error: {type(e).__name__}: {e}")

            return LLmResponse(content="", provider_name=self.config.provider_name, model=model)

    def parse_writing_response(self, raw_content: str) -> Dict[str, Any]:
        logger = r.logger
        if not raw_content or not isinstance(raw_content, str):
            logger.error(f"Gemini response is empty or not a string: {raw_content}")
            return self._error_response()
        try:
            data = json.loads(raw_content)
            if not isinstance(data, dict):
                logger.error(f"Gemini response JSON is not a dict: {data}")
                return self._error_response()
            for key in [
                "grammar_errors",
                "grammar_improvements",
                "vocabulary_suggestions",
                "vocabulary_improvements",
                "improvement_suggestions"
            ]:
                if key not in data or data[key] is None:
                    data[key] = []
                elif not isinstance(data[key], list):
                    data[key] = [data[key]]
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response JSON: {e}\nRaw content: {raw_content[-100:]}")
            return {
                "overall_score": 0.0,
                "grammar_score": 0.0,
                "vocabulary_score": 0.0,
                "coherence_score": 0.0,
                "content_score": 0.0,
                "general_feedback": "Response was truncated and could not be parsed.",
                "detailed_feedback": f"Gemini response was truncated: {str(e)}",
                "grammar_errors": [],
                "grammar_improvements": [],
                "vocabulary_suggestions": [],
                "vocabulary_improvements": [],
                "improvement_suggestions": [],
                "suggested": None,
                "warning": "Gemini response was truncated. Try reducing prompt size or increasing max_tokens."
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing Gemini response: {type(e).__name__}: {e}")
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
            "general_feedback": "Unable to assess writing due to technical error.",
            "detailed_feedback": "Please try again later.",
            "grammar_errors": None,
            "grammar_improvements": None,
            "vocabulary_suggestions": None,
            "vocabulary_improvements": None,
            "improvement_suggestions": None,
            "suggested": None,
        }