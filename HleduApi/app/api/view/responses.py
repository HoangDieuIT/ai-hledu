from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal

import app.model.composite as c
from pydantic import ConfigDict, Field, BaseModel
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass
from typing_extensions import Self
from app.resources import context as r

# ================================================================
# Settings
# ================================================================

config = ConfigDict(
    alias_generator=to_camel,
    populate_by_name=True,
)


@dataclass(config=config)
class AIModelResponse:
    """
    AI Model response model.
    """
    id: str = Field(description="AI Model ID")
    name: str = Field(description="AI Model name")
    provider_id: str = Field(description="Provider ID")
    is_active: bool = Field(description="Whether the model is active")


@dataclass(config=config) 
class ProviderResponse:
    """
    Provider response model.
    """
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

class VocabularySuggestion(BaseModel):
    """Vocabulary improvement suggestion"""
    original_word: str = Field(description="Original word used")
    suggested_word: str = Field(description="Suggested better word")
    reason: str = Field(description="Reason for the suggestion")

class WritingAssessmentResponse(BaseModel):
    """Complete writing assessment response"""
    # Scores
    overall_score: float = Field(..., ge=0, le=10, description="Overall writing score")
    grammar_score: float = Field(..., ge=0, le=10, description="Grammar score")
    vocabulary_score: float = Field(..., ge=0, le=10, description="Vocabulary score")
    coherence_score: float = Field(..., ge=0, le=10, description="Coherence score")
    content_score: float = Field(..., ge=0, le=10, description="Content score")
    
    # Feedback
    general_feedback: str = Field(description="Overall impression and feedback")
    detailed_feedback: str = Field(description="Comprehensive analysis")
    
    # Specific improvements
    grammar_errors: List[GrammarError] = Field(default_factory=list)
    grammar_improvements: List[str] = Field(default_factory=list)
    vocabulary_suggestions: List[VocabularySuggestion] = Field(default_factory=list)
    vocabulary_improvements: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    
    # Enhanced version
    suggested_writing: str = Field(description="Improved version of the writing")
    
    # Metadata
    provider_used: str = Field(description="AI provider used for assessment")
    model_used: str = Field(description="AI model used")
    assessment_timestamp: datetime = Field(default_factory=datetime.now)
    
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
                    {"error_type": "Subject-Verb Agreement",
                        "original_text": "Climate change are",
                        "corrected_text": "Climate change is",
                        "explanation": "Singular subject requires singular verb"
                    }
                ],
                "suggested_writing": "Climate change is a serious problem that affects everyone on Earth..."
            }
        }