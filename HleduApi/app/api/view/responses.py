from datetime import datetime
from typing import List, Optional, Any
from pydantic import ConfigDict, Field, BaseModel
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass
from app.ext.custom_datetime.time_handler import CustomDateTime

# ================================================================
# Settings
# ================================================================

config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


@dataclass(config=config)
class AIModelResponse:
    """AI Model response model."""
    id: str = Field(description="AI Model ID")
    name: str = Field(description="AI Model name")
    provider_id: str = Field(description="Provider ID")
    is_active: bool = Field(description="Whether the model is active")


@dataclass(config=config)
class ProviderResponse:
    """Provider response model."""
    id: str = Field(description="Provider ID")
    name: str = Field(description="Provider name")
    is_active: bool = Field(description="Whether the provider is active")
    ai_models: Optional[List[AIModelResponse]] = Field(default=None, description="AI models associated with this provider")


class GrammarError(BaseModel):
    """Individual grammar error details"""
    error_type: str = Field(description="Type of grammar error")
    original_text: str = Field(description="Original incorrect text")
    corrected_text: str = Field(description="Corrected version")
    explanation: str = Field(description="Explanation of the error")
    line_number: Optional[Any] = Field(default=None, description="Line number where the error occurred")


class VocabularySuggestion(BaseModel):
    """Vocabulary improvement suggestion"""
    original_word: str = Field(description="Original word used")
    suggested_word: str = Field(description="Suggested better word")
    reason: str = Field(description="Reason for the suggestion")
    line_number: Optional[Any] = Field(default=None, description="Line number where the word appears")


class WritingAssessmentResponse(BaseModel):
    @staticmethod
    def serialize_field(data_list, object_class):
        if not isinstance(data_list, list):
            return []
        parsed_objects = []
        for item in data_list:
            if isinstance(item, dict):
                try:
                    parsed_objects.append(object_class(**item))
                except Exception as e:
                   pass
        return parsed_objects
    """Complete writing assessment response"""
    overall_score: float = Field(..., ge=0, le=10, description="Overall writing score")
    grammar_score: float = Field(..., ge=0, le=10, description="Grammar score")
    vocabulary_score: float = Field(..., ge=0, le=10, description="Vocabulary score")
    coherence_score: float = Field(..., ge=0, le=10, description="Coherence score")
    content_score: float = Field(..., ge=0, le=10, description="Content score")

    general_feedback: str = Field(description="Overall impression and feedback")
    detailed_feedback: str = Field(description="Comprehensive analysis")

    grammar_errors: Optional[List[GrammarError]] = Field(default=None, description="Grammar errors found (null if no errors)")
    grammar_improvements: Optional[List[str]] = Field(default=None, description="Grammar improvement suggestions (null if not needed)")
    vocabulary_suggestions: Optional[List[VocabularySuggestion]] = Field(default=None, description="Vocabulary suggestions (null if vocabulary is good)")
    vocabulary_improvements: Optional[List[str]] = Field(default=None, description="Vocabulary improvement tips (null if not needed)")
    improvement_suggestions: Optional[List[str]] = Field(default=None, description="General improvement suggestions (null if writing is excellent)")

    suggested: Optional[str] = Field(default=None, description="Improved version of the writing (null if original is good)")

    # Metadata
    provider: str = Field(description="AI provider used for assessment")
    model: str = Field(description="AI model used")
    assessment_timestamp: datetime = Field(description="Assessment timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_score": 7.5,
                "grammar_score": 8.0,
                "vocabulary_score": 7.0,
                "coherence_score": 8.5,
                "content_score": 7.0,
                "general_feedback": "Good effort with room for improvement",
                "detailed_feedback": "The writing shows good understanding of the topic...",
                "grammar_errors": [
                    {
                        "error_type": "Subject-Verb Agreement",
                        "original_text": "Climate change are",
                        "corrected_text": "Climate change is",
                        "explanation": "Singular subject requires singular verb",
                        "line_number": 1
                    }
                ],
                "vocabulary_suggestions": [
                    {
                        "original_word": "big",
                        "suggested_word": "significant",
                        "reason": "More academic and precise",
                        "line_number": 2
                    }
                ],
                "suggested": "Climate change is a significant problem that affects everyone on Earth...",
                "provider": "gemini",
                "model": "gemini-2.0-flash",
                "assessment_timestamp": "2025-08-13T10:00:00Z"
            }
        }

    @classmethod
    def of(
        cls,
        data: dict,
        *,
        provider: str,
        model: str,
        assessment_timestamp: Optional[datetime] = None,
    ) -> "WritingAssessmentResponse":
        """Factory method to build response from parsed provider data."""

        return cls(
            overall_score=data.get("overall_score", 0.0),
            grammar_score=data.get("grammar_score", 0.0),
            vocabulary_score=data.get("vocabulary_score", 0.0),
            coherence_score=data.get("coherence_score", 0.0),
            content_score=data.get("content_score", 0.0),
            general_feedback=data.get("general_feedback", ""),
            detailed_feedback=data.get("detailed_feedback", ""),
            grammar_errors=cls.serialize_field(data.get("grammar_errors"), GrammarError),
            grammar_improvements=data.get("grammar_improvements"),
            vocabulary_suggestions=cls.serialize_field(data.get("vocabulary_suggestions"), VocabularySuggestion),
            vocabulary_improvements=data.get("vocabulary_improvements"),
            improvement_suggestions=data.get("improvement_suggestions"),
            suggested=data.get("suggested"),
            provider=provider,
            model=model,
            assessment_timestamp=assessment_timestamp or CustomDateTime.now(),
        )