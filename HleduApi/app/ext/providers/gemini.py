from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
import httpx
from app.resources import context as r
import json
from typing import Dict, Any, List


class GeminiProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)

    async def generate_response(self, prompt: str) -> LLmResponse:
        logger = r.logger
        model = self.config.model or "gemini-2.0-flash-exp"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
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
                            "maxOutputTokens": max(self.config.max_tokens, 4000), 
                            "responseMimeType": "application/json",
                            "responseSchema": {
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
                                                    "explanation": {"type": "STRING"}
                                                },
                                                "required": ["error_type", "original_text", "corrected_text", "explanation"]
                                            }
                                        },
                                        "grammar_improvements": {
                                            "type": "ARRAY",
                                            "items": {"type": "STRING"}
                                        },
                                        "vocabulary_suggestions": {
                                            "type": "ARRAY",
                                            "items": {
                                                "type": "OBJECT",
                                                "properties": {
                                                    "original_word": {"type": "STRING"},
                                                    "suggested_word": {"type": "STRING"},
                                                    "reason": {"type": "STRING"}
                                                },
                                                "required": ["original_word", "suggested_word", "reason"]
                                            }
                                        },
                                        "vocabulary_improvements": {
                                            "type": "ARRAY",
                                            "items": {"type": "STRING"}
                                        },
                                        "improvement_suggestions": {
                                            "type": "ARRAY",
                                            "items": {"type": "STRING"}
                                        },
                                        "suggested": {"type": "STRING"}
                                    },
                                    "required": ["overall_score", "grammar_score", "vocabulary_score", "coherence_score", "content_score", "general_feedback", "detailed_feedback"]
                                }
                        },
                    },
                )
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
        """Parse Gemini response for writing assessment"""
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
                "grammar_errors": self._get_optional_field(data, "grammar_errors"),
                "grammar_improvements": self._coerce_optional_str_list(self._get_optional_field(data, "grammar_improvements")),
                "vocabulary_suggestions": self._get_optional_field(data, "vocabulary_suggestions"),
                "vocabulary_improvements": self._coerce_optional_str_list(self._get_optional_field(data, "vocabulary_improvements")),
                "improvement_suggestions": self._coerce_optional_str_list(self._get_optional_field(data, "improvement_suggestions")),
                "suggested": self._get_optional_field(data, "suggested"),
            }
            
        except json.JSONDecodeError as e:
            r.logger.error(f"Failed to parse Gemini JSON response: {e}")
            return self._error_response()
        except Exception as e:
            r.logger.error(f"Error parsing Gemini writing response: {e}")
            return self._error_response()

    # -------------------- Provider-specific helpers --------------------
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
        if parsed < 0.0:
            return 0.0
        if parsed > 10.0:
            return 10.0
        return parsed

    def _coerce_optional_str_list(self, value: Any) -> List[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            t = value.strip()
            return [t] if t else None
        if isinstance(value, list):
            out: List[str] = []
            for item in value:
                if item is None:
                    continue
                out.append(item if isinstance(item, str) else str(item))
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
        