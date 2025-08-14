from pydantic import BaseModel, Field, field_validator
from typing import Literal
from app.service.types import TypeRequest


class WritingAssessmentTemplate(BaseModel):
    """Template to build prompt for writing assessment.
    Inputs are normalized to ensure DRY across paragraph/sentence modes.
    """

    student_level: str = Field(..., description="Student proficiency level")
    topic: str = Field(..., description="Writing topic")
    text: str = Field(..., description="User's writing text")
    type: Literal[TypeRequest.PARAGRAPH, TypeRequest.SENTENCE] = Field(
        ..., description="Input granularity"
    )

    @field_validator("type", mode="before")
    @classmethod
    def coerce_type(cls, v):
        if isinstance(v, TypeRequest):
            return v
        if isinstance(v, str):
            v = v.lower()
            if v == TypeRequest.PARAGRAPH.value:
                return TypeRequest.PARAGRAPH
            if v == TypeRequest.SENTENCE.value:
                return TypeRequest.SENTENCE
        return v

    def system_prompt(self) -> str:
        if self.type == TypeRequest.PARAGRAPH:
            return (
                "You are a helpful assistant for writing assessment. "
                "You are given a paragraph and must evaluate it objectively."
            )
        return (
            "You are a helpful assistant for writing assessment. "
            "You are given a sentence and must evaluate it objectively."
        )

    def user_prompt(self) -> str:
        return (
            "Please provide a comprehensive assessment of this writing piece.\n\n"
            f"Topic: {self.topic}\n"
            f"Student Level: {self.student_level}\n"
            f"Text: {self.text}\n\n"
            "Please analyze and provide:\n"
            "1. Overall score (0-10)\n"
            "2. Individual scores for Grammar, Vocabulary, Coherence, Content (0-10 each)\n"
            "3. General feedback (overall impression)\n"
            "4. Detailed feedback (comprehensive analysis)\n"
            "5. Grammar errors found with corrections\n"
            "6. Vocabulary suggestions for improvement\n"
            "7. Grammar improvement tips\n"
            "8. Vocabulary improvement tips\n"
            "9. General improvement suggestions\n"
            "10. An improved version of the writing\n\n"
            "Format your response as JSON with these fields:\n"
            "{\n"
            '  "overall_score": float,\n'
            '  "grammar_score": float,\n'
            '  "vocabulary_score": float,\n'
            '  "coherence_score": float,\n'
            '  "content_score": float,\n'
            '  "general_feedback": "string",\n'
            '  "detailed_feedback": "string",\n'
            '  "grammar_errors": [\n'
            '    {"error_type": "string", "original_text": "string", "corrected_text": "string", "explanation": "string"}\n'
            '  ],\n'
            '  "grammar_improvements": ["string"],\n'
            '  "vocabulary_suggestions": [\n'
            '    {"original_word": "string", "suggested_word": "string", "reason": "string"}\n'
            '  ],\n'
            '  "vocabulary_improvements": ["string"],\n'
            '  "improvement_suggestions": ["string"],\n'
            '  "suggested": "string"\n'
            "}"
        )


class SpeakingAssessmentTemplate(BaseModel):
    """Template to build prompt for speaking assessment."""

    student_level: str = Field(..., description="Student proficiency level")
    topic: str = Field(..., description="Speaking topic")
    text: str = Field(..., description="User's transcript or utterance text")
    type: Literal[TypeRequest.WORD, TypeRequest.SENTENCE, TypeRequest.PARAGRAPH, TypeRequest.ESSAY] = Field(
        ..., description="Input granularity"
    )

    @field_validator("type", mode="before")
    @classmethod
    def coerce_type(cls, v):
        if isinstance(v, TypeRequest):
            return v
        if isinstance(v, str):
            v = v.lower()
            mapping = {t.value: t for t in TypeRequest}
            return mapping.get(v, v)
        return v

    def system_prompt(self) -> str:
        return (
            "You are a helpful assistant for speaking assessment. "
            "Evaluate pronunciation, fluency, coherence, and vocabulary usage."
        )

    def user_prompt(self) -> str:
        return (
            "Please provide a comprehensive assessment of this speaking performance.\n\n"
            f"Topic: {self.topic}\n"
            f"Student Level: {self.student_level}\n"
            f"Transcript/Text: {self.text}\n\n"
            "Please analyze and provide:\n"
            "1. Overall speaking score (0-10)\n"
            "2. Scores for Pronunciation, Fluency, Coherence, Vocabulary (0-10 each)\n"
            "3. Specific pronunciation errors and corrections\n"
            "4. Fluency feedback and pace suggestions\n"
            "5. Recommended practice drills\n\n"
            "Format your response as JSON with these fields:\n"
            "{\n"
            '  "overall_score": float,\n'
            '  "pronunciation_score": float,\n'
            '  "fluency_score": float,\n'
            '  "coherence_score": float,\n'
            '  "vocabulary_score": float,\n'
            '  "pronunciation_errors": [\n'
            '    {"original": "string", "issue": "string", "suggestion": "string"}\n'
            '  ],\n'
            '  "fluency_feedback": "string",\n'
            '  "practice_drills": ["string"],\n'
            '  "general_feedback": "string"\n'
            "}"
        )
