from typing import Literal
from pydantic import BaseModel, Field
from app.service.types import TypeRequest, ModeRequest
from .base import WritingAssessmentTemplate, SpeakingAssessmentTemplate


class PromptTemplate(BaseModel):
    """Scalable prompt builder across modes (writing/speaking) and granularities."""

    student_level: str = Field(...)
    topic: str = Field(...)
    text: str = Field(...)
    type: Literal[
        TypeRequest.WORD,
        TypeRequest.SENTENCE,
        TypeRequest.PARAGRAPH,
        TypeRequest.ESSAY,
    ] = Field(..., description="Granularity")
    mode: Literal[ModeRequest.WRITING, ModeRequest.SPEAKING] = Field(..., description="Task mode")

    def _system_for_writing(self) -> str:
        return (
            f"You are an expert writing assessor for {self.student_level} level students. "
            f"Evaluate the given {self.type.value.lower()} on topic '{self.topic}' objectively using a 0-10 scale. "
            f"Adjust scoring according to {self.student_level} level. "
            "RESPOND WITH ONLY VALID JSON - NO OTHER TEXT. "
            "JSON must have these EXACT fields: "
            "overall_score, grammar_score, vocabulary_score, coherence_score, content_score, "
            "general_feedback, detailed_feedback, "
            "grammar_errors (array of objects with error_type, original_text, corrected_text, explanation, line_number OR empty array), "
            "grammar_improvements (array OR empty array), "
            "vocabulary_suggestions (array of objects with original_word, suggested_word, reason, line_number OR empty array), "
            "vocabulary_improvements (array OR empty array), "
            "improvement_suggestions (array OR empty array), "
            "suggested (string). "
            "All scores must be numbers between 0-10."
        )

    def _system_for_speaking(self) -> str:
        return (
            "You are a helpful assistant for speaking assessment. "
            "Evaluate pronunciation, fluency, coherence, and vocabulary usage. "
            "You must respond with valid JSON only. Do not include any text outside the JSON structure."
        )

    def _user_common(self) -> str:
        return (
            f"Topic: {self.topic}\n"
            f"Student Level: {self.student_level}\n"
            f"Text: {self.text}\n"
        )

    def _user_for_writing(self) -> str:
        return (
            self._user_common()
            + "Provide JSON response with exactly these fields: "
            "overall_score, grammar_score, vocabulary_score, coherence_score, content_score, "
            "general_feedback, detailed_feedback, "
            "grammar_errors (objects with error_type, original_text, corrected_text, explanation, line_number), "
            "grammar_improvements, "
            "vocabulary_suggestions (objects with original_word, suggested_word, reason, line_number), "
            "vocabulary_improvements, improvement_suggestions, suggested."
        )

    def _user_for_speaking(self) -> str:
        return (
            self._user_common()
            + "Provide JSON with: "
            "overall_score, pronunciation_score, fluency_score, coherence_score, vocabulary_score, "
            "pronunciation_errors, fluency_feedback, practice_drills."
        )

    def build(self) -> str:
        if self.mode is ModeRequest.WRITING:
            t = WritingAssessmentTemplate(
                student_level=self.student_level,
                topic=self.topic,
                text=self.text,
                type=self.type,
            )
        else:
            t = SpeakingAssessmentTemplate(
                student_level=self.student_level,
                topic=self.topic,
                text=self.text,
                type=self.type,
            )
        return f"<SYSTEM>\n{t.system_prompt()}\n</SYSTEM>\n<USER>\n{t.user_prompt()}\n</USER>"
