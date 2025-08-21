from app.ext.providers.base import BaseProvider, ProviderConfig, LLmResponse
import httpx
from app.resources import context as r
import json
from typing import Dict, Any, List


class GrokProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.API_URL = "https://api.groq.com/openai/v1"

    async def generate_response(self, prompt: str) -> LLmResponse:
        """
        Call Groq-compatible REST API if api_url is configured.
        """
        logger = r.logger
        model = self.config.model or "mixtral-8x7b"
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
                        "response_format": {"type": "json_object"},
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
            logger.exception("Grok call failed")
            return LLmResponse(content="", provider_name=self.config.provider_name, model=model)

    def parse_writing_response(self, raw_content: str) -> Dict[str, Any]:
        """
        Parse Grok response for writing assessment.
        Maps Grok response format to WritingAssessmentResponse model.
        """
        logger = r.logger
        
        try:
            if isinstance(raw_content, str):
                data = json.loads(raw_content)
            else:
                data = raw_content
            
            mapped_response = {
                "overall_score": self._parse_score(data.get("overall_score")),
                "grammar_score": self._parse_score(data.get("grammar_score")),
                "vocabulary_score": self._parse_score(data.get("vocabulary_score")),
                "coherence_score": self._parse_score(data.get("coherence_score")),
                "content_score": self._parse_score(data.get("content_score")),
                "general_feedback": data.get("general_feedback", ""),
                "detailed_feedback": data.get("detailed_feedback", ""),
                "grammar_errors": self._parse_grammar_errors(self._get_optional_field(data, "grammar_errors") or []),
                "grammar_improvements": self._coerce_optional_str_list(self._get_optional_field(data, "grammar_improvements")),
                "vocabulary_suggestions": self._parse_vocabulary_suggestions(self._get_optional_field(data, "vocabulary_suggestions") or []),
                "vocabulary_improvements": self._coerce_optional_str_list(self._get_optional_field(data, "vocabulary_improvements")),
                "improvement_suggestions": self._coerce_optional_str_list(self._get_optional_field(data, "improvement_suggestions")),
                "suggested": self._get_optional_field(data, "suggested")
            }
            
            return mapped_response
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Grok JSON response: {e}")
            return self._error_response()
        except Exception as e:
            logger.error(f"Error parsing Grok writing response: {e}")
            return self._error_response()

    # Provider-specific helpers
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

    def _parse_grammar_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse grammar errors from Grok format"""
        parsed_errors = []
        for error in errors:
            if isinstance(error, dict):
                parsed_errors.append({
                    "error_type": error.get("error_type", "Unknown"),
                    "original_text": error.get("original_text", ""),
                    "corrected_text": error.get("corrected_text", ""),
                    "explanation": error.get("explanation", ""),
                    "line_number": error.get("line_number")
                })
        return parsed_errors
    
    def _parse_vocabulary_suggestions(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse vocabulary suggestions from Grok format"""
        parsed_suggestions = []
        for suggestion in suggestions:
            if isinstance(suggestion, dict):
                parsed_suggestions.append({
                    "original_word": suggestion.get("original_word", ""),
                    "suggested_word": suggestion.get("suggested_word", ""),
                    "reason": suggestion.get("reason", ""),
                    "line_number": suggestion.get("line_number")
                })
        return parsed_suggestions

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
