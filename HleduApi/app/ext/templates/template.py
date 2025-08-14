from typing import Literal
from pydantic import BaseModel, Field
from app.service.types import TypeRequest, ModeRequest
from .base import WritingAssessmentTemplate, SpeakingAssessmentTemplate


class PromptTemplate(BaseModel):
    """
    Scalable prompt builder across modes (writing/speaking) and granularities.
    """

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
        match self.type:
            case TypeRequest.WORD:
                focus = "a word"
            case TypeRequest.SENTENCE:
                focus = "a sentence"
            case TypeRequest.PARAGRAPH:
                focus = "a paragraph"
            case TypeRequest.ESSAY:
                focus = "an essay"
            case _:
                focus = "text"
        return (
            f"You are an expert writing assessor for {self.student_level} level students. "
            f"Evaluate the given {focus} on topic '{self.topic}' objectively using a 0-10 scale. "
            f"Adjust your expectations and scoring criteria according to {self.student_level} proficiency level. "
            f"For {self.student_level} students, focus on appropriate grammar complexity, vocabulary range, and content depth. "
            "RESPOND WITH ONLY VALID JSON - NO OTHER TEXT. "
            "JSON must have these EXACT fields with EXACT names: "
            "overall_score (number 0-10), grammar_score (number 0-10), vocabulary_score (number 0-10), "
            "coherence_score (number 0-10), content_score (number 0-10), "
            "general_feedback (string), detailed_feedback (string), "
            "grammar_errors (array of objects with error_type, original_text, corrected_text, explanation OR empty array), "
            "grammar_improvements (array of strings OR empty array), "
            "vocabulary_suggestions (array of objects with original_word, suggested_word, reason OR empty array), "
            "vocabulary_improvements (array of strings OR empty array), "
            "improvement_suggestions (array of strings OR empty array), "
            "suggested (string). "
            "Use null for optional fields if not applicable. All scores must be numbers between 0-10."
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
        """
        Build the prompt for analyzing a writing task.
        Returns:
            str: A formatted string containing analysis instructions and JSON output format.
        """
        base_prompt = self._user_common()

        analysis_instructions = (
            f"Assess this writing considering it's from a {self.student_level} level student writing about '{self.topic}'. "
            f"Apply {self.student_level}-appropriate expectations for grammar complexity, vocabulary sophistication, and content depth. "
            "Provide assessment in JSON format with EXACTLY these fields: "
            "overall_score (number 0-10), grammar_score (number 0-10), vocabulary_score (number 0-10), "
            "coherence_score (number 0-10), content_score (number 0-10), "
            "general_feedback (string), detailed_feedback (string), "
            "grammar_errors (array OR empty array), grammar_improvements (array OR empty array), "
            "vocabulary_suggestions (array OR empty array), vocabulary_improvements (array OR empty array), "
            "improvement_suggestions (array OR empty array), suggested (string). "
            "Use empty arrays for optional fields if not applicable. RESPOND WITH JSON ONLY."
        )

        return f"{base_prompt}{analysis_instructions}"

    def _user_for_speaking(self) -> str:
        return (
            self._user_common()
            + "\nPlease analyze and provide a JSON response with these exact fields: "
            + "overall_score, pronunciation_score, fluency_score, coherence_score, vocabulary_score, "
            + "pronunciation_errors, fluency_feedback, practice_drills. "
            + "Respond with JSON only, no additional text."
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

